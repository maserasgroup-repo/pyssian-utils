#!/bin/usr/env python3

"""
Generates an xyz file from the provided gaussian files. For output files, it 
extracts the last geometry (unless --step is specified). This script is meant 
for quick inspections of gaussian outputs using other GUI tools such as jmol. 
"""

import os
from pathlib import Path
import argparse
from functools import partial

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry

__version__ = '0.1.0'

GAUSSIAN_INPUT_SUFFIX = '.com'
GAUSSIAN_OUTPUT_SUFFIX = '.log'

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Input/Output Files',nargs='+')
parser.add_argument('-L','--listfile',
                    action='store_true',
                    help="""When enabled instead of considering the files 
                    provided as the gaussian output files considers the file 
                    provided as a list of gaussian output files""")
parser.add_argument('-o','--outfile',
                    default=Path('all_geometries.xyz'),
                    type=Path,
                    help="""Name of the xyz file with all the provided 
                    geometries sorted by filename""")
parser.add_argument('--step',
                    default=None,
                    type=int,
                    help=""" Will attempt to access the ith optimization step of
                    a gaussian output file to extract its geometry on all files 
                    provided. 'initial geometry'='1'""")
parser.add_argument('--version',
                    version=f'script version {__version__}',
                    action='version')

def select_input_files(files,is_listfile=False): 
    if is_listfile:
        with open(files[0],'r') as F:
            inputfiles = [line.strip() for line in F]
    else:
        inputfiles = files
    return list(sorted(inputfiles))
def select_suffix(suffix): 
    """
    Ensures proper formatting of the suffixes used for gaussian inputs and 
    outputs and changes the values of the global variables GAUSSIAN_INPUT_SUFFIX,
    GAUSSIAN_OUTPUT_SUFFIX accordingly
    """
    
    if suffix is None:
        return GAUSSIAN_INPUT_SUFFIX
    in_suffix = suffix
    if in_suffix.startswith('.'): 
        return in_suffix.rstrip()
    return f'.{in_suffix}'

def info_from_gau_output(filepath,step=None): 
    with GaussianOutFile(filepath,[1,101,202]) as GOF:
        GOF.update()
    if step is None:
        L202 = GOF.get_links(202)[-1]
    else:
        L202 = GOF[0].get_links(202)[step-1]
    geom = Geometry.from_L202(L202)
    return geom
def info_from_gau_input(filepath):
    with GaussianInFile(filepath) as GIF:
        GIF.read()
    geom = Geometry.from_Input(GIF)
    return geom

def extract_geom(filepath,step=None): 
    suffix = Path(filepath).suffix
    if suffix in ['.in','.com','.gjf']: 
        return info_from_gau_input(filepath)
    if suffix in ['.log','.out'] and step is None:
        return info_from_gau_output(filepath)
    elif suffix in ['.log','.out']:
        return info_from_gau_output(filepath,step)
    if suffix == '.xyz': 
        return Geometry.from_xyz(filepath)
    raise NotImplementedError(f'files with suffix "{suffix}" cannot be interpreted')

if __name__ == "__main__":
    args = parser.parse_args()

    inputfiles = select_input_files(args.files,args.listfile)

    xyz = []
    for ifile in inputfiles:
        print(ifile)
        infilepath = Path(ifile)
        stem = infilepath.stem
        title = f'{stem}'
        geom = extract_geom(infilepath, step=args.step)
        xyz.append(geom.to_xyz(title=title))

    with open(args.outfile,'w') as F:
        F.write(''.join(xyz))
