"""
This module provides a set of functions with general utilities. as 
well as the basic variables for registering the subparsers and main functions
"""

import argparse
from pathlib import Path
from ._version import __version__
from pyssian.gaussianclasses import GaussianOutFile

# Core functions for pyssianutils command line inner workings
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

# Other functions utility variables
ALLOWEDMETHODS = ['oniom','mp2','mp2scs','mp4','ccsdt','default']

# General Utils
def write_2_file(filepath:Path):
    """
    Creates a wrapper for appending text to a certain File. Assumes that each
    call is equivalent to writing a single line.
    """
    def Writer(txt):
        with open(filepath,'a') as F:
            F.write(txt)
            F.write('\n')
    return Writer

# GaussianOutFile utils
def thermochemistry(GOF:GaussianOutFile) -> tuple[float|None]:
    """
    Returns the Zero Point Energy, Enthalpy and Free Energy
    from a frequency calculation.

    Parameters
    ----------
    GOF : GaussianOutFile

    Returns
    -------
    tuple
        (Z, H, G)
    """
    Link = GOF[-1].get_links(716)[-1]
    Z = Link.zeropoint[-1]
    H = Link.enthalpy[-1]
    G = Link.gibbs[-1]
    return Z, H, G
def potential_energy(GOF:GaussianOutFile,method:str='default')-> float|None:
    """
    Returns the last potential energy of a GaussianOutFile of a certain
    method. The default is the energy of the SCF cycle ('SCF Done:')

    Parameters
    ----------
    GOF : GaussianOutFile
    Method : string
        For DFT and HF the default behavior is correct. For Post-HF methods
        it needs to be specified. 
        Currently: ['oniom','mp2','mp2scs','MP4','ccsdt']

    Returns
    -------
    float
        Energy
    """
    
    assert method in ALLOWEDMETHODS

    if method == 'mp2': # Search for MP2 energy
        energy = GOF.get_links(804)[-1].MP2
    elif method == 'mp2scs':
        HF = GOF.get_links(502)[-1].energy
        SCS_corr = GOF.get_links(804)[-1].get_SCScorr()
        energy = HF + SCS_corr
    elif method == 'ccsdt': # Search for CCSD(T) energy or default to MP4
        Aux = GOF.get_links(913)[-1]
        energy = Aux.CCSDT
    elif method == 'mp4':
        Aux = GOF.get_links(913)[-1]
        energy = Aux.MP4
    elif method == 'oniom': 
        Aux = GOF.get_links(120)[-1]
        energy = Aux.energy
    else: # Otherwise go to the "Done(...)" Energy
        energy = None
        links = GOF.get_links(502,508)
        if links:
            energy = links[-1].energy
        if links and energy is None: 
            energy = links[-2].energy
    return energy

# Console Utils
def print_convergence(GOF,JobId,Last=False):
    """
    Displays the Convergence parameters for a certain InternalJob of a
    GaussianOutFile.

    Parameters
    ----------
    GOF : GaussianOutFile
        Gaussian File whose convergence parameters are going to be displayed.
    JobId : int
        InternalJob number in the Gaussian Output File.
    Last : bool
        If enabled only the last set of parameters is displayed
        (the default is False).
    """
    if Last:
        GOF[JobId].get_links(103)[-1].print_convergence()
    else:
        for i,L in enumerate(GOF[JobId].get_links(103)):
            print(i)
            L.print_convergence()
def print_thermo(GOF):
    """
    Prints in the console the thermochemistry of a GaussianOutFile.

    Parameters
    ----------
    GOF : GaussianOutFile
        Gaussian File whose thermochemistry is going to be displayed.
    """
    Z,H,G = thermochemistry(GOF)
    U = potential_energy(GOF)
    print(f"{'U': ^14}\t{'Z': ^14}\t{'H': ^14}\t{'G': ^14}")
    print(f"{U: 03.9f}\t{Z: 03.9f}\t{H: 03.9f}\t{G: 03.9f}")
