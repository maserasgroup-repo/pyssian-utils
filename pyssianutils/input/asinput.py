__doc__ = """
Takes a gaussian output file and constructs a gaussian input file with its last
geometry using its input file as template which is guessed as the {in_suffix} 
file with the same name as the provided output file.
"""
import argparse
from pathlib import Path

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry

from ..initialize import load_app_defaults
from ..utils import DirectoryTree

# Load app defaults
DEFAULTS = load_app_defaults()
GAUSSIAN_INPUT_SUFFIX = DEFAULTS['common']['in_suffix']
GAUSSIAN_OUTPUT_SUFFIX = DEFAULTS['common']['out_suffix']
DEFAULT_SUFFIX = (GAUSSIAN_INPUT_SUFFIX,GAUSSIAN_OUTPUT_SUFFIX)
DEFAULT_MARKER = DEFAULTS['common']['default_marker']
DEFAULT_SP_MARKER = DEFAULTS['input.asinput']['sp_marker']
DEFAULT_SOFTWARE = DEFAULTS['input.asinput']['software']
DEFAULT_SCRIPTNAME = DEFAULTS['input.asinput']['script_name']

class NotFoundError(RuntimeError):
    pass

def prepare_filepaths(
                      filepaths:list[str|Path],
                      outdir:str|Path|None,
                      in_suffix:str,
                      out_suffix:str,
                      is_folder:bool,
                      is_listfile:bool,
                      marker:str|None,
                      as_SP:bool=False,
                      no_marker:bool=False,
                      is_inplace:bool=False,
                      do_overwrite:bool=False,
                      ) -> tuple[list[Path]]:
    """
    This function encapsulates all the logic related to the generation of the
    final paths to the files, directory and subdirectory creation as well as
    paths to the template files.

    Parameters
    ----------
    folder : Namespace
        Output of the ArgumentParser.parse_args function

    Returns
    -------
    templates,geometries,newfiles
        A tuple of three lists of the same size. Templates represents the
        previously existing '.in' files. geometries the '.out' files provided
        by the user and newfiles the '.in' files that are to be created.

    """


    # Check the compatibility of the arguments, otherwise raise an error
    if is_inplace and no_marker and not do_overwrite:
        raise ValueError("Using the --inplace with --no-marker will replace "
                "the previously existing input files. To continue please re-run "
                "the command but add the flag '--overwrite' (or '-ow').")

    # Prepare folder structure
    if is_folder:
        folder = filepaths[0]
        if not is_inplace:
            outdir = Path.cwd()
        templates,geometries,newfiles = prepare_filepaths_folder(folder,
                                                                 outdir,
                                                                 in_suffix,
                                                                 out_suffix,
                                                                 )
    else:
        templates,geometries,newfiles = prepare_filepaths_nofolder(filepaths,
                                                                   outdir,
                                                                   in_suffix,
                                                                   is_inplace,
                                                                   is_listfile,
                                                                   )
    # Rename the newfiles to ensure the include (or not) the marker
    marker = select_marker(marker,
                           as_SP,
                           no_marker)

    if marker: 
        newfiles = [p.with_stem(f'{p.stem}_{marker}') for p in newfiles]

    return templates, geometries, newfiles
def prepare_filepaths_folder(folder:Path|str,
                             odir:str|Path|None,
                             in_suffix:str,
                             out_suffix:str) -> tuple[list[Path]]:
    """
    This function encapsulates the logic of the path generation when the
    --folder flag is enabled.
    """
    dir = DirectoryTree(folder,in_suffix,out_suffix)
    if odir is not None:
        odir = Path(odir)
        dir.set_newroot(odir)
        # create output folders
        print(f"Folders Created at '{odir}'")
        dir.create_folders()
    
    # Find the gaussian output files
    geometries = list(dir.outfiles)
    templates = [path.with_suffix(in_suffix) for path in geometries]
    newfiles = [dir.newpath(path).with_suffix(in_suffix) for path in geometries]

    return templates, geometries, newfiles
def prepare_filepaths_nofolder(files:list[str|Path],
                               odir:str|Path|None,
                               in_suffix:str,
                               is_inplace:bool=False,
                               is_listfile:bool=False,
                               ) -> tuple[list[Path]]:
    """
    This function encapsulates the logic of the path generation when the
    --folder flag is not enabled.
    """
    if not is_inplace:
        if odir is None:
            odir = Path.cwd()
        else:
            odir = Path(odir)
        odir.mkdir(parents=False,exist_ok=True)

    if is_listfile:
        with open(Path(files[0]),'r') as F:
            geometries = [Path(line.strip()) for line in F if line.strip()]
    else:
        geometries = [Path(f) for f in files]
    
    templates = [path.with_suffix(in_suffix) for path in geometries]

    if is_inplace:
        newfiles = [path for path in templates]
    else:
        newfiles = [odir/(g.with_suffix(in_suffix).name) for g in geometries]

    return templates, geometries, newfiles
def select_marker(marker:str|None,
                  as_SP:bool=False,
                  no_marker:bool=False):
    """
    This function encapsulates all the logic related to the selection of the
    marker.
    """
    # Logic to handle the marker selection
    if  no_marker:
        marker = ''
    elif marker is None:
        if as_SP:
            marker = DEFAULT_SP_MARKER
        else:
            marker = DEFAULT_MARKER

    return marker
def prepare_suffix(suffix:str) -> str: 
    """
    Ensures proper formatting of the suffixes used for gaussian inputs
    """
    if suffix.startswith('.'):
        suffix = suffix.rstrip()
    else: 
        suffix = f'.{suffix.strip()}'

    return suffix
def prepare_tail(filepath:Path|None) -> list[str]|None:
    if filepath is None: 
        return None
    
    with open(filepath,'r') as F:
        aux = [line.strip() for line in F]
    
    while len(aux)>=1 and not aux[0]:
        _ = aux.pop(0)
    
    while len(aux)>=1 and not aux[-1]:
        _ = aux.pop(-1)
    
    return aux

# Parser and Main Definition
__doc__ = __doc__.format(in_suffix=GAUSSIAN_INPUT_SUFFIX)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Output Files',nargs='+')
group_input = parser.add_mutually_exclusive_group()
group_input.add_argument('-l','--listfile',
                         dest='is_listfile',
                         action='store_true',default=False,
                         help="When enabled instead of considering the "
                         "files provided as the gaussian output files "
                         "considers the file provided as a list of gaussian "
                         "output files")
group_input.add_argument('-r','--folder',
                         dest='is_folder',
                         action='store_true',default=False,
                         help="Takes the folder and its subfolder "
                         "hierarchy and creates a new folder with the same "
                         "subfolder structure. Finds all the "
                         f"{GAUSSIAN_OUTPUT_SUFFIX}, attempts to find their "
                         f"companion {GAUSSIAN_INPUT_SUFFIX} files and creates the "
                         "new inputs in their equivalent locations in the new"
                         "folder tree structure.")
group_marker = parser.add_mutually_exclusive_group()
group_marker.add_argument('-m','--marker',
                          default=None,
                          help="Text added to the filename to differentiate "
                          "the original file from the newly created one. "
                          f"For example, myfile{GAUSSIAN_INPUT_SUFFIX} may become "
                          f"myfile_marker{GAUSSIAN_INPUT_SUFFIX}")
group_marker.add_argument('--no-marker',
                          dest='no_marker',
                          action='store_true',default=False,
                          help="The file stems are kept")
group_output = parser.add_mutually_exclusive_group()
group_output.add_argument('-o','--outdir',
                          default=None,
                          help="Where to create the new files, defaults "
                          "to the current directory")
group_output.add_argument('--inplace',
                          dest='is_inplace',
                          action='store_true',default=False,
                          help="Creates the new files in the same "
                          "locations as the files provided by the user")
parser.add_argument('-ow','--overwrite',
                    dest='do_overwrite',
                    action='store_true',default=False,
                    help="When creating the new files if a file with the "
                    "same name exists overwrites its contents. (The default "
                    "behaviour is to raise an error to notify the user before"
                    "overwriting).")
parser.add_argument('-t','--tail',
                    default=None,
                    help="Tail File that contains the extra options, such "
                    "as pseudopotentials, basis sets")
parser.add_argument('--as-SP',
                    dest='as_SP',
                    action='store_true', default=False,
                    help=f"Removes the freq, opt and scan keyword if "
                    "those existed in the previously existing inputs and "
                    f"changes the default marker to {DEFAULT_SP_MARKER} ")
parser.add_argument('--method',
                    default=None,
                    help="New method/functional to use. Originally "
                    "this option is thought to run DFT benchmarks it is not "
                    "guaranteed a working input for CCSDT or ONIOM.")
parser.add_argument('--basis',
                    default=None,
                    help="New basis to use if it was specified in the command "
                    "line. For these purposes 'gen' and 'genecp' also count "
                    "as 'basis' ")
parser.add_argument('--solvent',
                    default=None,
                    help="New solvent to use in the calculation written as "
                    "it would be written in Gaussian. ('vacuum'/'gas' will "
                    "remove the scrf keywords if they were in the previous "
                    "input files)")
parser.add_argument('--smodel',
                    dest='solvation_model',
                    default=None, choices=['smd','pcm',None], 
                    help="Solvent model. The scrf keyword will only be "
                    "included if the --solvent flag is enabled. "
                    "(Defaults to None which implies that no change to the "
                    "original inputs smodel will be done) ")
parser.add_argument('--add-text',
                    dest='add_text',
                    default=None, 
                    help='Attempts to add literally the text provided to '
                    'the command line. Recommended: '
                    '"keyword=(value1,keyword2=value2)" ')
parser.add_argument('--suffixes',
                    default=DEFAULT_SUFFIX,nargs=2,
                    help="Input and output suffix used for gaussian files")

def main(
         files:list[str|Path],
         outdir:str|Path|None=None,
         suffixes:tuple[str]=DEFAULT_SUFFIX,
         method:str|None=None,
         basis:str|None=None,
         solvent:str|None=None,
         solvation_model:str|None=None,
         add_text:str|None=None,
         is_folder:bool=False,
         is_listfile:bool=False,
         marker:str|None=None, # It should default to None, app defaults are later
         as_SP:bool=False,
         no_marker:bool=False,
         is_inplace:bool=False,
         do_overwrite:bool=False,
         tail:Path|str|None=None,
         ):

    # Prepare Tail
    tail = prepare_tail(tail)
    
    # Ensure proper suffixes
    in_suffix,out_suffix = map(prepare_suffix,suffixes)

    templates,geometries,newfiles = prepare_filepaths(files,
                                                      outdir,
                                                      in_suffix,
                                                      out_suffix,
                                                      is_folder,
                                                      is_listfile,
                                                      marker,
                                                      as_SP,
                                                      no_marker,
                                                      is_inplace,
                                                      do_overwrite)

    final_files = []
    for tfile,ifile,ofile in zip(templates,geometries,newfiles):
        print(f'Processing file {ifile}')

        # Check for file existence
        
        if not tfile.exists() and ifile.exists():
            print(f"{tfile} not found for {ifile} proceeding with the next file")
            continue
        elif tfile.exists() and ifile.exists():
            pass
        else:
            print(f"{ofile} not found. Skipping to the next one")

        if not do_overwrite and (tfile == ofile or ofile.exists()):
            raise RuntimeError(f"""Attempted to overwrite {ofile} when '-ow' was
                                not specified. Please check your files or file a
                               bug issue""")

        with GaussianInFile(tfile) as gif:
            gif.read()

        with GaussianOutFile(ifile,[101,202]) as gof:
            gof.read()
            l101 = gof.get_links(101)[0]
            l202 = gof.get_links(202)[-1]
            geom = Geometry.from_L202(l202)

        # Overwrite the corresponding values of attributes of the GIF
        gif.charge = l101.charge
        gif.spin = l101.spin
        gif.title = ofile.stem
        gif.geometry = geom

        # Handle the additions to the tail and commandlipathne
        if tail is not None:
            gif.parse_tail(tail)

        if add_text is not None:
            # This is fairly dirty but good enough for now
            gif.commandline[add_text] = []
        
        # Overwrite the method if the user specified so
        if method is not None:
            gif.method = method
        
        # Overwrite the basis if the user specified so
        if basis is not None:
            gif.basis = basis

        # Handle solvation substitutions
        if solvent is not None:
            if solvent.lower() in ['vacuum','gas']:
                gif.commandline.pop('scrf')
                # With the newest pyssian it should be 
                # gif.solvent = 'gas'
            else:
                gif.solvent = solvent
            
        if solvation_model is not None:
            gif.solvation_model = solvation_model
        
        # Handle removal of opt, freq and scan keywords
        if as_SP:
            keys = ['opt','freq','scan']
            for key in keys:
                _ = gif.pop_kwd(key)

        gif.write(ofile)
        final_files.append(ofile)