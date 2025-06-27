#!/bin/usr/env python3

"""
Takes a gaussian output file and constructs a 2 gaussian input files by 
distorting the last geometry of the provided file along the first imaginary 
frequency and using as template the .com file with the same name as the provided
output file.
"""

import os
import argparse
from collections import namedtuple
from itertools import groupby
from pathlib import Path
from typing import Tuple

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry, DirectoryTree

import numpy as np

__version__ = '0.0.0'

GAUSSIAN_INPUT_SUFFIX = '.com'
GAUSSIAN_OUTPUT_SUFFIX = '.log'

class NotFoundError(RuntimeError):
    pass

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('Files',help='Gaussian Output Files',nargs='+')
group_input = parser.add_mutually_exclusive_group()
group_input.add_argument('-L','--ListFile',help="""When enabled instead of
                    considering the files provided as the gaussian output files
                    considers the file provided as a list of gaussian output
                    files""",action='store_true',default=False)
group_input.add_argument('-r','--folder',help="""Takes the folder and its
                    subfolder hierarchy and creates a new folder with the same
                    subfolder structure. Finds all the .out, attempts to find
                    their companion .in files and creates the new inputs in
                    their equivalent locations in the new folder tree structure.
                    """,action='store_true',default=False)
group_marker = parser.add_mutually_exclusive_group()
group_marker.add_argument('-m','--marker',help="""Text added to the filename to
                    differentiate the original .out file from the newly created
                    one. """,default=None)
group_marker.add_argument('--no-marker',help="""Files will be created with the
                    same file name as the provided files but with the '.in'
                    extension""", action='store_true',default=False,
                    dest='no_marker')
group_output = parser.add_mutually_exclusive_group()
group_output.add_argument('-O','--OutDir',help="""Where to create the new files,
                    defaults to the current directory""",default='')
group_output.add_argument('--inplace',help="""Creates the new files in the same
                    locations as the files provided by the user""",
                    action='store_true',default=False)
parser.add_argument('-ow','--overwrite',help="""When creating the new files if a
                    file with the same name exists overwrites its contents. (The
                    default behaviour is to raise an error to notify the user
                    before overwriting).""",action='store_true',default=False)
parser.add_argument('--version',version=f'script version {__version__}',
                    action='version')
parser.add_argument('--suffix',default=None,nargs=2,help="""Input and output 
                    suffix used for gaussian files""") 

def prepare_filepaths(args):
    """
    This function encapsulates all the logic related to the generation of the
    final paths to the files, directory and subdirectory creation as well as
    paths to the template files.

    Parameters
    ----------
    args : Namespace
        Output of the ArgumentParser.parse_args function

    Returns
    -------
    templates,geometries,newfiles
        A tuple of three lists of the same size. Templates represents the
        previously existing '.in' files. geometries the '.out' files provided
        by the user and newfiles the '.in' files that are to be created.

    """
    # Prepare folder structure
    if args.folder:
        templates,geometries,newfiles = prepare_filepaths_folder(args)
    else:
        templates,geometries,newfiles = prepare_filepaths_nofolder(args)
    newfiles = list(zip(*newfiles))
    return templates, geometries, newfiles
def prepare_filepaths_folder(args):
    """
    This function encapsulates the logic of the path generation when the
    --folder flag is enabled.
    """
    marker = select_marker(args)
    dir = DirectoryTree(args.Files[0])
    if args.OutDir:
        OutDir = Path(args.OutDir)
        dir.set_newroot(OutDir)
        # create output folders
        print(f"Folders Created at '{OutDir}'")
        dir.create_folders()
    # Find the gaussian output files
    geometries = list(dir.outfiles)
    templates = [path.parent.joinpath(path.stem + GAUSSIAN_INPUT_SUFFIX) for path in geometries]
    newfiles = [dir.newpath(path) for path in geometries]
    if marker:
        namef = f'{{0.stem}}_f_{marker}{GAUSSIAN_INPUT_SUFFIX}'.format
        namer = f'{{0.stem}}_r_{marker}{GAUSSIAN_INPUT_SUFFIX}'.format
    else:
        namef = f'{{0.stem}}_f{GAUSSIAN_INPUT_SUFFIX}'.format
        namer = f'{{0.stem}}_r{GAUSSIAN_INPUT_SUFFIX}'.format
    newfiles_f = [path.parent.joinpath(namef(path)) for path in newfiles]
    newfiles_r = [path.parent.joinpath(namer(path)) for path in newfiles]
    return templates, geometries, (newfiles_f,newfiles_r)
def prepare_filepaths_nofolder(args):
    """
    This function encapsulates the logic of the path generation when the
    --folder flag is not enabled.
    """
    marker = select_marker(args)
    if not args.inplace:
        if args.OutDir is None:
            OutDir = Path(os.getcwd())
        else:
            OutDir = Path(args.OutDir)
        OutDir.mkdir(parents=False,exist_ok=True)

    if args.ListFile:
        with open(Path(args.Files[0]),'r') as F:
            geometries = [Path(line.strip()) for line in F if line.strip()]
    else:
        geometries = [Path(File) for File in args.Files]
    templates = [path.parent.joinpath(path.stem + GAUSSIAN_INPUT_SUFFIX) for path in geometries]
    if args.inplace:
        newfiles = [path for path in templates]
    else:
        newfiles = [OutDir.joinpath(path.stem + GAUSSIAN_INPUT_SUFFIX) for path in geometries]
    # Add the marker to the name of the file
    if marker:
        namef = f'{{0.stem}}_f_{marker}{GAUSSIAN_INPUT_SUFFIX}'.format
        namer = f'{{0.stem}}_r_{marker}{GAUSSIAN_INPUT_SUFFIX}'.format
    else:
        namef = f'{{0.stem}}_f{GAUSSIAN_INPUT_SUFFIX}'.format
        namer = f'{{0.stem}}_r{GAUSSIAN_INPUT_SUFFIX}'.format
    newfiles_f = [path.parent.joinpath(namef(path)) for path in newfiles]
    newfiles_r = [path.parent.joinpath(namer(path)) for path in newfiles]
    return templates, geometries, (newfiles_f,newfiles_r)

def select_marker(args):
    """
    This function encapsulates all the logic related to the selection of the
    marker.
    """
    # Logic to handle the marker selection
    if  args.no_marker:
        marker = ''
    elif args.marker is None:
        if args.as_SP:
            marker = 'SP'
        else:
            marker = 'new'
    else:
        marker = args.marker

    #Handle the Overwriting notification
    if args.inplace and args.no_marker and not args.overwrite:
        raise ValueError("""Using the --inplace with --no-marker will replace
                the previously existing '.in' files. To continue please re-run
                the command but add the flag '--overwrite' (or '-ow').""")
    return marker
def select_suffix(args): 
    """
    Ensures proper formatting of the suffixes used for gaussian inputs and 
    outputs and changes the values of the global variables GAUSSIAN_INPUT_SUFFIX,
    GAUSSIAN_OUTPUT_SUFFIX accordingly
    """
    global GAUSSIAN_INPUT_SUFFIX
    global GAUSSIAN_OUTPUT_SUFFIX
    if args.suffix is None:
        return
    in_suffix, out_suffix = args.suffix
    if in_suffix.startswith('.'): 
        GAUSSIAN_INPUT_SUFFIX = in_suffix.rstrip()
    if out_suffix.startswith('.'): 
        GAUSSIAN_OUTPUT_SUFFIX = out_suffix.rstrip()

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

if __name__ == '__main__':
    args = parser.parse_args()

    # Ensure proper suffixes
    select_suffix(args)

    templates,geometries,newfiles = prepare_filepaths(args)

    for tfile,ifile,(ofile_f,ofile_r) in zip(templates,geometries,newfiles):
        print(f'Processing File {ifile}')
        # Check for file existence
        if not tfile.exists() and ifile.exists():
            print(f"""{tfile} not found for {ifile} proceeding with the next
                    file""")
            continue
        elif tfile.exists() and ifile.exists():
            pass
        else:
            print(f"""{ifile} not found. Skipping to the next one""")
        output_exists = ofile_r.exists() or ofile_f.exists()
        if not args.overwrite and output_exists:
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

