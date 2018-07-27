
'''
Run image and clean individual channels in a non-cluster environment.
Parallelization is done over the available processors via a pool
of workers.

Because CASA makes temporary files in the current directory, it may be
useful to run this script from the same directory as the MS.

'''

import os
from glob import glob
import numpy as np
from astropy.table import Table, Column
from warnings import warn


def run_casa(spec, inputs, script_name, log_file, casa_call="casa"):
    '''
    Run script in casa in non-MPI mode
    '''

    # add in the log file here
    out_code = os.system("{0} --nogui --logfile {1} -c {2} {3} {4}"
                         .format(casa_call, log_file, script_name, spec,
                                 inputs))

    # Return the code for success and inputs for matching the pool output
    # to the channel.
    return spec, out_code


def _run_casa(inp):
    return run_casa(*inp)


def load_paramfile(filename):
    '''
    Load in a CASA parameter file and return a dictionary.
    '''

    d = {}

    with open(filename) as fil:
        for line in fil:
            if line[0] == "#" or line == "\n":
                continue
            key, val = line.split(" = ")

            # Strip off empty space, and additional ""
            d[key.strip()] = val.strip().strip('"')

    return d


def create_tclean_output_table(filename):
    '''
    Return an astropy table of the output summaries from each channel.

    Meaning of stop codes
    (https://open-bitbucket.nrao.edu/projects/CASA/repos/casa/browse/code/synthesis/ImagerObjects/SIIterBot.cc)

    0 - No stopping stepped reach. I don't think tclean will exit with this.
    1 - Reached niter
    2 - Reached cycle/overall threshold (?)
    3 - Stop flag given (from interactive clean?)
    4 - No changes from previous minor/major cycle
    5 - Diverging. Relative peak residual increased by >3 from previous cycle
    6 - Diverging. Relative min peak residual increased by >3 from previous
    7 - Empty mask
    8 - Reached nsigma threshold (disabled if nsigma=0.0)

    '''

    files = glob(filename + "_channel_*.results_dict.npy")

    if len(files) == 0:
        warn("Found no npy output files")
        return

    # Sort by number
    files.sort()

    for i, fil in enumerate(files):

        out_dict = np.load(fil).item()

        # Setup a dictionary
        if i == 0:
            all_dict = dict.fromkeys(out_dict)

            for key in all_dict:
                all_dict[key] = []

        for key in out_dict:
            all_dict[key].append(out_dict[key])

    # Now convert the dictionary into an astropy table

    table = Table()

    for key in all_dict:

        table[key] = Column(all_dict[key])

    stop_codes = {0: "Not reached", 1: "Reached niter",
                  2: "Reached threshold",
                  3: "Stop flag", 4: "No change after cycle",
                  5: "Diverging. Peak residual increase.",
                  6: "Diverging. Peak min. residual increase.",
                  7: "Empty clean mask",
                  8: "Reached nsigma threshold"}

    # Empty string array set to longest message in stop_codes
    str_outs = np.empty(table['nsigma'].shape, dtype='S39')

    str_outs = []

    for code in table['stopcode']:

        if code < 0 or code > 8:
            raise ValueError("Found code {0} not within 0 and 8. Check"
                             " output.".format(code))

        str_outs.append(stop_codes[code])

    table['stopcode_exp'] = Column(str_outs)

    return table


if __name__ == "__main__":

    import sys
    from multiprocessing import Pool
    from datetime import datetime
    from contextlib import closing

    # Number of cores to use. Note that CASA will base max. memory usage
    # off of the system's memory. Image one channel manually to find the memory
    # requirements.
    nprocs = int(sys.argv[1])

    # Script with the imaging call
    script_name = sys.argv[2]

    # File with settings for the imaging
    input_file = sys.argv[3]

    # Pass a custom path for the location of CASA. Otherwise assume
    # "casa" is set. Also set CASA flags here.
    casa_path = "casa" if len(sys.argv) == 4 else sys.argv[4]

    # Read in parameters here
    casa_inputs = load_paramfile(input_file)

    # A few of the parameters are needed to set the jobs up
    nchan = int(casa_inputs['nchan'])

    specs = np.arange(nchan + 1)

    log_file = "{0}_{1}".format(casa_inputs['imagename'],
                                datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

    # XXX For testing
    specs = specs[:3]

    # Need "closing" when running this in python <3.3
    with closing(Pool(nprocs)) as pool:

        job_gen = ((spec, input_file, script_name,
                    "{0}_{1}.log".format(log_file, spec), casa_path)
                   for spec in specs)

        outputs = pool.map(_run_casa, job_gen)

        # Require termination when using closing
        pool.terminate()

    # Check the output codes
    out_dict = {}
    for out in outputs:
        out_dict[out[0]] = out[1:]

    out_codes = np.array([int(out[1]) for out in outputs])

    bad_outs = np.array(out_dict.keys())[np.where(out_codes > 0)]

    print("Non-zero exit codes from the following channels: {0}"
          .format(bad_outs))

    # Read in the saved clean results files here and pull out statistics.
    out_tab = create_tclean_output_table(casa_inputs['imagename'])

    # Save as an HDF5 file. Most ascii formats do not allow for columns with
    # arrays with shapes larger than 1 column.
    out_tab.write("{0}_clean_results.h5".format(casa_inputs['imagename']),
                  path='data', format='hdf5')
