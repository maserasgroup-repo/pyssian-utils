#!/bin/usr/env python3

"""
Takes a gaussian output file and constructs a gaussian input file with its last
geometry either using a provided input file as template or using a .in file with
the same name as the provided output file.
"""

import os
import argparse
from collections import namedtuple
from itertools import groupby
from pathlib import Path

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry, DirectoryTree

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
parser.add_argument('-T','--Tail',help="""Tail File that contains the extra
                    options, such as pseudopotentials, basis sets """,
                    default=None)
parser.add_argument('--as-SP',help="""Removes the freq, opt and scan keyword if
                    those existed in the previously existing inputs and changes
                    the default marker to 'SP' """,action='store_true',
                    default=False,dest='as_SP')
parser.add_argument('--method',help="""New method/functional to use. Originally
                    this option is thought to run DFT benchmarks it is not
                    guaranteed a working input for CCSDT or ONIOM.""",
                    default=None)
parser.add_argument('--solvent',help="""New solvent to use in the calculation
                    written as it would be written in Gaussian. ('vacuum' will
                    remove the scrf keywords if they were in the previous input
                    files)""",default=None)
parser.add_argument('--smodel',default=None,choices=['smd','pcm',None], help="""
                    Solvent model. The scrf keyword will only be included if the
                    --solvent flag is enabled. (Defaults to None which implies
                    that no change to the original inputs smodel will be done)
                    """)
parser.add_argument('--add-text', default=None, help="""Attempts to add
                    literally the text provided to the command line.
                    Recommended: "keyword=(value1,keyword2=value2)" """,
                    dest='add_text')
parser.add_argument('--no-submit',default=False,action='store_true',
                    help="""Do not create a SubmitScript.sh File in the current
                    directory""",dest='no_submit')
parser.add_argument('--software',choices=['g09','g16'],help="""Version of
                    gaussian to which the calculations will be sent.
                    'qs {gxx}.queue.q file.in' (Default: g09)""",default='g09')
parser.add_argument('--version',version=f'script version {__version__}',
                    action='version')
parser.add_argument('--suffix',default=None,nargs=2,help="""Input and output 
                    suffix used for gaussian files""") 

Queue = namedtuple('Queue','nprocesors memory'.split())
QUEUES = {4:Queue(4,8),8:Queue(8,24),
          12:Queue(12,24),
          16:Queue(16,32),
          20:Queue(20,48),
          24:Queue(24,128),28:Queue(28,128),
          36:Queue(36,192),'q4':Queue('q4',4)}
def submitline(File,software):
    """
    Inspects the file, selects the queue and returns the string that corresponds
    to the submission of the calculation to a queue system.

    Parameters
    ----------
    File : Path
        pathlib.Path pointing towards the input file to submit.
    software : str
        either 'g09' or 'g16'

    Returns
    -------
    str

    """
    command = 'qs {0}.c{1.nprocesors}m{1.memory} {2};'
    with open(File,'r') as F:
        Text = [line.strip() for line in F]
    # Find nproc
    for line in Text:
        if 'nproc' in line:
            nprocs = int(line.strip().split("=")[-1])
            break
    else:
        raise NotFoundError(f'nproc not found in {File}')
    # Find Mem
    for line in Text:
        if '%mem' in line:
            memory = int(line.strip().split("=")[-1][:-2])
            if line.strip().lower().endswith('gb'):
                memory *= 1024
            break
    if nprocs == 4 and software == 'g16':
        queue = QUEUES['q4']
    elif nprocs == 4 and memory < 4000:
        queue = QUEUES['q4']
    else:
        queue = QUEUES[nprocs]
    txt = command.format(software,queue,File.name)
    return txt

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
    return templates, geometries, newfiles
def prepare_filepaths_folder(args):
    """
    This function encapsulates the logic of the path generation when the
    --folder flag is enabled.
    """
    marker = select_marker(args)
    dir = DirectoryTree(args.Files[0],GAUSSIAN_INPUT_SUFFIX,GAUSSIAN_OUTPUT_SUFFIX)
    if args.OutDir:
        OutDir = Path(args.OutDir)
        dir.set_newroot(OutDir)
        # create output folders
        print(f"Folders Created at '{OutDir}'")
        dir.create_folders()
    # Find the gaussian output files
    geometries = list(dir.outfiles)
    templates = [path.with_suffix(GAUSSIAN_INPUT_SUFFIX) for path in geometries]
    newfiles = [dir.newpath(path) for path in geometries]
    if marker:
        newname = f'{{0.stem}}_{marker}{GAUSSIAN_INPUT_SUFFIX}'.format
    else:
        newname = f'{{0.stem}}{GAUSSIAN_INPUT_SUFFIX}'.format
    newfiles = [path.parent.joinpath(newname(path)) for path in newfiles]
    return templates, geometries, newfiles
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
        newname = f'{{0.stem}}_{marker}{GAUSSIAN_INPUT_SUFFIX}'.format
    else:
        newname = f'{{0.stem}}{GAUSSIAN_INPUT_SUFFIX}'.format
    newfiles = [path.parent.joinpath(newname(path)) for path in newfiles]
    return templates, geometries, newfiles

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

if __name__ == '__main__':
    args = parser.parse_args()

    # Prepare Tail
    if args.Tail is None:
        Tail = None
    else:
        with open(os.path.abspath(args.Tail),'r') as F:
            Tail = [line.strip() for line in F]
    
    # Ensure proper suffixes
    select_suffix(args)

    templates,geometries,newfiles = prepare_filepaths(args)
    files4submit = []

    for TFile,IFile,OFile in zip(templates,geometries,newfiles):
        print(f'Processing File {IFile}')
        # Check for file existence
        if not TFile.exists() and IFile.exists():
            print(f"""{TFile} not found for {IFile} proceeding with the next
                    file""")
            continue
        elif TFile.exists() and IFile.exists():
            pass
        else:
            print(f"""{OFile} not found. Skipping to the next one""")
        if not args.overwrite and (TFile == OFile or OFile.exists()):
            raise RuntimeError(f"""Attempted to overwrite {OFile} when '-ow' was
                                not specified """)

        with GaussianInFile(TFile) as GIF:
            GIF.read()
        with GaussianOutFile(IFile,[101,202]) as GOF:
            GOF.read()
            l101 = GOF.get_links(101)[0]
            l202 = GOF.get_links(202)[-1]
            geom = Geometry.from_L202(l202)

        # Overwrite the corresponding values of attributes of the GIF
        GIF.charge = l101.charge
        GIF.spin = l101.spin
        GIF.title = OFile.stem
        GIF.geometry = geom

        # Handle the additions to the tail and commandlipathne
        if Tail is not None:
            GIF.parse_tail(Tail)
        if args.add_text is not None:
            # This is fairly dirty but good enough for now
            GIF.commandline[args.add_text] = []
        # Overwrite the method if the user specified so
        if args.method is not None:
            GIF.method = args.method
        # Handle solvation substitutions
        if args.solvent is not None:
            if args.solvent.lower() == 'vacuum':
                GIF.commandline.pop('scrf')
            else:
                items = GIF.commandline.get('scrf',[])
                for i,item in enumerate(items):
                    if 'solvent' in item:
                        items.pop(i)
                        break
                items.append(f'solvent={args.solvent}')
                GIF.commandline['scrf'] = items
        if args.smodel is not None:
            items = GIF.commandline.get('scrf',[])
            for i,item in enumerate(items):
                if item in ['smd','pcm']:
                    items.pop(i)
                    break
            items.append(args.smodel)
            GIF.commandline['scrf'] = items
        # Handle removal of opt, freq and scan keywords
        if args.as_SP:
            keys = ['opt','freq','scan']
            for key in keys:
                _ = GIF.commandline.pop(key,None)

        GIF.write(OFile)
        files4submit.append((OFile.parent,OFile))
    if not args.no_submit:
        # Now create the submit script
        SubmitLines = [ '#!/bin/bash\n',
                        '# Automated Submit Script\n'
                        f'BASEDIR=$PWD;']
        files4submit.sort(key=lambda x: x[0])
        for folder,group in groupby(files4submit,key=lambda x: x[0]):
            SubmitLines.append(f'echo "moving to {folder}";')
            SubmitLines.append(f'cd {folder};')
            items = list(group)
            for item in items:
                SubmitLines.append(submitline(item[1],args.software))
            SubmitLines.append('cd ${BASEDIR};')
        SubmitLines.append('echo "Finished submiting calculations";')

        with open('SubmitScript.sh','w') as F:
            F.write('\n'.join(SubmitLines))
