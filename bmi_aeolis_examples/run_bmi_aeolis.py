import aeolis.model
import numpy
import sys
import argparse

if __name__ == "__main__":

    debug = False

    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file",
        required = True, dest = "config_file")
    args = parser.parse_args()

    # initialize aeolis
    bmi_aeolis_model=aeolis.model.AeoLiS(configfile=str(args.config_file))
    bmi_aeolis_model.initialize()

    # start time marching
    icount = 1
    while bmi_aeolis_model.t <= bmi_aeolis_model.p['tstop']:

        print('aeolis time: ' + str(bmi_aeolis_model.t) + '  count: ' + str(icount))

        icount = icount + 1

        # continue with aeolis update()
        bmi_aeolis_model.update(3600.)

    bmi_aeolis_model.finalize()
