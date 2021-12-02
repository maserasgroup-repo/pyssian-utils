#!/bin/usr/env python3
"""
Prints the Potential energy, Zero point energy, Enthalpy and Free energy
from a gaussian frequency calculation. By default the Potential energy is
the value of the 'Done'
"""

import os

import argparse
from pyssian import GaussianOutFile
from pyssianutils.functions import thermochemistry, potential_energy, write_2_file

__version__ = '0.0.1'

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('Files',help='Gaussian Output File',nargs='+')
parser.add_argument('-L','--ListFile',help="""When enabled instead of
                    considering the files provided as the gaussian output files
                    considers the file provided as a list of gaussian output
                    files""",action='store_true')
parser.add_argument('-O','--OutFile',help="""File to write the Data. If it
                    exists, the data will be appended, if not specified it will
                    print to the console""",default=None)
parser.add_argument('--Method',help="""If the Final Potential energy is not the
                    Energy of the 'SCF Done:' the target Potential Energy
                    has to be specified, otherwise defaults to the energy of the
                    'SCF Done:' """, 
                    choices=['oniom','mp2','mp2scs','mp4','ccsdt'],
                    default='default',type=lambda x: x.lower())
parser.add_argument('-v','--verbose',help="""if enabled it will raise an error
                    anytime it is unable to find the thermochemistry of the 
                    provided file""", default=False,action='store_true')
parser.add_argument('--version',version=f'script version{__version__}',
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

    # Header to know which is each column
    n = largest_filename = max([len(File) for File in Files])
    name_format = f'{{: <{n}}}'

    # Values format
    number_fmt = '{: 03.9f}'
    largest_value = len(number_fmt.format(10000))
    value_fmt = f'{{: ^{largest_value}}}'
    spacer = '    '

    line_fmt = spacer.join([name_format,]+[value_fmt,]*4)

    # Write table header
    WriteOutput(line_fmt.format(f'{{: ^{n}}}'.format('File'),'U','Z','H','G'))

    # Actual parsing
    for IFile in Files:
        if not IFile: #In the case of an empty filename, write an empty line
            WriteOutput('')
            continue
        InFilepath = os.path.abspath(IFile)
        Name = IFile
        with GaussianOutFile(InFilepath,[1,120,502,508,716,804,913,9999]) as GOF:
            GOF.read()
        
        U = potential_energy(GOF,args.Method)
        
        if U is not None: 
            U = value_fmt.format(number_fmt.format(U))
        elif args.verbose:
            raise RuntimeError(f'Potential Energy not found in file {IFile}')
        else:
            U = value_fmt.format('')

        try:
            Z,H,G = thermochemistry(GOF)
        except IndexError as e:
            Z = value_fmt.format('')
            H = value_fmt.format('')
            G = value_fmt.format('')
        else:
            Z = value_fmt.format(number_fmt.format(Z))
            H = value_fmt.format(number_fmt.format(H))
            G = value_fmt.format(number_fmt.format(G))
        
        WriteOutput(line_fmt.format(IFile,U,Z,H,G))
