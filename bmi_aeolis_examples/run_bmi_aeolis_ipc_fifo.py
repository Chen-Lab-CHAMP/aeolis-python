import aeolis.model
import numpy
import struct
import sys
import argparse
import model_coupling_ipc

if __name__ == "__main__":

    debug = False

    parser = argparse.ArgumentParser()
    parser.add_argument("--var-in-pipe",
        required = True, dest = "pipe_from_cshore")
    parser.add_argument("--var-out-pipe",
        required = True, dest = "pipe_to_cshore")
    parser.add_argument("--config-file",
        required = True, dest = "config_file")
    args = parser.parse_args()

    p_to_cs = None
    p_from_cs = None

    # initialize aeolis
    bmi_aeolis_model=aeolis.model.AeoLiS(configfile=str(args.config_file))
    bmi_aeolis_model.initialize()

    # find out zb and max_mwl shape and type
    zb_ptr = bmi_aeolis_model.get_var('zb') # note: aeolise get_var is actually getting the pointer
    zs_buffer = numpy.array([0], dtype=numpy.float64).item() # [0] has no meaning, just want to initialize an array with 1 entry

    print('length(zb) = '+str(len(zb_ptr)))
    print('zb:'+str(zb_ptr[0][0:5]))
    print('shape(zb) = '+str(zb_ptr.shape))


    ipc = model_coupling_ipc.model_coupling_ipc()
    ipc.InitializeVarInfo("bathymetry",
        model_coupling_ipc.VarId.var_id_bathymetry.value,
        zb_ptr.dtype, zb_ptr.shape, [zb_ptr.shape[1]])

    ipc.InitializeVarInfo("max_mean_water_level",
        model_coupling_ipc.VarId.var_id_max_mean_water_level.value,
        type(zs_buffer))

    ngrid = len(zb_ptr[0])

    print('original tstop = ', str(bmi_aeolis_model.p['tstop']))
    # bmi_aeolis_model.set_var('tstop', 7200)
    # print('new tstop = ', str(bmi_aeolis_model.p['tstop']))
    # print(bmi_aeolis_model.t)

    # bmi_aeolis_model.p['tstop'] = 3600.0
    print('new tstop = ', str(bmi_aeolis_model.p['tstop']))


    # start time marching
    icount = 1
    while bmi_aeolis_model.t <= bmi_aeolis_model.p['tstop']:

        print('aeolis time: ' + str(bmi_aeolis_model.t) + '  count: ' + str(icount))

        icount = icount + 1

        # receive zb and max_mwl from cshore and set them (through pointer)
        if not p_from_cs:
            p_from_cs = open(str(args.pipe_from_cshore), "rb")

        # protocol: zb first, zs second
        status, zb_buffer = ipc.RecvVar(p_from_cs, "bathymetry")
        if status == 0:
            if debug:
                print('correct. receive zb status = ' + str(status))
                print('zb:'+str(zb_buffer))
        else:
            print('wrong. receive zb status = ' + str(status))

        with open('zbfromCSHORE'+str(icount)+'.txt','w') as f:                #the file containing numbers
             for elements in zb_buffer[0]:
                 f.write(str(elements))
                 f.write('\n')

        bmi_aeolis_model.set_var('zb', zb_buffer)
       # OR we can directly change bmi_aeolis_model.s['zb'] to zb_buffer
       # bmi_aeolis_model.s['zb'] = zb_buffer

        status, zs_buffer = ipc.RecvVar(p_from_cs, "max_mean_water_level")

        if status == 0:
            if debug:
                print('correct. receive max_mwl status = ' + str(status))
                print('max_mwl:'+str(zs_buffer))
        else:
            print('wrong. receive max_mwl status = ' + str(status))

        bmi_aeolis_model.p['tide_file'] = numpy.array([[0.0, zs_buffer],
                                [bmi_aeolis_model.p['tstop'], zs_buffer]])

        # bmi_aeolis_model.p['tide_file'] = numpy.array([[0.0, 1.0],
        #                         [bmi_aeolis_model.p['tstop'], 1.0]])

        if debug:
            print(bmi_aeolis_model.p['tide_file'])

        # bmi_aeolis_model.s['zb'].setflags(write=True)

        # continue with aeolis update()
        bmi_aeolis_model.update(3600.)

        # get and send zb from aeolis to cshore
        if not p_to_cs:
            p_to_cs = open(str(args.pipe_to_cshore), "wb")

        zb_ptr = bmi_aeolis_model.get_var('zb')

        with open('zbtoCSHORE'+str(icount)+'.txt','w') as f:                #the file containing numbers
             for elements in zb_ptr[0]:
                 f.write(str(elements))
                 f.write('\n')

        status = ipc.SendVar(p_to_cs, "bathymetry", zb_ptr)
        if status==0:
            if debug:
                print('correct. send zb to cshore.')
        else:
            print('wrong. send zb to cshore. status = ' +str(status))

# save final bathy profile in a txt file.
    with open('zbnew.txt','w') as f:                #the file containing numbers
         for elements in zb_ptr[0]:
             f.write(str(elements))
             f.write('\n')

    bmi_aeolis_model.finalize()

    p_from_cs.close()
    p_to_cs.close()
