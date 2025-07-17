"""
Generates submission scripts for different clusters architectures based on 
the gaussian input and output suffixes.
"""
import argparse

from ..utils import add_parser_as_subparser

from . import custom
from . import slurm

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(help='sub-command help',dest='submit_mode')

add_parser_as_subparser(subparsers,
                        custom.parser, 'custom',
                        help=custom.__doc__)

add_parser_as_subparser(subparsers,
                        slurm.parser, 'slurm',
                        help=slurm.__doc__)

def main(
         submit_mode:str|None=None,
         **kwargs):

    if submit_mode == 'custom': 
        custom.main(**kwargs)
    if submit_mode == 'slurm': 
        slurm.main(**kwargs)
