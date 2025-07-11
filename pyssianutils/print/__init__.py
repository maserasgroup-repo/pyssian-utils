from pathlib import Path

from ..utils import register_subparser, register_main
from ..initialize import get_appdir
from .potential import add_subparser as add_potential_options
from .potential import main as potential_main
from .thermo import add_subparser as add_thermo_options
from .thermo import main as thermo_main
from .summary import add_subparser as add_summary_options
from .summary import main as summary_main

# Typing imports
import argparse

@register_subparser
def subparser_print(subparsers:argparse._SubParsersAction):
    subparser = subparsers.add_parser('print', help=""" Gathers the different 
                                      output printing options""")

    subsubparsers = subparser.add_subparsers(help="""if no subcommand is 
                                             specified the default one is used""",
                                             dest='print_mode')

    add_potential_options(subsubparsers)

    add_thermo_options(subsubparsers)

    add_summary_options(subsubparsers)

@register_main
def main_print(print_mode:str|None=None,
               **kwargs): 

    appdir = get_appdir()
    if not appdir.exists(): 
        raise RuntimeError(f"{appdir} does not exist. Please ensure to run pyssianutils 'init'")

    if print_mode == 'potential': 
        potential_main(**kwargs)
    elif print_mode == 'thermo': 
        thermo_main(**kwargs)
    elif print_mode == 'summary': 
        summary_main(**kwargs)
    


