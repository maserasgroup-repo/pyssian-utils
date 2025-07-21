"""
Prints the Potential energy, Zero point energy, Enthalpy and Free energy
from a gaussian frequency calculation. By default the Potential energy is
the value of the 'Done'
"""
import argparse
from pathlib import Path

from pyssian import GaussianOutFile
from pyssian.chemistryutils import is_method
from ..utils import (thermochemistry, potential_energy, 
                     write_2_file, ALLOWEDMETHODS)
from ..initialize import load_app_defaults

# Load app defaults
DEFAULTS = load_app_defaults()
NUMBER_FMT = DEFAULTS['print']['energy_hartree_fmt']

# Utility Functions
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

    E,Z,H,G = '', '', '', ''

    with GaussianOutFile(ifile,[1,120,502,508,716,804,913,9999]) as GOF:
            GOF.read()
    
    if method is None:
        method = guess_method(GOF)

    E = potential_energy(GOF,method)
    
    if E is None and not verbose: 
        E = ''
    elif verbose:
        raise RuntimeError(f'Potential Energy not found in file {ifile.name}')
    else: 
        E = number_fmt.format(E)
    
    try:
        Z,H,G = thermochemistry(GOF)
    except IndexError as e:
        if verbose: 
            raise e
    
    if Z: Z = number_fmt.format(Z)
    if H: H = number_fmt.format(H)
    if G: G = number_fmt.format(G)

    return E, Z, H, G

# Parser and Main definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Output File(s)',nargs='+')
parser.add_argument('-l','--listfile',
                    action='store_true', dest='is_listfile',
                    help="When enabled instead of considering the files provided "
                    "as the gaussian output files considers the file provided as "
                    "a list of gaussian output files")
parser.add_argument('-o','--outfile',
                    default=None,
                    help="File to write the Data. If it exists, the data will be "
                    "appended. If none is provided it will be printed to stdout")
parser.add_argument('--method',
                    choices=ALLOWEDMETHODS,
                    default='default', type=lambda x: x.lower(),
                    help="When not provided it will attempt (and may fail) to "
                    "guess the method used for the calculation to correctly "
                    "read the potential energy. Otherwise it defaults to the "
                    "Energy of the 'SCF Done:'")
parser.add_argument('--only-stem',
                    dest='only_stem',
                    default=False, action='store_true',
                    help="only show the file stem instead of the full path")
parser.add_argument('-v','--verbose',
                    default=False, action='store_true',
                    help="if enabled it will raise an error anytime it is "
                    "unable to find the thermochemistry of the provided file")

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
    number_fmt = NUMBER_FMT
    largest_value = len(number_fmt.format(10000))
    value_fmt = f'{{: ^{largest_value}}}'
    spacer = '    '

    line_fmt = spacer.join([name_format,]+[value_fmt,]*4)

    # Write table header
    write_output(line_fmt.format(name_format.format('File'),'E','Z','H','G'))

    # Actual parsing
    for ifile in files:
        if not ifile: #In the case of an empty filename, write an empty line
            write_output('')
            continue

        filepath = Path(ifile)

        with GaussianOutFile(filepath,[1,120,502,508,716,804,913,9999]) as GOF:
            GOF.read()
        
        E,Z,H,G = parse_gaussianfile(filepath, 
                                     number_fmt,
                                     method,
                                     verbose)
        
        name = ifile
        if only_stem:
            name = filepath.stem

        write_output(line_fmt.format(name,E,Z,H,G))
