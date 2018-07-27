
'''
Combine individually-imaged channels into a cube.
'''

import sys
from glob import glob
from warnings import warn

filename = sys.argv[-2]

# Check for the expected number of images
num_imgs = int(sys.argv[-1])

suffixes = ['mask', 'model', 'pb', 'psf', 'residual', 'image',
            'image.pbcor', 'sumwt', 'weight']

for suff in suffixes:

    images = glob("{0}_channel*.{1}".format(filename, suff))

    if len(images) == 0:
        warn("No images found for {}".format(suff))
        continue

    if len(images) != num_imgs:
        warn("Number of images found ({0}) does not match"
             " expected number ({1}) for {2}. Skipping cube creation."
             .format(len(images), num_imgs, suff))
        continue

    cubename = "{0}.{1}".format(filename, suff)

    ia.imageconcat(outfile=cubename, infiles=images, reorder=True,
                   overwrite=True)
    ia.close()
