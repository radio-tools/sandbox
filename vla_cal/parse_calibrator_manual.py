import os
import numpy as np
import requests
from astropy import coordinates
from astropy.table import Table,Column
from bs4 import BeautifulSoup
import re

def get_page(url="http://www.aoc.nrao.edu/~gtaylor/csource.html"):
    if os.path.exists(os.path.basename(url)):
        with open(os.path.basename(url), 'r') as fh:
            text = fh.read()
    else:
        response = requests.get(url)
        root = BeautifulSoup(response.content, 'html5lib')

        pre = root.find('pre')
        text = pre.get_text()

    return text

def parse_cal_man(text):

    RA_re = re.compile("([0-9][0-9]h[0-9][0-9]m[0-9][0-9].[0-9]{6}s)")
    DEC_re = re.compile("([0-9][0-9]d[0-9][0-9]'[0-9][0-9].[0-9]{6}\")")

    start_recording=False

    table = {}
    for line in text.split("\n"):

        lsplit = line.split()

        if 'J2000' in line:
            source = {}
            source['jname'] = lsplit[0]
            source['PC'] = lsplit[2]
            source['coordinates'] = coordinates.SkyCoord(lsplit[3], lsplit[4], frame='fk5')
            table[source['jname']] = source
            start_recording=False

        if 'BAND' in line:
            start_recording = True
            continue

        if start_recording and len(lsplit) >= 7:
            band = {}
            band['Name'] = lsplit[0] + " " + lsplit[1]
            band['Quality'] = {'A': lsplit[2],
                               'B': lsplit[3],
                               'C': lsplit[4],
                               'D': lsplit[5],
                              }
            try:
                band['Flux'] = float(lsplit[6])
            except ValueError:
                band['Flux'] = np.nan

            source[band['Name']] = band

    return table

def dicts_to_table(data):

    bands = ['90cm P', '20cm L', '6cm C', '3.7cm X', '2cm U', '1.3cm K', '0.7cm Q',]
    columns = ['Source Name', 'RA2000', 'Dec2000', 'PC', ] + [band + ":" + suffix for band in bands for suffix in ('A','B','C','D','Flux')]
    #coltypes = [str, str, str, str, ] + [str, str, str, str, float]*len(bands)

    coldata = [[] for _ in columns]
    for sourcename in data:
        source = data[sourcename]

        coldata[0].append(sourcename)
        coldata[1].append(source['coordinates'].ra.deg)
        coldata[2].append(source['coordinates'].dec.deg)
        coldata[3].append(source['PC'])
        for ii,band in enumerate(bands):
            if band in source:
                coldata[4+5*(ii)+0].append(source[band]['Quality']['A'])
                coldata[4+5*(ii)+1].append(source[band]['Quality']['B'])
                coldata[4+5*(ii)+2].append(source[band]['Quality']['C'])
                coldata[4+5*(ii)+3].append(source[band]['Quality']['D'])
                coldata[4+5*(ii)+4].append(source[band]['Flux'])
            else:
                coldata[4+5*(ii)+0].append(' ')
                coldata[4+5*(ii)+1].append(' ')
                coldata[4+5*(ii)+2].append(' ')
                coldata[4+5*(ii)+3].append(' ')
                coldata[4+5*(ii)+4].append(np.nan)

    tbl = Table([Column(data=dat, name=colname) for dat, colname in zip(coldata, columns)])

    return tbl

def get_and_parse_cal_man():
    text = get_page()
    parsedtxt = parse_cal_man(text)
    return dicts_to_table(parsedtxt)

def write_cal_man(outfile='/Users/adam/repos/radio-astro-tools-sandbox/vla_cal/cal_manual.txt'):
    calman = get_and_parse_cal_man()

    calman.sort('RA2000')
    calman.write(outfile, format='ascii.fixed_width')
