"""
Prints the Potential energy. Defaults to the 'Done' of l502 or l508
"""
import argparse
from pathlib import Path

from pyssian import GaussianOutFile
from pyssian.chemistryutils import is_method
from ..utils import potential_energy, write_2_file, ALLOWEDMETHODS
from ..initialize import load_app_defaults

# Load app defaults
DEFAULTS = load_app_defaults()
NUMBER_FMT = DEFAULTS['print']['energy_hartree_fmt']

# Utility functions
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
                       verbose:bool=False) -> str:
    
    ifile = Path(ifile)

    with GaussianOutFile(ifile,[1,120,502,508,716,804,913,9999]) as GOF:
            GOF.read()
    
    method = guess_method(GOF)

    E = potential_energy(GOF,method)
    
    if E is None and not verbose: 
        return ''
    elif verbose:
        raise RuntimeError(f'Potential Energy not found in file {ifile.name}')

    return number_fmt.format(E)

# Parser and Main Definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Output File(s)',nargs='+')
parser.add_argument('-l','--listfile',
                    action='store_true',dest='is_listfile',
                    help="When enabled instead of considering the files provided "
                    "as the gaussian output files considers the file provided as "
                    "a list of gaussian output files")
parser.add_argument('-o','--outfile',
                    default=None,
                    help="File to write the Data. If it exists, the data will be "
                    "appended. If none is provided it will be printed to stdout")
parser.add_argument('--method',
                    choices=ALLOWEDMETHODS,
                    default='default',type=lambda x: x.lower(),
                    help="When not provided it will attempt (and may fail) to "
                    "guess the method used for the calculation to correctly read "
                    "the potential energy. Otherwise it defaults to the Energy of "
                    "the 'SCF Done:' ")
parser.add_argument('-v','--verbose',
                    default=False,action='store_true',
                    help="if enabled it will raise an error anytime it is unable "
                    "to find the energy of the provided file")

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
    number_fmt = NUMBER_FMT
    largest_value = len(number_fmt.format(10000))
    value_fmt = f'{{: ^{largest_value}}}'

    line_fmt = f'{name_format}{spacer}{value_fmt}'

    for ifile in files:
        if not ifile: #In the case of an empty filename, write an empty line
            write_output('')
            continue
        
        E = parse_gaussianfile(ifile,
                               number_fmt,
                               verbose)
        
        write_output(line_fmt.format(str(ifile),E))
