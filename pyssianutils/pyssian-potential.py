#!/bin/usr/env python3

"""
Prints the Potential energy. Defaults to the 'Done' of l502 or l508
"""

import os

import argparse
from pyssian import GaussianOutFile
from pyssianutils.functions import potential_energy, write_2_file

__version__ = '0.0.0'

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('Files',help='Gaussian Output File',nargs='+')
parser.add_argument('-L','--ListFile',help="""When enabled instead of
                    considering the files provided as the gaussian output files
                    considers the file provided as a list of gaussian output
                    files""",action='store_true')
parser.add_argument('-O','--OutFile',help="""File to write the Data. If it
                    exists, the data will be appended""",default=None)
parser.add_argument('--Method',help="""If the Final Potential energy is not the
                    Energy of the 'SCF Done:' the target Potential Energy
                    has to be specified, otherwise defaults to the energy of the
                    'SCF Done:' """, choices=['mp2','mp2scs','mp4','ccsdt'],
                    default='default',type=lambda x: x.lower())
parser.add_argument('-q','--quiet',help="""if enabled does not print errors when
                    parsing files and instead only prints their name """,
                    default=False,action='store_true')
parser.add_argument('--version',version=f'script version {__version__}',
                    action='version')

if __name__ == "__main__":
    args = parser.parse_args()

    if args.ListFile:
        with open(args.Files[0],'r') as F:
            Files = [line.strip() for line in F]
    else:
        Files = args.Files

    OutFile = args.OutFile
    if args.OutFile is not None:
        OutFile = os.path.abspath(args.OutFile)
        WriteOutput = write_2_file(OutFile)
    else:
        WriteOutput = print

    # Format for the numbers
    txt = '{}\t{: 03.9f}'

    for IFile in Files:
        if not IFile: #In the case of an empty filename, write an empty line
            WriteOutput('')
            continue
        InFilepath = os.path.abspath(IFile)
        Name = IFile
        with GaussianOutFile(InFilepath,[502,508,804,913]) as GOF:
            GOF.update()
        try:
            U = potential_energy(GOF,args.Method)
        except IndexError as e:
            if not args.quiet:
                raise e
            else:
                WriteOutput(Name)
        else:
            msg = '{}\t{: 03.9f}'
            WriteOutput(txt.format(Name,U))
