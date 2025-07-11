"""
Prints the Potential energy, Zero point energy, Enthalpy and Free energy
from a gaussian frequency calculation. By default the Potential energy is
the value of the 'Done'
"""
from pathlib import Path

from pyssian import GaussianOutFile
from pyssian.chemistryutils import is_method
from ..utils import (thermochemistry, potential_energy, 
                                    write_2_file, ALLOWEDMETHODS)

# typing imports
import argparse

def add_subparser(parser:argparse._SubParsersAction):
    subparser = parser.add_parser('thermo', help=__doc__)
    subparser.add_argument('files',help='Gaussian Output File(s)',nargs='+')
    subparser.add_argument('-l','--listfile',help="""When enabled instead of
                           considering the files provided as the gaussian output files
                           considers the file provided as a list of gaussian output
                           files""",action='store_true',dest='is_listfile')
    subparser.add_argument('-o','--outfile',help="""File to write the Data. If it
                           exists, the data will be appended. If none is provided 
                           it will be printed to stdout""",default=None)
    subparser.add_argument('--method',help=""" When not provided it will 
                           attempt (and may fail) to guess the method used 
                           for the calculation to correctly read the potential
                           energy. Otherwise it defaults to the Energy of the
                           'SCF Done:' """, 
                           choices=ALLOWEDMETHODS,
                           default='default',type=lambda x: x.lower())
    subparser.add_argument('--only-stem',help=""" only show the file stem 
                           instead of the full path """,default=False,
                           action='store_true',dest='only_stem')
    subparser.add_argument('-v','--verbose',help="""if enabled it will raise an error
                           anytime it is unable to find the thermochemistry of the 
                           provided file""", default=False,action='store_true')

def guess_method(GOF:GaussianOutFile): 
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

def parse_gaussianfile(ifile:str|Path, 
                       number_fmt:str,
                       method:str|None=None,
                       verbose:bool=False) -> tuple[str]:
    
    ifile = Path(ifile)

    U,Z,H,G = '', '', '', ''

    with GaussianOutFile(ifile,[1,120,502,508,716,804,913,9999]) as GOF:
            GOF.read()
    
    if method is None:
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

    return U, Z, H, G

def main(files:list[str],
         is_listfile:bool=False,
         method:str|None=None,
         outfile:Path|str|None=None,
         only_stem:bool=False,
         verbose:bool=False
         ):

    assert method in ALLOWEDMETHODS+[None]

    if is_listfile:
        with open(files[0],'r') as F:
            files = [line.strip() for line in F]

    if outfile is not None:
        outfile = Path(outfile)
        write_output = write_2_file(outfile)
    else:
        write_output = print

    # Header column's names
    n = largest_filename_len = max([len(f) for f in files])
    if only_stem:
        n = max([len(Path(f).stem) for f in files])

    name_format = f'{{: <{n}}}'

    # Values format
    number_fmt = '{: 03.9f}'
    largest_value = len(number_fmt.format(10000))
    value_fmt = f'{{: ^{largest_value}}}'
    spacer = '    '

    line_fmt = spacer.join([name_format,]+[value_fmt,]*4)

    # Write table header
    write_output(line_fmt.format(name_format.format('File'),'U','Z','H','G'))

    # Actual parsing
    for ifile in files:
        if not ifile: #In the case of an empty filename, write an empty line
            write_output('')
            continue

        filepath = Path(ifile)

        with GaussianOutFile(filepath,[1,120,502,508,716,804,913,9999]) as GOF:
            GOF.read()
        
        U,Z,H,G = parse_gaussianfile(filepath, 
                                     number_fmt,
                                     method,
                                     verbose)
        
        name = ifile
        if only_stem:
            name = filepath.stem

        write_output(line_fmt.format(name,U,Z,H,G))
