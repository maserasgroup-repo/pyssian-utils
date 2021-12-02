#!/bin/usr/env python3

"""
Checks all .in files in the current directory or the provided folder to generate 
a SubmitScript.sh that properly sends them to their queues (Files with a 
matching .out file are ignored as default). It checks in which queue they should
go according to the values of nprocshared and %mem. To use the generated script 
run in the cluster: 'chmod +x SubmitScript.sh; ./SubmitScript;' or 
'bash SubmitScript.sh'
"""

import os
import argparse
from pathlib import Path
from collections import namedtuple
from itertools import groupby

from pyssian.classutils import DirectoryTree
from pyssian.gaussianclasses import GaussianInFile

__version__ = '0.1.0'

Queue = namedtuple('Queue','nprocesors memory'.split())
QUEUES = {4:Queue(4,8),8:Queue(8,24),
          12:Queue(12,24),20:Queue(20,48),
          24:Queue(24,128),28:Queue(28,128),
          36:Queue(36,192),'q4':Queue('q4',4)}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('software',choices=['g09','g16'],default='g09',
                    nargs='?')
parser.add_argument('--recursive','-r',action='store_true',help="""If enabled it
                    will recursively search in the subdirectories of the current 
                    folder""")
parser.add_argument('--ascomments',help="""If enabled found .in files with a
                matching .out are included as comments""",action='store_true')
parser.add_argument('--norun',help="""If enabled the submit command will instead
                just generate the .in.sub file""",action='store_true')
parser.add_argument('--version',version=f'script version {__version__}',
                    action='version')


class NotFoundError(RuntimeError):
    pass

def submitline(File,software,ascomment,norun):
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

    with GaussianInFile(File) as GIF: 
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
        queue = QUEUES[nprocs]
    
    line = f'{{}}qs {software}.c{queue.nprocesors}m{queue.memory} {{}} {File.name};'

    if norun and ascomment: line = line.format('#','0')
    elif norun:             line = line.format('' ,'0')
    elif ascomment:         line = line.format('#','' )
    else:                   line = line.format('' ,'' )

    return  line

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

def prepare_filepaths(cwd,recursive=False):
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
    if recursive:
        dir = DirectoryTree(cwd)
        outputs = list(dir.outfiles)
        inputs = list(dir.infiles)
    else:
        inputs = cwd.glob('*.in')
        outputs = cwd.glob('*.out')

    # Find the matching files with the outputs
    matching_inputs = [file.parent/f'{file.stem}.in' for file in outputs]

    # Remove from the inputs the files present in matching_inputs
    nomatch_inputs = list(set(str(file) for file in inputs) - set(str(file) for file in matching_inputs))
    nomatch_inputs = [Path(file) for file in nomatch_inputs]

    return nomatch_inputs,matching_inputs

if __name__ == "__main__":
    args = parser.parse_args()

    cwd = Path(os.getcwd())

    without_output, with_outputs = prepare_filepaths(cwd,recursive=args.recursive)
    entry = namedtuple('entry','folder file ascomment')
    
    files4submit = []

    for file in without_output: 
        files4submit.append(entry(folder=file.parent,file=file,ascomment=False))
    
     # add the ones that should go as comment
    if args.ascomments:
        for ofile in with_outputs: 
            file = ofile.parent / (ofile.stem + '.in')
            files4submit.append(entry(folder=file.parent,file=file,ascomment=True))

    # Now create the submit script
    SubmitLines = ['#!/bin/bash\n',
                   '# Automated Submit Script\n'
                   f'BASEDIR=$PWD;']
    files4submit.sort(key=lambda x: x[0])
    for folder,group in groupby(files4submit,key=lambda x: x[0]):
        folder_path = folder.relative_to(cwd)
        if str(folder_path) != '.': 
            SubmitLines.append(f'echo "moving to {folder_path}";')
            SubmitLines.append(f'cd {folder_path};')
        entries = list(group)
        for entry in entries:
            folder,file,ascomment = entry
            line = submitline(file,
                              software=args.software,
                              ascomment=ascomment,
                              norun=args.norun)
            SubmitLines.append(line)
        if str(folder_path) != '.': 
            SubmitLines.append('cd ${BASEDIR};')
    SubmitLines.append('echo "Finished submiting calculations";')

    with open('SubmitScript.sh','w') as F:
        F.write('\n'.join(SubmitLines))
        