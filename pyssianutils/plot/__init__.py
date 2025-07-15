"""
Gathers various plotting options
"""
import argparse

from ..utils import add_parser_as_subparser

from . import optview

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(help='sub-command help',dest='plot_mode')
add_parser_as_subparser(subparsers,
                        optview.parser, 'optview',
                        help=optview.__doc__)

def main(
        plot_mode:str|None=None,
        **kwargs):

    if plot_mode == 'optview': 
        optview.main(**kwargs)