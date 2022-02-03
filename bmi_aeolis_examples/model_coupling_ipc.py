import copy
import numpy
import enum

@enum.unique
class VarId(enum.Enum):
    var_id_bathymetry = 1,
    var_id_max_mean_water_level = 2

class model_coupling_ipc(object):

    def __init__(self):
        self.var_info = {}
        # {<var name>:
        #   {"var_id": <int var id>,
        #   "type": <numpy data type>,
        #   "shape": <var shape>,
        #   "row_length": [<row1 len>, <row2 len>, ..., <rowN len>]}}

    def InitializeVarInfo(self,
        name, var_id, data_type, shape = None, row_length = None):
        self.var_info[name] = {
            "var_id": var_id,
            "type": data_type}
        if shape and row_length:
            self.var_info[name]["shape"] = shape
            self.var_info[name]["row_length"] = row_length

    ##
    # @param stream a pipe/socket for writing.
    # @param var_name name of the var to send.
    # @param buffer the var to send.
    # @return status status code.
    def SendVar(self, stream, var_name, buffer):
        try:
            a = numpy.array(
                [self.var_info[var_name]["var_id"]], dtype = numpy.int32)
            #a.tofile(stream)
            stream.write(a.data)

            if not "row_length" in self.var_info[var_name]:
                # scalar
                a = numpy.array([buffer],
                    dtype = self.var_info[var_name]["type"])
                #a.tofile(stream)
                stream.write(a.data)
            elif len(self.var_info[var_name]["shape"]) == 1:
                # 1-d array
                #buffer.tofile(stream)
                stream.write(buffer.data)
            elif len(self.var_info[var_name]["shape"]) == 2:
                # 2-d array
                for i in range(0,
                    len(self.var_info[var_name]["row_length"]), 1):
                    # buffer[i][:self.var_info[var_name]["row_length"][i]].\
                    #     tofile(stream)
                    stream.write(buffer.data)
            else:
                # higher-dimension array
                return 2

            # flush buffered write operations
            stream.flush()
        except Exception as e:
            print(str(e))
            return 1

        return 0

    ##
    # @param stream a pipe/socket for reading.
    # @param var_name name of var to receive.
    # @return status status code.
    # @return buffer the variable received in a scalar or a numpy.ndarray.
    def RecvVar(self, stream, var_name):
        buffer = None

        try:
            a = numpy.frombuffer(
                stream.read(numpy.dtype(numpy.int32).itemsize),
                count = 1, dtype = numpy.int32)

            if not a[0] == self.var_info[var_name]["var_id"]:
                return 2, None

            if not "row_length" in self.var_info[var_name]:
                # scalar
                a = numpy.fromstring(
                    stream.read(1 * numpy.dtype(
                        self.var_info[var_name]["type"]).itemsize),
                    count = 1, dtype = self.var_info[var_name]["type"])
                buffer = a[0]
            elif len(self.var_info[var_name]["shape"]) == 1:
                # 1-d array
                buffer = numpy.fromstring(
                    stream.read(numpy.dtype(
                        self.var_info[var_name]["type"]).itemsize *
                        self.var_info[var_name]["row_length"][0]),
                    count = self.var_info[var_name]["row_length"][0],
                    dtype = self.var_info[var_name]["type"])
            elif len(self.var_info[var_name]["shape"]) == 2:
                # 2-d array
                # TEMP SOLUTION. must fill arbitrary shape[0]*shape[1] elements
                buffer = numpy.fromstring(
                    stream.read(numpy.dtype(
                        self.var_info[var_name]["type"]).itemsize *
                        self.var_info[var_name]["row_length"][0]),
                    count = self.var_info[var_name]["row_length"][0],
                    dtype = self.var_info[var_name]["type"])
                buffer.shape = (1, self.var_info[var_name]["shape"][1])
                # buffer = numpy.ndarray(
                #     (1, self.var_info[var_name]["shape"][1]),
                #     buffer = memoryview(stream.read(numpy.dtype(
                #         self.var_info[var_name]["type"]).itemsize *
                #         self.var_info[var_name]["row_length"][0])),
                #     dtype = self.var_info[var_name]["type"])

                # var = []
                # for i in range(0, len(var_info["row_length"]), 1):
                #     var.append(numpy.fromfile(
                #         stream, dtype = var_info["type"],
                #         count = var_info["row_length"][i]))
                # var = numpy.array(var)
            else:
                # higher-dimension array
                return 3, None
        except Exception as e:
            print(str(e))
            return 1, None

        return 0, buffer
