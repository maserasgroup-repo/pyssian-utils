#!/bin/usr/env python3
"""
Prints the Potential energy, Zero point energy, Enthalpy and Free energy
from a gaussian frequency calculation. By default the Potential energy is
the value of the 'Done'
"""

import os
from pathlib import Path
import argparse
from pyssian import GaussianOutFile
from pyssian.chemistryutils import is_method
from pyssianutils.functions import thermochemistry, potential_energy, write_2_file

__version__ = '0.0.1'


def create_parser(): 
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('Files',help='Gaussian Output File',nargs='+')
    parser.add_argument('-L','--ListFile',help="""When enabled instead of
                        considering the files provided as the gaussian output files
                        considers the file provided as a list of gaussian output
                        files""",action='store_true')
    parser.add_argument('-O','--OutFile',help="""File to write the Data. If it
                        exists, the data will be appended, if not specified it will
                        print to the console""",default=None)
    parser.add_argument('--with-sp',help="""if enabled it will try to match the 
                        pattern provided to compute the SP corrections from the files
                        that match the pattern to provide the final energies""",
                        dest='with_sp',default=False,action='store_true')
    parser.add_argument('--pattern',help="""pattern used when matching the SP files, 
                        defaults to 'SP'""",
                        default='SP')
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
    return parser

def guess_method(GOF): 
    commandline = GOF.get_links(1)[-1].commandline
    # Assume that any "/" is not in any relevant keyword and it will only split 
    # a possible "method/basis" nomenclature
    commandline = commandline.replace('/',' ').split()
    method = 'default'
    for candidate in commandline: 
        if is_method(candidate): 
            method = candidate.lower()
    
    if method in ['oniom','mp2','mp2scs','mp4','ccsdt']: 
        return method
    else: 
        return 'default'

def parse_gaussianfile(ifile, number_fmt, pattern=None, verbose=False):
    
    ifile = Path(ifile)

    U,Z,H,G = '', '', '', ''

    with GaussianOutFile(ifile,[1,120,502,508,716,804,913,9999]) as GOF:
            GOF.read()
    method = guess_method(GOF)

    U = potential_energy(GOF,method)
    
    if U is None and not verbose: 
        U = ''
    elif verbose:
        raise RuntimeError(f'Potential Energy not found in file {ifile.name}')
    else: 
        U = number_fmt.format(U)
    
    try:
        Z,H,G = thermochemistry(GOF)
    except IndexError as e:
        if verbose: 
            raise e
    
    if Z: Z = number_fmt.format(Z)
    if H: H = number_fmt.format(H)
    if G: G = number_fmt.format(G)

    if pattern is None: # If no pattern is provided assume no SP info should be provided
        return U, Z, H, G, '', ''
    
    # now try to guess a SP 

    new_stem = ifile.stem + f'_{pattern}'
    sp_candidate = ifile.with_stem(new_stem)
    
    if not sp_candidate.exists(): # if no file is found do not provide SP corrections
        return U, Z, H, G, '', ''

    with GaussianOutFile(sp_candidate,[1,120,502,508,716,804,913,9999]) as GOF_sp:
            GOF_sp.read()
    
    method_sp = guess_method(GOF_sp)
    U_sp = potential_energy(GOF_sp,method_sp)

    if U_sp is None: 
        U_sp = ''
    else: 
        U_sp = number_fmt.format(U_sp)
    
    try:
        G_sp = float(U_sp) + (float(G) - float(U))
    except ValueError: 
        G_sp = ''
    else:
        G_sp = number_fmt.format(G_sp)
    
    return U, Z, H, G, U_sp, G_sp
    
if __name__ == "__main__":
    parser = create_parser()
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
    if args.with_sp:
        n = largest_filename = max([len(File)+len(args.pattern) for File in Files])
    else:
        n = largest_filename = max([len(File) for File in Files])

    name_format = f'{{: <{n}}}'

    # Values format
    number_fmt = '{: 03.9f}'
    largest_value = len(number_fmt.format(10000))
    value_fmt = f'{{: ^{largest_value}}}'
    spacer = '    '

    if args.with_sp: 
        line_fmt = spacer.join([name_format,]*2+[value_fmt,]*6)
    else:
        line_fmt = spacer.join([name_format,]+[value_fmt,]*4)

    # Write table header
    if args.with_sp:
        WriteOutput(line_fmt.format(f'{{: ^{n}}}'.format('File'),
                                    f'{{: ^{n}}}'.format('File_SP'),
                                    'U','Z','H','G','U(SP)','G(final)'))
    else:
        WriteOutput(line_fmt.format(f'{{: ^{n}}}'.format('File'),
                                    'U','Z','H','G'))

    # Actual parsing
    for IFile in Files:
        if not IFile: #In the case of an empty filename, write an empty line
            WriteOutput('')
            continue
        if Path(IFile).stem.endswith(args.pattern) and args.with_sp: 
            continue
        InFilepath = os.path.abspath(IFile)
        Name = IFile

        if args.with_sp: 
            U,Z,H,G,U_sp,G_sp = parse_gaussianfile(InFilepath,number_fmt,args.pattern,args.verbose)
        else:
            U,Z,H,G,U_sp,G_sp = parse_gaussianfile(InFilepath,number_fmt,None,args.verbose)
        
        if U_sp: # assume it found the matching SP file
            IFile_sp = str(Path(IFile).with_stem(Path(IFile).stem+f'_{args.pattern}'))
        
        U,Z,H,G,U_sp,G_sp = map(value_fmt.format,[U,Z,H,G,U_sp,G_sp])

        if args.with_sp:
            WriteOutput(line_fmt.format(IFile,IFile_sp,U,Z,H,G,U_sp,G_sp))
        else:
            WriteOutput(line_fmt.format(IFile,U,Z,H,G))
