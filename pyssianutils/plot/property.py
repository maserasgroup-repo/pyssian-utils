"""
Generate a quick figure for a single property of a single gaussian output 
calculation file. 
"""

import argparse
import warnings
from pathlib import Path

from pyssian import GaussianOutFile
from pyssian.classutils import Geometry
from pyssian.chemistryutils import is_method

from ..utils import ALLOWEDMETHODS, potential_energies
from ..initialize import load_app_defaults

try:
    import numpy as np
    import pandas as pd 
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError as e: 
    LIBRARIES_LOADED = False
    LIBRARIES_ERROR = e
else:
    LIBRARIES_LOADED = True

BOHR2ANGS = 5.29177210544E-1 # Source: https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0

# Utility functions
def guess_method(GOF:GaussianOutFile): 
    commandline = GOF.get_links(1)[-1].commandline
    # Assume that any "/" is not in any relevant keyword and it will only split 
    # a possible "method/basis" nomenclature
    commandline = commandline.replace('/',' ').split()
    method = 'default'
    for candidate in commandline: 
        if is_method(candidate): 
            method = candidate.lower()
    
    if method in ['oniom','mp2','mp2scs','mp4','ccsdt']: 
        return method
    else: 
        return 'default'
def angle_between(v1:np.array,v2:np.array):
    # Computes the angle between two vectors
    # Inputs two vectors numpy.array and returns the angle in radians
    # Handles vector with the same direction
    # Requires numpy library
    # Reference:   "http://stackoverflow.com/a/13849249/71522"
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1!=0 and n2!=0:
        v1_u = v1/n1
        v2_u = v2/n2
        return np.arccos(np.clip(np.dot(v1_u, v2_u),-1.0,1.0))
    else:
        return 0
def get_dihedral(i:np.array,j:np.array,k:np.array,l:np.array):
    # Inputs 4 Points as numpy.array and returns the dihedral between the
    # planes ijk and jkl in radians
    # Get the normal vector for the planes
    nijk = np.cross(i-j,k-j)
    njkl = np.cross(j-k,l-k)
    # Get vector normal to both normal vectors
    normal = np.cross(nijk,njkl)
    # Calculate angle using the function already defined
    dihedral = angle_between(nijk,njkl)
    # Assign sign criteria
    if np.dot(normal,j-k) < 0.0:
        dihedral = -dihedral
    return dihedral

def add_common_arguments(parser:argparse.ArgumentParser): 
    parser.add_argument('ifile',help='Gaussian Output File')
    parser.add_argument('--outfile',
                        default=Path('screen.png'),
                        help='Output image file')
    parser.add_argument('--interactive',
                        dest='is_interactive',
                        action='store_true',default=False,
                        help="""Instead of writing to a file open a window showing 
                        the figure""")
    parser.add_argument('--browser',
                        dest='in_browser',
                        action='store_true',default=False,
                        help="""Only if --interactive is enabled, it will display
                        the image in the browser. To exit remember to Ctrl+C""")

# Parser and main definition
parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(help='sub-command help',dest='target')
energy = subparsers.add_parser('energy',help='Draw the potential energy')
add_common_arguments(energy)
energy.add_argument('--include-scf',
                    dest='include_scf',
                    default=False,action='store_true',
                    help='include the energies of each step of the SCF cycles')
energy.add_argument('--method',
                    default='default',type=lambda x: x.lower(),
                    choices=ALLOWEDMETHODS,
                    help=""" When not provided it will 
                    attempt (and may fail) to guess the method used 
                    for the calculation to correctly read the potential
                    energy of each step. If it fails it defaults to the 
                    Energy of the 'SCF Done:' """)

parameter = subparsers.add_parser('parameter',help='Draw the a named geometrical parameter')
add_common_arguments(parameter)
parameter.add_argument('name',
                       help="""Name of the parameter. For the available options 
                       please look at the definitions on your file using 
                       pyssianutils others track""")

distance = subparsers.add_parser('distance',help='Draw the distance between two atoms')
add_common_arguments(distance)
distance.add_argument('atoms',
                       nargs=2,type=int,
                       help="""Atom numerical ids following Gaussian's convention
                       (First atom = 1)""")

angle = subparsers.add_parser('angle',help='Draw the angle between three atoms')
add_common_arguments(angle)
angle.add_argument('atoms',
                   nargs=3,type=int,
                   help="""Atom numerical ids following Gaussian's convention
                   (First atom = 1)""")

dihedral = subparsers.add_parser('dihedral',help='Draw the dihedral between 4 atoms')
add_common_arguments(dihedral)
dihedral.add_argument('atoms',
                      nargs=4,type=int,
                      help="""Atom numerical ids following Gaussian's convention
                      (First atom = 1)""")


def main(
         ifile:str|Path,
         outfile:str|Path,
         target:str,
         line:bool=False,
         scatter:bool=False,
         color:str='k',
         is_interactive:bool=False,
         in_browser:bool=False,
         **kwargs):  
    
    if is_interactive and in_browser: 
        matplotlib.use('WebAgg')
    elif is_interactive: 
        warnings.warn("""We have observed that while the figure generated 
                      when writing to a file maintains all desired proportions
                      when showing it interactively (not in the browser) 
                      fontsizes and relative positions are not respected.""")
        
    with GaussianOutFile(ifile) as GOF: 
        GOF.read()

    match target:
        case 'energy':
            x,y,xlabel,ylabel = _main_energy(GOF,**kwargs)
        case 'parameter':
            x,y,xlabel,ylabel = _main_parameter(GOF,**kwargs)
        case 'distance':
            x,y,xlabel,ylabel = _main_distance(GOF,**kwargs)
        case 'angle':
            x,y,xlabel,ylabel = _main_angle(GOF,**kwargs)
        case 'dihedral':
            x,y,xlabel,ylabel = _main_dihedral(GOF,**kwargs)
        case _: 
            raise NotImplementedError(f'Plotting of property={target} is not implemented')
    
    if not line and not scatter:
        plt.plot(x,y,color=color)
        plt.scatter(x,y,c=color)
    elif line: 
        plt.plot(x,y,color=color)
    else:
        plt.scatter(x,y,color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(Path(ifile).stem)

    if is_interactive:
        plt.show(block=True)
    else:
        print(f'writing -> {outfile}')
        plt.savefig(outfile,bbox_inches='tight')

def _main_energy(
        GOF:GaussianOutFile,
        method:str,
        include_scf:bool=False):
    y = np.array(potential_energies(GOF,method,include_scf))
    x = np.arange(y.shape[0])
    ylabel = 'Potential Energy, hartree'
    xlabel = 'iteration'
    if include_scf: 
        xlabel = 'scf step'
    return x,y,xlabel,ylabel

def guess_parameter_unit(name:str):
    if name.startswith('R'):
        converter,unit = lambda x: x*BOHR2ANGS, 'Angstrom'
    elif name[0] in ['D','I','A']:
        converter,unit = lambda x: np.rad2deg(x), 'Degrees'
    else:
        converter, unit = lambda x: x, '(unknown)'
    return converter, unit
def _main_parameter(
        GOF:GaussianOutFile,
        name:str):
    links103 = GOF.get_links(103)
    # Guess the unit of the parameter
    converter,unit = guess_parameter_unit(name)
    y = []
    for l103 in links103:
        if l103.mode != 'Iteration':
            iterable = l103.parameters
            get_name = lambda x: x.Name
            get_value = lambda x: float(x.Value)
        else:
            iterable = l103.derivatives
            get_name = lambda x: x.Var
            get_value = lambda x: converter(float(x.new))

        for parameter in iterable:
            if get_name(parameter) == name:
                y.append(get_value(parameter))
                break
        else:
            y.append(np.nan)
    y = np.array(y)
    x = np.arange(y.shape[0])
    ylabel = f'Parameter {name}, {unit}'
    xlabel = 'iteration'
    return x,y,xlabel,ylabel

def _main_distance(
        GOF:GaussianOutFile,
        atoms:tuple[int,int,int]):
    
    source,target = atoms # Ids, first=1

    y = []
    for l202 in GOF.get_links(202):
        xyz = np.array(Geometry.from_L202(l202).coordinates)
        distance = np.linalg.norm(xyz[source-1,:] - xyz[target-1,:])
        y.append(distance)
    
    y = np.array(y)
    x = np.arange(y.shape[0])
    ylabel = f'Distance({source},{target}) Angstrom'
    xlabel = 'iteration'
    
    return x,y,xlabel,ylabel

def _main_angle(
        GOF:GaussianOutFile,
        atoms:tuple[int,int,int]):
    
    i,j,k = atoms

    y = []
    for l202 in GOF.get_links(202):
        xyz = np.array(Geometry.from_L202(l202).coordinates)
        angle = angle_between(xyz[i-1],xyz[j-1],xyz[k-1])
        y.append(angle)
    
    y = np.array(y)
    x = np.arange(y.shape[0])
    ylabel = f'Angle({i},{j},{k}) Angstrom'
    xlabel = 'iteration'
    
    return x,y,xlabel,ylabel

def _main_dihedral(
        GOF:GaussianOutFile,
        atoms:tuple[int,int,int,int]):
    
    i,j,k,l = atoms

    y = []
    for l202 in GOF.get_links(202):
        xyz = np.array(Geometry.from_L202(l202).coordinates)
        angle = get_dihedral(xyz[i-1],xyz[j-1],xyz[k-1],xyz[l-1])
        y.append(angle)
    
    y = np.array(y)
    x = np.arange(y.shape[0])
    ylabel = f'Angle({i},{j},{k}) Angstrom'
    xlabel = 'iteration'
    
    return x,y,xlabel,ylabel