"""
Gathers various plotting options
"""
import argparse

from ..utils import add_parser_as_subparser

from . import optview
from . import optmulti
from . import property

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(help='sub-command help',dest='plot_mode')
add_parser_as_subparser(subparsers,
                        optview.parser, 'optview',
                        help=optview.__doc__)
add_parser_as_subparser(subparsers,
                        optmulti.parser, 'optmulti',
                        help=optmulti.__doc__)
add_parser_as_subparser(subparsers,
                        property.parser, 'property',
                        help=property.__doc__)

def main(
        plot_mode:str|None=None,
        **kwargs):

    if plot_mode == 'optview': 
        optview.main(**kwargs)
    if plot_mode == 'optmulti': 
        optmulti.main(**kwargs)
    if plot_mode == 'property': 
        property.main(**kwargs)