"""
Script to parse out the calibrator fluxes for a pipeline's weblog
"""
import os

def parse_logfile(data):
    if isinstance(data, str):
        # assume it is a filename
        with open(data,'r') as fh:
            text = fh.readlines()
    else:
        # try this?
        text = data.readlines()


    table = {}

    start_recording=False
    for line in text:
        if ("fluxscale::pipeline.hifv.tasks.fluxscale.fluxboot::" in line and
            "Fitting data with power law" in line):
            start_recording=True

        if "fitted spectral index & SNR" in line and start_recording:
            source_name = line.split("fluxscale::pipeline.hifv.tasks.fluxscale.fluxboot::")[-1].split()[0]
            table[source_name] = {}

        if "fluxscale::pipeline.hifv.tasks.fluxscale.fluxboot::" in line and start_recording:
            line_data = line.split("fluxscale::pipeline.hifv.tasks.fluxscale.fluxboot::")[-1]
            try:
                freq, flux, eflux, fitflux = [float(x) for x in line_data.split()]
            except ValueError:
                # if it can't convert, it's not a float, give up.
                continue

            table[source_name][freq] = (flux, eflux, fitflux)

    return table

def process_weblog(dirname):
    fn = os.path.join(dirname, 'html/stage13/casapy.log')

    return parse_logfile(fn)
