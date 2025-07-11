"""
Prints the Potential energy. Defaults to the 'Done' of l502 or l508
"""
from pathlib import Path

from pyssian import GaussianOutFile
from pyssian.chemistryutils import is_method
from ..utils import potential_energy, write_2_file, ALLOWEDMETHODS

# typing imports
import argparse

def add_subparser(parser:argparse._SubParsersAction):
    subparser = parser.add_parser('potential', help=__doc__)
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
    subparser.add_argument('-v','--verbose',help="""if enabled it will raise an error
                           anytime it is unable to find the energy of the provided file
                           """, default=False,action='store_true')

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
                       verbose:bool=False) -> tuple[str]:
    
    ifile = Path(ifile)

    U = ''

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
    
    return U

def main(
         files:list[str|Path],
         is_listfile:bool=False,
         method:str|None=None,
         outfile:Path|str|None=None,
         verbose:bool=False
         ):

    assert method in ALLOWEDMETHODS+[None]

    if is_listfile:
        with open(files[0],'r') as F:
            files = [line.strip() for line in F]
    else:
        files = [Path(f) for f in files]

    if outfile is not None:
        outfile = Path(outfile)
        write_output = write_2_file(outfile)
    else:
        write_output = print

    largest_filename_len = max([len(str(ifile)) for ifile in files])
    name_format = f'{{: <{largest_filename_len}}}'
    spacer = '    '

    # Format for the numbers
    number_fmt = '{: 03.9f}'
    largest_value = len(number_fmt.format(10000))
    value_fmt = f'{{: ^{largest_value}}}'

    line_fmt = f'{name_format}{spacer}{value_fmt}'

    for ifile in files:
        if not ifile: #In the case of an empty filename, write an empty line
            write_output('')
            continue
        
        U = parse_gaussianfile(ifile,
                               number_fmt,
                               verbose)
        
        write_output(line_fmt.format(str(ifile),U))
