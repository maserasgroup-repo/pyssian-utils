__doc__ = """
Checks all {in_suffix} files in the current directory or the provided folder to 
generate a {script_name} that properly sends them to their queues (Files with a 
matching {out_suffix} file are ignored as default). It checks in which queue 
they should go according to the values of 'nprocshared' and 'mem'. To use the 
generated script run in the cluster: 'chmod +x {script_name}; ./{script_name};' 
or 'bash {script_name}'
"""

import argparse
from pathlib import Path
from collections import namedtuple
from itertools import groupby

from pyssian.gaussianclasses import GaussianInFile

from ..initialize import load_app_defaults
from ..utils import DirectoryTree

# Load app defaults
DEFAULTS = load_app_defaults()
GAUSSIAN_INPUT_SUFFIX = DEFAULTS['common']['in_suffix']
GAUSSIAN_OUTPUT_SUFFIX = DEFAULTS['common']['out_suffix']
DEFAULT_SOFTWARE = DEFAULTS['submit.custom']['software']
DEFAULT_SCRIPT = DEFAULTS['submit.custom']['script_name']

Queue = namedtuple('Queue','nprocesors memory'.split())
QUEUES = dict() 
for k,v in DEFAULTS['submit.custom.queues'].items(): 
    if k == 'default':
        QUEUES['default'] = QUEUES[DEFAULTS['submit.custom.queues']['default']]
    else:
        # v is a tuple as a str
        v = tuple(map(int,v[1:-1].split(',')))
        QUEUES[k] = Queue(*v)

# Utility Functions and classes
class NotFoundError(RuntimeError):
    pass

def submitline(ifile:Path,
               software:str,
               ascomment:bool,
               norun:bool) -> str:
    """
    Inspects the file, selects the queue and returns the string that corresponds
    to the submission of the calculation to a queue system.

    Parameters
    ----------
    ifile : Path
        pathlib.Path pointing towards the input file to submit.
    software : str
        either 'g09' or 'g16'
    ascomment : bool
        If True, the line will start with a #
    norun : bool
        If True, after the queue a 0 will be added to allow submission without 
        running. This is HPC specific. 
    
    Returns
    -------
    str
        formatted line for the submission script
    """

    with GaussianInFile(ifile) as GIF: 
        GIF.read()
        nprocs = int(GIF.nprocs)
        mem = GIF.mem

    memory = int(mem[:-2])             # Assume 'xxxMB'
    if mem[-2:] == 'GB': 
        memory = memory*1024    # Translate to MB in case of GB
    
    if nprocs == 4 and software == 'g16':
        queue = QUEUES['q4']
    elif nprocs == 4 and memory < 4000:
        queue = QUEUES['q4']
    else:
        queue = QUEUES.get(str(nprocs),QUEUES['default'])
    
    line = f'{{}}qs {software}.c{queue.nprocesors}m{queue.memory} {{}} {ifile.name};'

    if norun and ascomment: line = line.format('#','0')
    elif norun:             line = line.format('' ,'0')
    elif ascomment:         line = line.format('#','' )
    else:                   line = line.format('' ,'' )

    return  line

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
def prepare_filepaths(folder:Path|str,
                      in_suffix:str,
                      out_suffix:str,
                      recursive:bool=False) -> tuple[list[Path]]:
    """
    This function encapsulates all the logic related to the generation of the
    final paths to the files, directory and subdirectory creation as well as
    paths to the template files.

    Parameters
    ----------
    folder : Path | str
        location of the input (and/or) output files
    in_suffix : str
        suffix used to identify input files, e.g. '.com'
    out_suffix : str
        suffix used to identify input files, e.g. '.log'
    recursive : bool, optional
        If enabled it will do a recursive search on all subfolders of the 
        provided folder, by default False

    Returns
    -------
    nomatch_inputs,matching_inputs
        A tuple of two lists of the same size. nomatch_inputs are input files 
        without an output file matching their name. matching_inputs are the 
        input files with an output file matching their name (typically implying 
        that the calculation for that input was previously submitted and finished).
    """
    # Prepare folder structure
    if recursive:
        dir = DirectoryTree(folder,in_suffix,out_suffix)
        outputs = list(dir.outfiles)
        inputs = list(dir.infiles)
    else:
        inputs = folder.glob(f'*{in_suffix}')
        outputs = folder.glob(f'*{out_suffix}')

    # Find the matching files with the outputs
    matching_inputs = [file.parent/f'{file.stem}{in_suffix}' for file in outputs]

    # Remove from the inputs the files present in matching_inputs
    nomatch_inputs = list(
        set(str(file) for file in inputs) - set(str(file) for file in matching_inputs)
        )
    nomatch_inputs = [Path(file) for file in nomatch_inputs]

    return nomatch_inputs,matching_inputs

# Define Parser and main
__doc__ = __doc__.format(in_suffix=GAUSSIAN_INPUT_SUFFIX,
                         out_suffix=GAUSSIAN_OUTPUT_SUFFIX,
                         script_name=DEFAULT_SCRIPT,
                         )

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('folder',
                    nargs='?',default=None,
                    help="Folder where the files are located. If not provided "
                    "it will use the current working directory.")
parser.add_argument('--outfile','-o',
                    dest='scriptname',
                    default=DEFAULT_SCRIPT,
                    help='name of the output file')
parser.add_argument('--software',
                    choices=['g09','g16'],
                    default=DEFAULT_SOFTWARE)
parser.add_argument('--recursive','-r',
                    action='store_true', default=False,
                    help="If enabled it will recursively search in the "
                    "subdirectories of the current folder")
parser.add_argument('--ascomments',
                    dest='as_comments',
                    action='store_true',default=False,
                    help=f"If enabled found {GAUSSIAN_INPUT_SUFFIX} files with "
                    f"a matching {GAUSSIAN_OUTPUT_SUFFIX} are included as comments")
parser.add_argument('--suffix',
                    default=(None,None),nargs=2,
                    help="Input and output suffix used for gaussian files") 
parser.add_argument('--norun',
                    dest='no_run',
                    action='store_true',default=False,
                    help="If enabled the submit command will instead just "
                    f"generate the {GAUSSIAN_INPUT_SUFFIX}.sub file")


def main(
         folder:Path|None,
         software:str=DEFAULT_SOFTWARE,
         suffix:tuple[str|None]=(None,None),
         recursive:bool=False,
         as_comments:bool=False,
         no_run:bool=False,
         scriptname:str=DEFAULT_SCRIPT):

    if folder is None: 
        folder = Path.cwd()

    in_suffix,out_suffix = select_suffix(*suffix)

    without_output, with_outputs = prepare_filepaths(folder,
                                                     in_suffix,
                                                     out_suffix,
                                                     recursive)
    
    entry = namedtuple('entry','folder file ascomment')
    
    files4submit = []

    for file in without_output: 
        files4submit.append(entry(folder=file.parent,file=file,ascomment=False))
    
     # add the ones that should go as comment
    if as_comments:
        for ofile in with_outputs: 
            ifile = ofile.with_suffix(in_suffix)
            files4submit.append(entry(folder=ifile.parent,file=ifile,ascomment=True))

    # Now create the submit script
    submit_lines = ['#!/bin/bash\n',
                    '# Automated Submit Script\n'
                    f'BASEDIR=$PWD;']
    files4submit.sort(key=lambda x: x[0])
    for folder,group in groupby(files4submit,key=lambda x: x[0]):
        folder_path = folder.relative_to(folder)
        if str(folder_path) != '.': 
            submit_lines.append(f'echo "moving to {folder_path}";')
            submit_lines.append(f'cd {folder_path};')
        entries = list(group)
        for entry in entries:
            folder,ifile,as_comment = entry
            line = submitline(ifile,
                              software=software,
                              ascomment=as_comment,
                              norun=no_run)
            submit_lines.append(line)
        if str(folder_path) != '.': 
            submit_lines.append('cd ${BASEDIR};')
    submit_lines.append('echo "Finished submiting calculations";')

    with open(folder/scriptname,'w') as F:
        F.write('\n'.join(submit_lines))
        