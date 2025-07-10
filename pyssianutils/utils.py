"""
todo
"""
import os
import argparse
from pathlib import Path
from ._version import __version__

SUBPARSERS = dict()
MAINS = dict() 

def register_subparser(f):
    # assume all functions that will be be decorated 
    # to create the corresponding subparsers are 
    # subparser_{command}
    command = f.__name__.split('_')[1]
    SUBPARSERS[command] = f
    return f
def register_main(f):
    # assume all functions that will be be decorated 
    # to create the corresponding MAINS are 
    # main_{command}
    command = f.__name__.split('_')[1]
    MAINS[command] = f
    return f

def create_parser()->argparse.ArgumentParser: 
    parser = argparse.ArgumentParser(description=__doc__,prog='pyssianutils')
    parser.add_argument('--version', action='version', version=f'pyssianutils {__version__}')
    subparsers = parser.add_subparsers(help='sub-command help',dest='command')


    for _,add_subparser in SUBPARSERS.items(): 
        add_subparser(subparsers)

    return parser


#parser.add_argument('Files',help='Gaussian Output Files',nargs='+')
#group_input = parser.add_mutually_exclusive_group()
#group_input.add_argument('-L','--ListFile',help="""When enabled instead of
#                    considering the files provided as the gaussian output files
#                    considers the file provided as a list of gaussian output
#                    files""",action='store_true',default=False)
#group_input.add_argument('-r','--folder',help="""Takes the folder and its
#                    subfolder hierarchy and creates a new folder with the same
#                    subfolder structure. Finds all the .out, attempts to find
#                    their companion .in files and creates the new inputs in
#                    their equivalent locations in the new folder tree structure.
#                    """,action='store_true',default=False)
#group_marker = parser.add_mutually_exclusive_group()
#group_marker.add_argument('-m','--marker',help="""Text added to the filename to
#                    differentiate the original .out file from the newly created
#                    one. """,default=None)
#group_marker.add_argument('--no-marker',help="""Files will be created with the
#                    same file name as the provided files but with the '.in'
#                    extension""", action='store_true',default=False,
#                    dest='no_marker')
#group_output = parser.add_mutually_exclusive_group()
#group_output.add_argument('-O','--OutDir',help="""Where to create the new files,
#                    defaults to the current directory""",default='')
#group_output.add_argument('--inplace',help="""Creates the new files in the same
#                    locations as the files provided by the user""",
#                    action='store_true',default=False)
#parser.add_argument('-ow','--overwrite',help="""When creating the new files if a
#                    file with the same name exists overwrites its contents. (The
#                    default behaviour is to raise an error to notify the user
#                    before overwriting).""",action='store_true',default=False)
#parser.add_argument('-T','--Tail',help="""Tail File that contains the extra
#                    options, such as pseudopotentials, basis sets """,
#                    default=None)
#parser.add_argument('--as-SP',help="""Removes the freq, opt and scan keyword if
#                    those existed in the previously existing inputs and changes
#                    the default marker to 'SP' """,action='store_true',
#                    default=False,dest='as_SP')
#parser.add_argument('--method',help="""New method/functional to use. Originally
#                    this option is thought to run DFT benchmarks it is not
#                    guaranteed a working input for CCSDT or ONIOM.""",
#                    default=None)
#parser.add_argument('--solvent',help="""New solvent to use in the calculation
#                    written as it would be written in Gaussian. ('vacuum' will
#                    remove the scrf keywords if they were in the previous input
#                    files)""",default=None)
#parser.add_argument('--smodel',default=None,choices=['smd','pcm',None], help="""
#                    Solvent model. The scrf keyword will only be included if the
#                    --solvent flag is enabled. (Defaults to None which implies
#                    that no change to the original inputs smodel will be done)
#                    """)
#parser.add_argument('--add-text', default=None, help="""Attempts to add
#                    literally the text provided to the command line.
#                    Recommended: "keyword=(value1,keyword2=value2)" """,
#                    dest='add_text')
#parser.add_argument('--no-submit',default=False,action='store_true',
#                    help="""Do not create a SubmitScript.sh File in the current
#                    directory""",dest='no_submit')
#parser.add_argument('--software',choices=['g09','g16'],help="""Version of
#                    gaussian to which the calculations will be sent.
#                    'qs {gxx}.queue.q file.in' (Default: g09)""",default='g09')
#parser.add_argument('--version',version=f'script version {__version__}',
#                    action='version')
#parser.add_argument('--suffix',default=None,nargs=2,help="""Input and output 
#                    suffix used for gaussian files""") 