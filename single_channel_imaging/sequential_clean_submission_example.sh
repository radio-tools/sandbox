
# Demonstrating the use of sequential_clean_submission.py
# Inputs: number of procs, name of clean script, saved tclean input file, (optional) path to casa

# Single image cleaning
python sequential_clean_submission.py 3 single_channel_clean.py tclean.saved /home/user/casa-release-5.1.2/bin/casa

# An HDF5 file should not be in the imagename path. Check for bad output codes
# (column 'stopcode_exp') from the imaging.

# Concatenate into cubes
# Give filename prefix and the number of channels that *should* be saved
/home/user/casa-release-5.1.2/bin/casa -c image_concat.py test_image 3
