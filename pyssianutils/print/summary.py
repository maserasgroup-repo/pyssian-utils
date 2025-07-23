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
                       pattern:str|None=None,
                       method:str|None=None,
                       method_sp:str|None=None,
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

    if pattern is None: # If no pattern is provided assume no SP info should be provided
        return E, Z, H, G, '', ''
    
    # now try to guess a SP 

    new_stem = ifile.stem + f'_{pattern}'
    sp_candidate = ifile.with_stem(new_stem)
    
    if not sp_candidate.exists(): # if no file is found do not provide SP corrections
        return E, Z, H, G, '', ''

    with GaussianOutFile(sp_candidate,[1,120,502,508,716,804,913,9999]) as GOF_sp:
            GOF_sp.read()
    
    if method_sp is None: 
        method_sp = guess_method(GOF_sp)
    
    U_sp = potential_energy(GOF_sp,method_sp)

    if U_sp is None: 
        U_sp = ''
    else: 
        U_sp = number_fmt.format(U_sp)
    
    try:
        G_sp = float(U_sp) + (float(G) - float(E))
    except ValueError: 
        G_sp = ''
    else:
        G_sp = number_fmt.format(G_sp)
    
    return E, Z, H, G, U_sp, G_sp

# Parser and Main definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Output File(s)',nargs='+')
parser.add_argument('-l','--listfile',
                    action='store_true', dest='is_listfile',
                    help="When enabled instead of considering the files "
                    "provided as the gaussian output files considers the file "
                    "provided as a list of gaussian output files")
parser.add_argument('-o','--outfile',
                    default=None,
                    help="File to write the Data. If it exists, the data will "
                    "be appended. If none is provided it will be printed to stdout")
parser.add_argument('--with-sp',
                    dest='with_sp',
                    default=False, action='store_true',
                    help="if enabled it will try to match the pattern provided "
                    "to compute the SP corrections from the files that match "
                    "the pattern to provide the final energies")
parser.add_argument('--pattern',
                    default='SP',
                    help="pattern used when matching the SP files, defaults to 'SP'")
parser.add_argument('--method',
                    choices=ALLOWEDMETHODS + ['default'],
                    default='default', type=lambda x: x.lower(),
                    help="When not provided it will attempt (and may fail) to "
                    "guess the method used for the calculation to correctly "
                    "read the potential energy. Otherwise it defaults to the "
                    "Energy of the 'SCF Done:' ")
parser.add_argument('--method-sp',
                    dest='method_sp',type=lambda x: x.lower(),
                    choices=ALLOWEDMETHODS, default='default', 
                    help="When not provided it will attempt (and may fail) to "
                    "guess the method used for the SP calculation to correctly "
                    "read the potential energy. Otherwise it defaults to the "
                    "Energy of the 'SCF Done:' ", )
parser.add_argument('--only-stem',
                    dest='only_stem',
                    default=False, action='store_true',
                    help="only show the file stem instead of the full path ")
parser.add_argument('-v','--verbose',
                    default=False, action='store_true',
                    help="if enabled it will raise an error anytime it is "
                    "unable to find the thermochemistry of the provided file")

def main(files:list[str],
         is_listfile:bool=False,
         method:str|None=None,
         method_sp:str|None=None,
         outfile:Path|str|None=None,
         with_sp:bool=False,
         pattern:str='SP',
         only_stem:bool=False,
         verbose:bool=False
         ):
    if is_listfile:
        with open(files[0],'r') as F:
            files = [line.strip() for line in F]
    else:
        files = files

    if outfile is not None:
        outfile = Path(outfile)
        write_output = write_2_file(outfile)
    else:
        write_output = print

    # Header to know which is each column
    n = largest_filename = max([len(f)+len(pattern) for f in files])
    if only_stem:
        n = max([len(Path(f).stem)+len(pattern) for f in files])
    if not with_sp: 
        n = n - len(pattern)

    name_format = f'{{: <{n}}}'

    # Values format
    number_fmt = NUMBER_FMT
    largest_value = len(number_fmt.format(10000))
    value_fmt = f'{{: ^{largest_value}}}'
    spacer = '    '

    # Write header and prepare line format
    if with_sp: 
        line_fmt = spacer.join([name_format,]*2+[value_fmt,]*6)
        write_output(line_fmt.format(f'{{: ^{n}}}'.format('File'),
                                     f'{{: ^{n}}}'.format('File_SP'),
                                     'E','Z','H','G','E(SP)','G(final)'))
    else:
        line_fmt = spacer.join([name_format,]+[value_fmt,]*4)
        write_output(line_fmt.format(f'{{: ^{n}}}'.format('File'),
                                     'E','Z','H','G'))

    # Actual parsing
    for ifile in files:
        if not ifile: #In the case of an empty filename, write an empty line
            write_output('')
            continue

        filepath = Path(ifile)
        if with_sp and filepath.stem.endswith(pattern): 
            continue

        if not with_sp:
            pattern = method_sp = None

        E,Z,H,G,U_sp,G_sp = parse_gaussianfile(filepath,
                                               number_fmt,
                                               pattern,
                                               method,
                                               method_sp,
                                               verbose)
        
        if U_sp: # assume it found the matching SP file
            ifile_sp = str(filepath.with_stem(f'{filepath.stem}_{pattern}'))
        else:
            ifile_sp = ''
        
        E,Z,H,G,U_sp,G_sp = map(value_fmt.format,[E,Z,H,G,U_sp,G_sp])

        name = ifile
        name_sp = ifile_sp
        if with_sp:
            if only_stem: 
                name = filepath.stem
                name_sp = Path(ifile_sp).stem

            write_output(line_fmt.format(name,name_sp,E,Z,H,G,U_sp,G_sp))
        else:
            if only_stem: 
                name = filepath.stem
            
            write_output(line_fmt.format(name,E,Z,H,G))
