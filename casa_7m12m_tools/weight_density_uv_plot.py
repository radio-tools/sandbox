import numpy as np
import pylab as pl

def plot_weight_density(vis, spw=0, field='', nbins=50, bins=None):

    mymsmd = msmdtool()
    mymsmd.open(vis)
    reffreq = "{value}{unit}".format(**mymsmd.reffreq(spw)['m0'])
    reffreq = "{0}Hz".format(mymsmd.meanfreq(spw))
    closest_channel = np.argmin(np.abs(mymsmd.chanfreqs(spw) - mymsmd.meanfreq(spw)))
    mymsmd.close()

    myms = mstool()

    myms.open(vis)
    myms.selectinit(0)
    myms.msselect(dict(field=field, spw=reffreq))
    myms.selectchannel(start=closest_channel, nchan=1, inc=1, width=1)
    datadict=myms.getdata(['UVW', 'WEIGHT', 'FLAG'])
    myms.close()
    wt = datadict['weight']
    uvw = datadict['uvw']
    # We have exactly one channel (we forced it above) and the second index
    # should be the channel ID
    # If the flag shape does not conform to this assumption, we're in trouble
    flags = datadict['flag'][:,0,:]


    # calculate the UV distance from the uvw array
    uvd = (uvw[:2,:]**2).sum(axis=0)**0.5

    if bins is None:
        bins = np.linspace(uvd.min(), uvd.max(), nbins)

    if flags.shape != wt.shape:
        if flags.shape[0] == wt.shape[1]:
            flags = flags.T
        else:
            raise ValueError("Flag shape and weight shape don't match. "
                             "Flag shape: {0}  Weight shape: {1}".format(
                                 flags.shape,wt.shape))

    # set weights to zero because we're adding them (this is obviously not right
    # for many operations, but it is right here!)
    wt[flags] = 0

    # one plot for each polarization
    h_1 = np.histogram(uvd, bins, weights=wt[0,:])
    h_2 = np.histogram(uvd, bins, weights=wt[1,:])

    # plot points at the bin center
    midbins = (bins[:-1] + bins[1:])/2.
    # compute the bin area for division below
    bin_area = (bins[1:]**2-bins[:-1]**2)*np.pi

    pl.clf()
    pl.plot(midbins, h_1[0]/bin_area, drawstyle='steps-mid')
    pl.plot(midbins, h_2[0]/bin_area, drawstyle='steps-mid')
    pl.xlabel("UV Distance")
    pl.ylabel("Sum of weights / annular area")
