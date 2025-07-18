"""
Gathers the other more specific utilities
"""
import argparse

from ..utils import add_parser_as_subparser

from . import track
from . import cubestddft

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(help='sub-command help',dest='other_command')
add_parser_as_subparser(subparsers,
                        track.parser, 'track',
                        help=track.__doc__)
add_parser_as_subparser(subparsers,
                        cubestddft.parser, 'cubes-tddft',
                        help=cubestddft.__doc__)

def main(
         other_command:str|None=None,
         **kwargs):

    if other_command == 'track': 
        track.main(**kwargs)
    elif other_command == 'cubes-tddft': 
        cubestddft.main(**kwargs)

    