
## Tools for imaging single channels from a spectral-line data set in casa.

These scripts can be used as templates. Examples are provided for use with a single
machine (`sequential_clean_submission_example.sh`) or in a cluster environment (`imaging_array_submission.sh`).



Steps:

1. Set tclean imaging parameters, as desired. Either by running a test channel in CASA (e.g., for determining the clean threshold) and saving the `tclean.last` script, or by adapting the example in this folder.
2. (Optional) If using a pre-made clean mask or model, the cubes must be split into the channel numbers that will be imaged. The split channels must end with "{name}_channel_{num}.image" for a starting model, and "{name}_channel_{num}.mask" for a mask. The tclean parameters should specify the name prefix.
3. Create the imaging script with the tclean call. The template given here (`single_channel_clean.py`) is already fairly generalized. The script should accept the same command line arguments as the template. If `iter>0` and `interactive=0`, a dictionary of diagnostics are returned. In the template, these diagnostics are saved, which is easier than looking through every CASA log file. **Note that this also forces the creation of a summary plot made with matplotlib. If no frame buffer is set, use xvfb to create a virtual display.**
4. Create the submission script. If running on a cluster, the submission script may change significantly. The template given here (`imaging_array_submission.sh`) is an example of an job array submission with [slurm](https://slurm.schedmd.com/overview.html). If running on a single machine, the `sequential_clean_submission.py` script creates a pool of workers that each run a separate CASA job. **In both cases, it is useful to run a test channel (as in Step 1) and figure out how much memory CASA requires. It may be that the number of simultaneous jobs is limited by the system's RAM rather than the number of processors.**
5. Examine the output HDF5 with a summary of the CLEAN results for each channel. This is automatically created in `sequential_clean_submission.py`. When running on a cluster, this needs to be run separately with `gather_tclean_outputs.py`. Check for any issues (divergence, reached `iter`, etc) by examining the `stopcode` and `stopcode_exp` columns in the table. To open the table with astropy.table, use: `from astropy.table import Table; tab = Table.read('filename.h5', path='data')`.
6. Concatenate the channel outputs into cubes (`image_concat.py`). The filename given in `tclean.saved` is needed, as well as the expected number of output channels.