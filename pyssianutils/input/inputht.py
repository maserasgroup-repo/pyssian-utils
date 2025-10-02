"""
Generates a gaussian input files from the last geometry of gaussian output files
or from the geometry of gaussian input files or a .xyz file using a Header 
and/or Tail Files which contain everything but the geometry and spin/charge (
which must be provided for .xyz files)
"""
from pathlib import Path
import argparse

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry
from ..initialize import load_app_defaults

# Load app defaults
DEFAULTS = load_app_defaults()
GAUSSIAN_INPUT_SUFFIX = DEFAULTS['common']['in_suffix']
GAUSSIAN_OUTPUT_SUFFIX = DEFAULTS['common']['out_suffix']
DEFAULT_SUFFIX = GAUSSIAN_INPUT_SUFFIX
DEFAULT_MARKER = DEFAULTS['common']['default_marker']
GAUSSIAN_IN_SUFFIXES = DEFAULTS['common']['gaussian_in_suffixes'][1:-1].split(',')
GAUSSIAN_OUT_SUFFIXES = DEFAULTS['common']['gaussian_out_suffixes'][1:-1].split(',')
DEFAULT_CHARGE = DEFAULTS['input.inputht'].getint('charge')
DEFAULT_SPIN = DEFAULTS['input.inputht'].getint('spin')

# Utility Functions
def select_input_files(files:list[Path|str],is_listfile:bool=False) -> list[Path]: 
    if is_listfile:
        with open(files[0],'r') as F:
            inputfiles = [Path(line.strip()) for line in F]
    else:
        inputfiles = [Path(f) for f in files]
    return inputfiles
def prepare_suffix(suffix:str) -> str: 
    """
    Ensures proper formatting of the suffixes used for gaussian inputs
    """
    if suffix.startswith('.'):
        suffix = suffix.rstrip()
    else: 
        suffix = f'.{suffix.strip()}'

    return suffix

def prepare_header(filepath:Path|None):
    
    if filepath is None:
        return ''
    
    with open(filepath,'r') as F:
        aux = [line.strip() for line in F]
    
    while len(aux)>=1 and not aux[0]:
        _ = aux.pop(0)
    while len(aux)>=1 and not aux[-1]:
        _ = aux.pop(-1)
    
    return '\n'.join(aux)
def prepare_tail(filepath:Path|None):
    if filepath is None: 
        return ''
    
    with open(filepath,'r') as F:
        aux = [line.strip() for line in F]
    
    while len(aux)>=1 and not aux[0]:
        _ = aux.pop(0)
    
    while len(aux)>=1 and not aux[-1]:
        _ = aux.pop(-1)
    
    return '\n'.join(aux)

def info_from_gau_output(filepath,step=None): 
    with GaussianOutFile(filepath,[1,101,202]) as GOF:
        GOF.update()
    L101 = GOF.get_links(101)[0]
    spin = L101.spin
    charge = L101.charge
    if step is None:
        L202 = GOF.get_links(202)[-1]
    else:
        L202 = GOF[0].get_links(202)[step-1]
    geom = Geometry.from_L202(L202)
    return geom, charge, spin
def info_from_gau_input(filepath):
    with GaussianInFile(filepath) as GIF:
        GIF.read()
    geom = Geometry.from_Input(GIF)
    spin = GIF.spin
    charge = GIF.charge
    return geom, charge, spin
def extract_geom_spin_and_charge(filepath:str|Path,
                                 charge:int|None=None,
                                 spin:int|None=None,
                                 step:int|None=None): 
    suffix = Path(filepath).suffix
    if suffix in GAUSSIAN_IN_SUFFIXES: 
        return info_from_gau_input(filepath)
    if suffix in GAUSSIAN_OUT_SUFFIXES and step is None:
        return info_from_gau_output(filepath)
    elif suffix in GAUSSIAN_OUT_SUFFIXES:
        return info_from_gau_output(filepath,step)
    if suffix == '.xyz': 
        return Geometry.from_xyz(filepath), charge, spin
    raise NotImplementedError(f'files with suffix "{suffix}" cannot be interpreted')

# Parser and Main Definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Input/Output Files',nargs='+')
parser.add_argument('-l','--listfile',
                    action='store_true',default=False,
                    dest='is_listfile',
                    help="""When enabled instead of considering the files 
                    provided as the gaussian output files considers the file 
                    provided as a list of gaussian output files""",)
group_marker = parser.add_mutually_exclusive_group()
group_marker.add_argument('-m','--marker',
                        default=DEFAULT_MARKER,
                        help=f"""Text added to the filename to differentiate 
                        the original file from the newly created one.
                        For example, myfile{GAUSSIAN_INPUT_SUFFIX} may become 
                        myfile_marker{GAUSSIAN_INPUT_SUFFIX}""")
group_marker.add_argument('--no-marker',
                        action='store_true',
                        default=False,
                        dest='no_marker',
                        help="The file stems are kept")
parser.add_argument('-o','--outdir',
                    default='',
                    help=""" Where to create the new files, defaults to the 
                    current directory""")
parser.add_argument('--step',
                    default=None,
                    type=int,
                    help=""" Will attempt to access the ith optimization step of
                    a gaussian output file to extract its geometry on all files 
                    provided. 'initial geometry'='1'""")
parser.add_argument('-H','--header',
                    default=None,
                    help="""Header File that contains the queue, memory as well 
                    as the gaussian calculation instructions. The output will 
                    start at the charge-spin line """)
parser.add_argument('-T','--tail',
                    default=None,
                    help="""Tail File that contains the extra options, such as 
                    pseudopotentials, basis sets """)
parser.add_argument('--charge',
                    default=DEFAULT_CHARGE,
                    type=int,
                    help="""Net charge of the whole system""")
parser.add_argument('--spin',
                    default=DEFAULT_SPIN,
                    type=int,
                    help="""spin of the system""")
parser.add_argument('--suffix',
                    default=DEFAULT_SUFFIX,
                    help='Input suffix used for gaussian files, e.g. ".com"')

def main(files:list[str|Path],
         is_listfile:bool,
         marker:str,
         outdir:Path|str,
         header:Path|str,
         tail:Path|str,
         suffix:str,
         charge:int=DEFAULT_CHARGE,
         spin:int=DEFAULT_SPIN,
         step:None|int=None,
         no_marker:bool=False,
         ):

    inputfiles = select_input_files(files,is_listfile)

    if no_marker:
        marker = ''

    outdir = Path(outdir)
    header = prepare_header(header)
    tail = prepare_tail(tail)
    suffix = prepare_suffix(suffix)

    template = f'{header}\n\n{{title}}\n\n{{charge}} {{spin}}\n{{coords}}\n\n{tail}\n\n\n'

    for ifile in inputfiles:
        print(ifile)
        infilepath = Path(ifile)
        stem = infilepath.stem
        if marker:
            ofile = outdir/f'{stem}_{marker}{suffix}'
        else:
            ofile = outdir/f'{stem}{suffix}'
        geom,charge,spin = extract_geom_spin_and_charge(infilepath,
                                                        charge=charge,
                                                        spin=spin,
                                                        step=step)
        with open(ofile,'w') as F:
            txt = template.format(title=f'{stem}_{marker}',
                                  charge=charge,
                                  spin=spin,
                                  coords=str(geom))
            F.write(txt)
