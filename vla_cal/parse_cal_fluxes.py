"""
Script to parse out the calibrator fluxes for a pipeline's weblog
"""
import glob
import os
import tarfile


def parse_logfile(data):
    if isinstance(data, str):
        # assume it is a filename
        with open(data,'rb') as fh:
            text = fh.readlines()
    else:
        # try this?
        text = data.readlines()


    table = {}

    start_recording=False
    for line in text:
        line = line.decode('utf-8')

        if (("fluxscale::pipeline.hifv.tasks.fluxscale.fluxboot::" in line or
             "fluxscale::::casa" in line) and
            "Fitting data with power law" in line):
            start_recording=True

            splitter = ("fluxscale::::casa" if "fluxscale::::casa" in line else
                        "fluxscale::pipeline.hifv.tasks.fluxscale.fluxboot::")

        if start_recording and "fitted spectral index & SNR" in line:
            source_name = line.split(splitter)[-1].split()[0]
            table[source_name] = {}

        if start_recording and splitter in line:
            line_data = line.split(splitter)[-1]
            try:
                freq, flux, eflux, fitflux = [float(x) for x in line_data.split()]
            except ValueError:
                # if it can't convert, it's not a float, give up.
                continue

            table[source_name][freq] = (flux, eflux, fitflux)

    return table

def get_date_from_listobs(data):

    if isinstance(data, str):
        # assume it is a filename
        with open(data,'rb') as fh:
            text = fh.readlines()
    else:
        # try this?
        text = data.readlines()

    for line in text:
        if "Observed from" in line.decode('utf-8'):
            startdate = line.decode('utf-8').split('Observed from')[-1].split()[0]

    return startdate

def process_weblog(dirname):
    table = {}
    if os.path.splitext(dirname)[-1] == '.tgz':
        tf = tarfile.open(dirname)

        listobs_ti = [x for x in tf.getnames() if 'listobs' in x][0]
        listobs_fh = tf.extractfile(listobs_ti)

        fluxboot_fh = tf.extractfile('weblog/logs/fluxboot.log')

        date = get_date_from_listobs(listobs_fh)
        
        fluxes = parse_logfile(fluxboot_fh)

    else:
        listobs_fn = glob.glob(os.path.join(dirname, "html/sessionSession_default/*/listobs.txt"))[0]
        flux_fn = os.path.join(dirname, 'html/stage13/casapy.log')

        fluxes = parse_logfile(flux_fn)
        date = get_date_from_listobs(listobs_fn)

    table[date] = fluxes

    return table

def process_all_weblogs(fn='weblog.tgz', startdir='.'):
    """
    Search current directory for files with specified name and process them all
    """

    table = {}

    for root, dirs, files in os.walk(startdir):

        for name in files:
            if name == fn:
                fullpath = os.path.join(root,name)
                print("Processing {0}".format(fullpath))
                table.update(process_weblog(fullpath))


    return table


def plot_cal_fluxes(tbl, sourcecenter=None, radius=None):
    # ignore dates...
    
    import pylab as pl
    import numpy as np
    calibrators = set([x for y in tbl for x in tbl[y]])

    coordinates = np.array([((float(cn[1:3]) + float(cn[3:5])/60.),
                            (float(cn[5:8]) + float(cn[8:10])/60.))
                           for cn in calibrators])
    meds = []

    for calname in calibrators:
        print(calname)
        xdata = []
        ydata = []
        for date in tbl:
            for cn in tbl[date]:
                if calname == cn:
                    for freq in tbl[date][cn]:
                        xdata.append(freq)
                        ydata.append(tbl[date][cn][freq][0])

        pl.figure(1).clf()
        pl.plot(xdata, ydata, '.')
        pl.xlabel("Frequency (GHz)")
        pl.ylabel("Flux (Jy)")
        pl.title(calname)
        pl.savefig("calibrator_flux_plot_{0}.png".format(calname))

        medflux = np.median(ydata)
        meds.append(medflux)


    pl.figure(1).clf()
    pl.scatter(coordinates.T[0], coordinates.T[1], s=np.array(meds)*100)
    pl.xlabel("RA")
    pl.ylabel("Dec")
    pl.savefig("calibrator_positions.png")

    if sourcecenter is not None and radius is not None:
        matches = ((coordinates.T[0]*360/24. - sourcecenter[0])**2 +
                   (coordinates.T[1] - sourcecenter[1])**2)**0.5 < radius


    pl.figure(1).clf()
    pl.scatter(coordinates.T[0][matches], coordinates.T[1][matches], s=np.array(meds)[matches]*100)
    pl.xlabel("RA")
    pl.ylabel("Dec")
    pl.savefig("calibrator_positions_zoom.png")
