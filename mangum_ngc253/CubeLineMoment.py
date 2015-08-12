"""

Derive Moment0, Moment1, and Moment2 from a reasonably-well separated spectral line in
an image cube.  Simply calculates moments over a defined HWZI for each line in band.

To run in ipython use:

run ~/Python/CubeLineMoment.py

To Do:
(1) Grab target name from FITS header
(2) Grab vz from FITS header
(3) Change output values for second moment to km/s rather than (km/s)^2

"""
from __future__ import print_function

import numpy as np
import pyspeckit
from spectral_cube import SpectralCube
from astropy import wcs
from astropy import units as u
import pyregion
import pylab as pl
import aplpy

# Read the FITS cube
# And change the units back to Hz
# and cut out a region that only includes the Galaxy (so we don't have to worry
# about masking later)
cube = SpectralCube.read('NGC253-H2COJ54K024-Feather-line.fits').with_spectral_unit(u.Hz).subcube_from_ds9region(pyregion.open('ngc253box.reg'))

# redshift velocity
vz = 258.8*u.km/u.s

# Lines to be analyzed (including brightest_line)
target = 'NGC253'
my_line_list = [362.630304, 364.103249, 363.945894, 363.785397, 362.736048] * u.GHz
my_line_widths = [150.0, 80.0, 80.0, 80.0, 80.0] * u.km/u.s
my_line_names = ['HNC43','H2COJ54K4','H2COJ54K2','HC3N4039','H2COJ54K0']
# These are:
# H2CO 5(4)-4(4) at 364.103249 GHz
# H2CO 5(24)-4(23) at 363.945894 GHz
# HC3N 40-39 at 363.785397 GHz
# H2CO 5(05)-4(04) at 362.736048 GHz (actually a blend with HNC 4-3...)

brightest_line = 362.630304*u.GHz # HNC 4-3

# assume you have a constant expected width....
width = 150*u.km/u.s


# Use the brightest line to identify the appropriate peak velocities, but ONLY
# from a slab including +/- width:
brightest_cube = cube.with_spectral_unit(u.km/u.s, rest_value=brightest_line,
                                         velocity_convention='optical').spectral_slab(vz-width,
                                                                                      vz+width)

peak_velocity = brightest_cube.spectral_axis[brightest_cube.argmax(axis=0)]
pl.figure(2).clf()
pl.imshow(peak_velocity.value)
pl.colorbar()

# make a spatial mask excluding pixels with no signal
# (you can do better than this - this is the trivial, first try algorithm)
peak_amplitude = brightest_cube.max(axis=0)
# found this range from inspection of a spectrum:
# s = cube.max(axis=(1,2))
# s.quicklook()
noisemap = cube.spectral_slab(362.603*u.GHz, 363.283*u.GHz).std(axis=0)
spatial_mask = peak_amplitude > 3*noisemap

# Now loop over EACH line, extracting moments etc. from the appropriate region:
# we'll also apply a transition-dependent width (my_line_widths) here because
# these fainter lines do not have peaks as far out as the bright line.

for line_name,line_freq,line_width in zip(my_line_names,my_line_list,my_line_widths):

    subcube = cube.with_spectral_unit(u.km/u.s,
                                      rest_value=line_freq,
                                      velocity_convention='optical'
                                     ).spectral_slab(peak_velocity.min()-line_width,
                                                     peak_velocity.max()+line_width)

    # this part makes a cube of velocities
    temp = subcube.spectral_axis
    velocities = np.tile(temp[:,None,None], subcube.shape[1:])

    # now we use the velocities from the brightest line to create a mask region
    # in the same velocity range but with different rest frequencies (different
    # lines)
    mask = np.abs(peak_velocity - velocities) < line_width

    # Mask on a pixel-by-pixel basis with a 1-sigma cut
    signal_mask = subcube > noisemap

    # the mask is a cube, the spatial mask is a 2d array, but in this case
    # numpy knows how to combine them properly
    # (signal_mask is a different type, so it can't be combined with the others
    # yet - I'll add a feature request for that)
    msubcube = subcube.with_mask(mask & spatial_mask).with_mask(signal_mask)

    # you might want to use a line name instead of a frequency here....
    #
    # mkdir moment0
    for moment in (0,1,2):
        mom = msubcube.moment(order=moment, axis=0)
        mom.hdu.writeto("moment{0}/{1}_{2}_moment{0}.fits".format(moment,target,line_name), clobber=True)
        pl.figure(1).clf()
        mom.quicklook(filename='moment{0}/{1}_{2}_moment{0}.png'.format(moment,target,line_name))
