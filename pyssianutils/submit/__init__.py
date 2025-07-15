"""
Generates submission scripts for different clusters architectures based on 
the gaussian input and output suffixes.
"""
import argparse

from ..utils import add_parser_as_subparser
from ..initialize import check_initialization

from . import custom

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(help='sub-command help',dest='submit_mode')

add_parser_as_subparser(subparsers,
                        custom.parser, 'custom',
                        help=custom.__doc__)

def main(
         submit_mode:str|None=None,
         **kwargs):

    check_initialization()

    if submit_mode == 'custom': 
        custom.main(**kwargs)
