"""
Gathers the different output printing options
"""
import argparse

from ..utils import add_parser_as_subparser

from . import potential
from . import thermo
from . import summary

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(help='sub-command help',dest='print_mode')
add_parser_as_subparser(subparsers,
                        potential.parser, 'potential',
                        help=potential.__doc__)
add_parser_as_subparser(subparsers,
                        thermo.parser,'thermo',
                        help=thermo.__doc__)
add_parser_as_subparser(subparsers,
                        summary.parser,'summary',
                        help=summary.__doc__)

def main(
        print_mode:str|None=None,
        **kwargs):

    if print_mode == 'potential': 
        potential.main(**kwargs)
    elif print_mode == 'thermo': 
        thermo.main(**kwargs)
    elif print_mode == 'summary': 
        summary.main(**kwargs)
    


