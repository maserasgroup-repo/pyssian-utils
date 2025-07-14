"""
Takes a gaussian output file and constructs 2 gaussian input files by 
distorting the last geometry of the provided file along the first imaginary 
frequency and using as template the .com file with the same name as the provided
output file. This approach is sometimes termed as "poorman's irc", but in no 
case it substitutes a proper IRC calculation.
"""
import argparse
from pathlib import Path
from typing import Tuple

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry, DirectoryTree

import numpy as np

from .initialize import check_initialization

GAUSSIAN_INPUT_SUFFIX = '.com'
GAUSSIAN_OUTPUT_SUFFIX = '.log'

class NotFoundError(RuntimeError):
    pass

def prepare_filepaths(filepaths:list[str|Path],
                      outdir:str|Path|None,
                      in_suffix:str,
                      out_suffix:str,
                      is_folder:bool,
                      is_listfile:bool,
                      marker:str|None,
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
        previously existing '.com' files. geometries the '.log' files provided
        by the user and newfiles the '.com' files that are to be created.

    """


    # Check the compatibility of the arguments, otherwise raise an error
    if is_inplace and no_marker and not do_overwrite:
        raise ValueError("""Using the --inplace with --no-marker will replace
                the previously existing input files. To continue please re-run
                the command but add the flag '--overwrite' (or '-ow').""")

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
    marker = select_marker(marker, no_marker)

    if marker:
        newfiles_f,newfiles_r = newfiles
        newfiles_f = [p.with_stem(f'{p.stem}_{marker}') for p in newfiles_f]
        newfiles_r = [p.with_stem(f'{p.stem}_{marker}') for p in newfiles_r]
        newfiles = newfiles_f,newfiles_r

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
    
    newfiles_f = [p.with_stem(f'{p.stem}_f{p.suffix}') for p in newfiles]
    newfiles_r = [p.with_stem(f'{p.stem}_r{p.suffix}') for p in newfiles]
    
    return templates, geometries, (newfiles_f,newfiles_r)
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
    
    newfiles_f = [p.with_stem(f'{p.stem}_f{p.suffix}') for p in newfiles]
    newfiles_r = [p.with_stem(f'{p.stem}_r{p.suffix}') for p in newfiles]

    return templates, geometries, (newfiles_f,newfiles_r)

def select_marker(marker:str|None,
                  no_marker:bool=False):
    """
    This function encapsulates all the logic related to the selection of the
    marker.
    """
    # Logic to handle the marker selection
    if  no_marker:
        marker = ''
    elif marker is None:
        marker = 'new'

    return marker
def select_suffix(in_suffix:str|None,out_suffix:str|None) -> tuple[str]: 
    """
    Ensures proper formatting of the suffixes used for gaussian inputs and 
    outputs and changes the values of the global variables GAUSSIAN_INPUT_SUFFIX,
    GAUSSIAN_OUTPUT_SUFFIX accordingly
    """
    if in_suffix is not None and in_suffix.startswith('.'):
        in_suffix = in_suffix.rstrip()
    elif in_suffix is None: 
        in_suffix = GAUSSIAN_INPUT_SUFFIX
    else:
        in_suffix = in_suffix

    if out_suffix is not None and out_suffix.startswith('.'):
        out_suffix = out_suffix.rstrip()
    elif out_suffix is None: 
        out_suffix = GAUSSIAN_OUTPUT_SUFFIX
    else:
        out_suffix = out_suffix
    return in_suffix,out_suffix

def apply_distortions(gau_log:str|Path,factor:float=0.13) -> Tuple[Geometry,Geometry]:

    with GaussianOutFile(gau_log) as GOF:
        GOF.read()
        l716 = GOF.get_links(716)[-1]
        l202 = GOF.get_links(202)[-1]

    geom_f = Geometry.from_L202(l202)
    geom_r = Geometry.from_L202(l202)
    disp_matrix = np.array(l716.freq_displacements[0].xyz)

    geom_f.coordinates = (np.array(geom_f.coordinates) + factor*disp_matrix).tolist()
    geom_r.coordinates = (np.array(geom_r.coordinates) - factor*disp_matrix).tolist()
    
    return geom_f, geom_r

# Parser and Main definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Output Files',nargs='+')
group_input = parser.add_mutually_exclusive_group()
group_input.add_argument('-l','--listfile',
                            dest='is_listfile',
                            action='store_true',default=False,
                            help="""When enabled instead of considering the 
                            files provided as the gaussian output files 
                            considers the file provided as a list of gaussian
                            output files""")
group_input.add_argument('-r','--folder',
                            dest='is_folder',
                            action='store_true',default=False,
                            help="""Takes the folder and its subfolder 
                            hierarchy and creates a new folder with the same 
                            subfolder structure. Finds all the .log, attempts 
                            to find their companion .com files and creates the 
                            new inputs in their equivalent locations in the new
                            folder tree structure.""")
group_marker = parser.add_mutually_exclusive_group()
group_marker.add_argument('-m','--marker',
                        default='new',
                        help="""Text added to the filename to differentiate 
                        the original file from the newly created one.
                        For example, myfile.com may become myfile_marker.com""")
group_marker.add_argument('--no-marker',
                        dest='no_marker',
                        action='store_true',default=False,
                        help="The file stems are kept")
group_output = parser.add_mutually_exclusive_group()
group_output.add_argument('-o','--outdir',
                            default=None,
                            help="""Where to create the new files, defaults 
                            to the current directory""")
group_output.add_argument('--inplace',
                            dest='is_inplace',
                            action='store_true',default=False,
                            help="""Creates the new files in the same 
                            locations as the files provided by the user""")
parser.add_argument('-ow','--overwrite',
                    dest='do_overwrite',
                    action='store_true',default=False,
                    help="""When creating the new files if a file with the 
                    same name exists overwrites its contents. (The default 
                    behaviour is to raise an error to notify the user before
                    overwriting).""")
parser.add_argument('--suffix',
                    default=(None,None),nargs=2,
                    help="""Input and output suffix used for gaussian files""") 

def main(
         files:list[str|Path],
         outdir:str|Path|None=None,
         suffix:tuple[str|None]=(None,None),
         is_folder:bool=False,
         is_listfile:bool=False,
         marker:str|None=None,
         no_marker:bool=False,
         is_inplace:bool=False,
         do_overwrite:bool=False,
         ):
    
    check_initialization()

    # Ensure proper suffixes
    in_suffix,out_suffix = select_suffix(*suffix)

    templates,geometries,newfiles = prepare_filepaths(files,
                                                      outdir,
                                                      in_suffix,
                                                      out_suffix,
                                                      is_folder,
                                                      is_listfile,
                                                      marker,
                                                      no_marker,
                                                      is_inplace,
                                                      do_overwrite)

    for tfile,ifile,(ofile_f,ofile_r) in zip(templates,geometries,newfiles):
        print(f'Processing File {ifile}')
        # Check for file existence
        if not tfile.exists() and ifile.exists():
            print(f"{tfile} not found for {ifile} proceeding with the next file")
            continue
        elif tfile.exists() and ifile.exists():
            pass
        else:
            print(f"{ifile} not found. Skipping to the next one")

        output_exists = ofile_r.exists() or ofile_f.exists()
        
        if not do_overwrite and output_exists:
            raise RuntimeError(f"""Attempted to overwrite {ofile_f} and {ofile_r}
                               when '-ow' was not specified """)

        with GaussianInFile(tfile) as GIF:
            GIF.read()

        # Handle removal of opt, freq and scan keywords
        _ = GIF.pop_kwd('opt')
        _ = GIF.pop_kwd('freq')
        _ = GIF.pop_kwd('scan')

        # Ensure optimizations to minima
        GIF.add_kwd('opt')
        GIF.add_kwd('freq')

        geom_f, geom_r = apply_distortions(ifile)

        GIF.title = ofile_f.stem
        GIF.geometry = geom_f
        GIF.write(ofile_f)

        GIF.title = ofile_r.stem
        GIF.geometry = geom_r
        GIF.write(ofile_r)

