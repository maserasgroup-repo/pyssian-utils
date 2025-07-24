"""
This module provides a set of functions with general utilities. as 
well as the basic variables for registering the subparsers and main functions
"""
import os
import re
import argparse
from pathlib import Path
from ._version import __version__
from pyssian.gaussianclasses import GaussianOutFile

from typing import Callable

# Core functions/Gobals for pyssianutils command line inner workings
MAINS = dict()
def register_main(f:Callable,name:None|str=None) -> Callable:
    """
    Function used to store the main functions of each command of pyssianutils,
    abstracting it from how it is actually stored. 

    Parameters
    ----------
    f : Callable
        any function to be stored
    name : None | str, optional
        name used to store the function. If none is provided it will assume that
        the function name follows the convention "{something}_name", by default None

    Returns
    -------
    Callable
        The function that was added. Allows the usage of register_main as a decorator.
    """
    if name is None: 
        command = f.__name__.split('_')[1]
    else:
        command = name
    MAINS[command] = f
    return f

def create_parser()-> tuple[argparse.ArgumentParser,argparse._SubParsersAction]:
    """
    Creates the highest-level parser of the pyssianutils as well as the 
    _SubparsersAction to which each subparser must be added.

    Returns
    -------
    tuple[argparse.ArgumentParser,argparse._SubParsersAction]
        parser,subparsers
    """
    parser = argparse.ArgumentParser(description=__doc__,prog='pyssianutils')
    parser.add_argument('--version', action='version', version=f'pyssianutils {__version__}')
    subparsers = parser.add_subparsers(help='sub-command help',dest='command')

    return parser, subparsers
def add_parser_as_subparser(subparsers:argparse._SubParsersAction,
                            parser:argparse.ArgumentParser,
                            name:str,
                            **kwargs) ->  argparse.ArgumentParser:
    """
    Adds a previously existing parser as a subparser. This function is copied 
    and adapted from the implementation of the function 
    argparse._SubParsersAction.add_parser in python 3.12.11.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction
        Subparser action (which allows the standard .add_parser method) where 
        the new parser will be added to.
    parser : argparse.ArgumentParser
        Existing parser that is going to be added as subparser.
    name : str
        value in the main parser to invoke the existing parser added as subparser
    **kwargs

    Returns
    -------
    argparse.ArgumentParser
        The same existing parser that was provided as input. In order to match 
        the behavior of argparse._SubParsersAction.add_parser

    Raises
    ------
    argparse.ArgumentError
        Conflict in subparser name
    argparse.ArgumentError
        Conflict in subparser alias
    """
    
    # set prog from the existing prefix
    if kwargs.get('prog') is None:
        kwargs['prog'] = '%s %s' % (subparsers._prog_prefix, name)

    aliases = kwargs.pop('aliases', ())

    if name in subparsers._name_parser_map:
        raise argparse.ArgumentError(subparsers, f'conflicting subparser: {name}')
    for alias in aliases:
        if alias in subparsers._name_parser_map:
            raise argparse.ArgumentError(subparsers, f'conflicting subparser alias: {alias}')
    
    if 'help' in kwargs:
        help = kwargs.pop('help')
        choice_action = subparsers._ChoicesPseudoAction(name, aliases, help)
        subparsers._choices_actions.append(choice_action)

    # create the parser and add it to the map
    # This is uneeded cause it already exists: 
    #     parser = subparsers._parser_class(**kwargs)
    subparsers._name_parser_map[name] = parser

    # make parser available under aliases also
    for alias in aliases:
        subparsers._name_parser_map[alias] = parser

    return parser

# Other functions utility variables
ALLOWEDMETHODS = ['oniom','mp2','mp2scs','mp4','ccsdt','default']
SCFCYCLE_PATTERN = re.compile(r'^\sE=\s?(-?[0-9]*\.[0-9]*)\s*Delta',re.MULTILINE)

# Class utils
class DirectoryTree(object):
    """
    Class that provides recursive file iteration search, iteration and recursive
    creation of directories following the same structure as the original one.
    """
    def __init__(self,path:str|Path|os.PathLike,in_suffix:str,out_suffix:str):
        self.root = Path(path)
        self.cwd = Path(os.getcwd())
        self.newroot = self.root
        self.in_suffix = in_suffix
        self.out_suffix = out_suffix
    def set_newroot(self,newroot:str|Path|os.PathLike):
        self.newroot = Path(newroot)

    def newpath(self,path:str|Path|os.PathLike) -> Path:
        """
        Takes a path rooted to the previous root and prepares it to be
        rooted in the new root.

        Parameters
        ----------
        path : str | Path | os.PathLike
            path to a file relative to the DirectoryTree's root

        Returns
        -------
        Path
            path of the file as if it was relative to the newroot instead of 
            the root
        """
        
        return self.newroot.joinpath(path.relative_to(self.root))

    @staticmethod
    def RecursiveFileSystemGenerator(path,key=None):
        """
        Generator that traverses the filesystem in depth first order and yields
        the paths that satisfy the key function condition. If no key function
        is provided, returns all folders and items. The first yield is always
        None, and the second yield is always the path value if it satisfies the
        key condition.

        Parameters
        ----------
        path : Path
            Path pointing to a directory.
        key : function
            A function that returns a boolean. Used in a similar fashion as
            the key paramer of the 'sorted' python builtin.
        """
        cls = DirectoryTree
        if key is None:
            key=lambda x: True
        yield None
        if key(path):
            yield path
        if path.is_dir():
            for subpath in path.iterdir():
                subgen =cls.RecursiveFileSystemGenerator(subpath,key=key)
                _ = next(subgen)
                for i in subgen:
                    yield i

    @property
    def folders(self):
        generator = self.RecursiveFileSystemGenerator
        _iter = generator(self.root,key=lambda x: x.is_dir())
        _  = next(_iter)
        return _iter

    @property
    def infiles(self):
        def f_in(x):
            Out = False
            if x.exists() and x.suffix == self.in_suffix:
                Out = True
            return Out
        _iter = self.RecursiveFileSystemGenerator(self.root,key=f_in)
        _  = next(_iter)
        return _iter

    @property
    def outfiles(self):
        def f_out(x):
            Out = False
            if x.exists() and x.suffix == self.out_suffix:
                Out = True
            return Out
        _iter = self.RecursiveFileSystemGenerator(self.root,key=f_out)
        _  = next(_iter)
        return _iter

    def create_folders(self):
        """
        Creates the folders of a new Directory tree, rooted in self.newroot
        instead of self.root
        """
        for folder in self.folders:
            newpath = self.newpath(folder)
            newpath.mkdir(parents=True,exist_ok=True)

# General Utils
def write_2_file(filepath:Path) -> Callable[[str],None]:
    """
    Creates a wrapper for appending text to a certain File. Assumes that each
    call is equivalent to writing a single line.

    Parameters
    ----------
    filepath : Path
        file where the output will be appended.

    Returns
    -------
    Callable[[str],None]
        a function where each call writes the text and attaches a newline at 
        the end of it.
    """
    def Writer(txt):
        with open(filepath,'a') as F:
            F.write(txt)
            F.write('\n')
    return Writer

# GaussianOutFile utils
def thermochemistry(GOF:GaussianOutFile) -> tuple[float|None,float|None,float|None]:
    """
    Returns the Zero Point Energy, Enthalpy and Free Energy
    from a frequency calculation.

    Parameters
    ----------
    GOF : GaussianOutFile
        Gaussian Output File Instance. (It assumes that previously the .read()
        or .update() methods have been used)

    Returns
    -------
    tuple[float|None,float|None,float|None]
        Zero point energy, Enthalpy, Free Energy
    """
    Link = GOF[-1].get_links(716)[-1]
    Z = Link.zeropoint[-1]
    H = Link.enthalpy[-1]
    G = Link.gibbs[-1]
    return Z, H, G
def potential_energy(GOF:GaussianOutFile,method:str='default')-> float|None:
    f"""
    Returns the last potential energy of a GaussianOutFile of a certain
    method. The default is the energy of the SCF cycle ('SCF Done:')

    Parameters
    ----------
    GOF : GaussianOutFile
    method : string
        For DFT and HF the default behavior is correct. For Post-HF methods
        it needs to be specified. 
        Currently: {ALLOWEDMETHODS}

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
def potential_energies(GOF:GaussianOutFile,method:str='default',withscf:bool=False)-> list[float|None]:
    f"""
    Returns all potential energies of a GaussianOutFile of a certain
    method. The default is the energy of the SCF cycle ('SCF Done:')

    Parameters
    ----------
    GOF : GaussianOutFile
    method : str
        For DFT and HF the default behavior is correct. For Post-HF methods
        it needs to be specified. 
        Currently: {ALLOWEDMETHODS}
    withscf : bool
        If Enabled (and method is 'default') it will include the energies of the
        scf iterations.

    Returns
    -------
    list[float]
        Energies
    """
    
    assert method in ALLOWEDMETHODS

    if method == 'mp2':
        energies = [l.MP2 for l in GOF.get_links(804)] 
    elif method == 'mp2scs':
        links502 = GOF.get_links(502)
        links804 = GOF.get_links(804)
        energies = [l0.energy + l1.get_SCScorr() for l0,l1 in zip(links502,links804)]
    elif method == 'ccsdt':
        energies = [l.CCSDT for l in GOF.get_links(913)]
    elif method == 'mp4':
        energies = [l.MP4 for l in GOF.get_links(913)]
    elif method == 'oniom':
        energies = [l.energy for l in GOF.get_links(120)]
    else: # Otherwise go to the "Done(...)" Energy
        energies = []
        links502 = GOF.get_links(502)
        links508 = GOF.get_links(508)
        if not links508:
            for l502 in links502:
                if withscf:
                    scf_energies = list(map(float,SCFCYCLE_PATTERN.findall(l502.text)))
                    energies.extend(scf_energies)
                    if scf_energies and (scf_energies[-1] != l502.energy):
                        energies.append(l502.energy)
                energies.append(l502.energy)
        else:
            for l502,l508 in zip(links502,links508):
                if withscf:
                    scf_energies = list(map(float,SCFCYCLE_PATTERN.findall(l502.text)))
                    energies.extend(scf_energies)
                    if l508.energy is not None: 
                        energies.append(l508.energy)
                    elif scf_energies and (scf_energies[-1] != l502.energy): 
                        energies.append(l502.energy)
                else:
                    energy = l502.energy
                    if l508.energy is not None: 
                        energy = l508.energy
                    energies.append(energy)
    return energies

# Console Utils
def print_convergence(GOF:GaussianOutFile,JobId:int,Last:bool=False):
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
def print_thermo(GOF:GaussianOutFile):
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
