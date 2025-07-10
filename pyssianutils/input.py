import shutil
import platform
import warnings
import tarfile

from pathlib import Path

from .utils import register_subparser, register_main
from .initialize import get_appdir
from ._inputHT import add_subparser_options as add_inputHT_options
from ._asinput import add_subparser_options as add_asinput_options

# Typing imports
import argparse

def add_common_parser_options(parser:argparse.ArgumentParser):

    group_marker = parser.add_mutually_exclusive_group()
    group_marker.add_argument('-m','--marker',
                            default='new',
                            help="""Text added to the filename to differentiate 
                            the original file from the newly created one.
                            For example, myfile.com may become myfile_marker.com""")
    group_marker.add_argument('--no-marker',
                            action='store_true',
                            default=False,
                            dest='no_marker',
                            help="The file stems are kept")

@register_subparser
def subparser_input(subparsers:argparse._SubParsersAction):
    subparser = subparsers.add_parser('input', help=""" This is an alias to the 
                                      user's default input method that also 
                                      includes the option of just changing 
                                      the default input method.""")
    
    assert type(subparser) == argparse.ArgumentParser
    subparser.add_argument('--set-inputHT-default',
                           help="""Set the 'inputHT' gaussian input generation
                           as the default method""",
                           action='store_true',
                           default=False,
                           dest='set_inputHT_default')
    subparser.add_argument('--set-asinput-default',
                           help="""Set the 'asinput' gaussian input generation 
                           as the default one""",
                           action='store_true',
                           default=False,
                           dest='set_asinput_default')


    appdir = get_appdir()
    if appdir.exists(): 
        defaults = dict() # read the defaults
        input_default = defaults.get('input_default','inputHT') # TEMPORARY PATCH 
    else: 
        input_default = None
    
    subsubparsers = subparser.add_subparsers(help="""if no subcommand is 
                                             specified the default one is used""",
                                             dest='input_mode')
    
    subparser.set_defaults(input_mode=input_default)

    if input_default == 'inputHT': 
        default_input_options = subparser.add_argument_group('inputHT (default) options')
        add_inputHT_options(default_input_options)
    elif input_default == 'asinput': 
        default_input_options = subparser.add_argument_group('inputHT (default) options')
        add_asinput_options(subparser)
    
    inputht = subsubparsers.add_parser('inputHT', help="""Create inputs using a 
                                    Header and a Tail File""")
    add_inputHT_options(inputht)

    asinput = subsubparsers.add_parser('asinput', help="""Create inputs based on
                                    existing input files with a matching name""")
    add_asinput_options(asinput)


def modify_defaults(default_input:str|None=None):
    appdir = get_appdir()
    defaults = dict() # read appdir/defaults.ini
    if default_input is not None:
        defaults['default_input'] = default_input
    # Save defaults

def main_input(default_input:str|None=None,
               set_inputHT_default:bool=False,
               set_asinput_default:bool=False): 

    appdir = get_appdir()
    if not appdir.exists(): 
        raise RuntimeError(f"{appdir} does not exist. Please ensure to run pyssianutils 'init'")

    if set_inputHT_default: 
        modify_defaults(default_input='inputHT')
        return
    
    if set_asinput_default:
        modify_defaults(default_input='asinput')
        return
    

