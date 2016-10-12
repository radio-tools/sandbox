"""
Script to parse out the calibrator fluxes for a pipeline's weblog
"""
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
        listobs_fn = os.path.join(dirname, "html/sessionSession_default/listobs.txt")
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
