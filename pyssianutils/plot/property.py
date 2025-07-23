"""
Generate a quick figure for a single property of a single gaussian output 
calculation file. 
"""

import argparse
from pathlib import Path

from pyssian import GaussianOutFile
from pyssian.classutils import Geometry
from pyssian.chemistryutils import is_method

from ..utils import ALLOWEDMETHODS, potential_energies
from ..initialize import load_app_defaults

try:
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError as e: 
    LIBRARIES_LOADED = False
    LIBRARIES_ERROR = e
else:
    LIBRARIES_LOADED = True

BOHR2ANGS = 5.29177210544E-1 # Source: https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0
DEFAULTS = load_app_defaults()
DEFAULT_OUTFILE = Path(DEFAULTS['plot.property']['outfile'])
DEFAULT_PLOT = DEFAULTS['plot.property']['default_plot']
DEFAULT_COLOR = DEFAULTS['plot.property']['color']

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
                        default=DEFAULT_OUTFILE,
                        help='Output image file')
    if DEFAULTS['plot.property'].getboolean('default_interactive'): 
        parser.add_argument('--static',
                            dest='is_interactive',
                            action='store_false', default=True,
                            help="Write to a file instead of showing the figure "
                            "in a new window")
    else:
        parser.add_argument('--interactive',
                            dest='is_interactive',
                            action='store_true',default=False,
                            help="Instead of writing to a file open a window "
                            "showing the figure")

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
                    help="When not provided it will attempt (and may fail) to "
                    "guess the method used for the calculation to correctly "
                    "read the potential energy of each step. If it fails it "
                    "defaults to the Energy of the 'SCF Done:' ")

parameter = subparsers.add_parser('parameter',help='Draw a named geometrical parameter')
add_common_arguments(parameter)
parameter.add_argument('name',
                       help="Name of the parameter. For the available options "
                       "please look at the definitions on your file using "
                       "'pyssianutils others track'")

geometry = subparsers.add_parser('geometry',
                                 help="Draw a geometric parameter that may "
                                 "not be a internal parameter. If 2 atom "
                                 "ids are provided it will assume that it is a "
                                 "distance, 3 for an angle and 4 for a dihedral")
add_common_arguments(geometry)
geometry.add_argument('atoms',
                      nargs='+',type=int,
                      help="Atom numerical ids following the convention: "
                      "first atom = 1")

def main(
         ifile:str|Path,
         target:str,
         outfile:str|Path=DEFAULT_OUTFILE,
         line:bool=False,
         scatter:bool=False,
         color:str=DEFAULT_COLOR,
         is_interactive:bool=False,
         **kwargs):  
    
    assert DEFAULT_PLOT in ['line','scatter','both']
    # We want to delay any errors of optional libraries to the 
    # actual moment when they would be required
    if not LIBRARIES_LOADED: 
        raise LIBRARIES_ERROR
    
    if Path(outfile).suffix == '.svg':
        matplotlib.rcParams['svg.fonttype'] = 'none'
        
    with GaussianOutFile(ifile) as GOF: 
        GOF.read()

    match target:
        case 'energy':
            x,y,xlabel,ylabel = _main_energy(GOF,**kwargs)
        case 'parameter':
            x,y,xlabel,ylabel = _main_parameter(GOF,**kwargs)
        case 'geometry':
            x,y,xlabel,ylabel = _main_geometry(GOF,**kwargs)
        case _: 
            raise NotImplementedError(f'Plotting of property={target} is not implemented')
    
    if not line and not scatter:
        if DEFAULT_PLOT in ['line','both']:
            plt.plot(x,y,color=color)
        if DEFAULT_PLOT in ['scatter','both']:
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

def _main_geometry(GOF:GaussianOutFile,
                   atoms:tuple[int]):
    n = len(atoms)

    xlabel = 'iteration'

    match n: 
        case 2:
            i,j = atoms
            getter = lambda xyz: np.linalg.norm(xyz[i-1,:] - xyz[j-1,:])
            ylabel = f'Distance({i},{j}) Angstrom'
        case 3:
            i,j,k = atoms
            getter = lambda xyz: np.rad2deg(angle_between(xyz[i-1]-xyz[j-1],xyz[k-1]-xyz[j-1]))
            ylabel = f'Angle({i},{j},{k}) Degrees'
        case 4:
            i,j,k,l = atoms
            getter = lambda xyz: np.rad2deg(get_dihedral(xyz[i-1],xyz[j-1],xyz[k-1],xyz[l-1]))
            ylabel = f'Dihedral({i},{j},{k},{l}) Degrees'
        case _: 
            raise argparse.ArgumentError("the number of atom ids provided "
                                f"should be 2, 3 or 4. The input was: {atoms}")
    
    y = []
    for l202 in GOF.get_links(202):
        xyz = np.array(Geometry.from_L202(l202).coordinates)
        y.append(getter(xyz))
    
    y = np.array(y)
    x = np.arange(y.shape[0])
    
    return x,y,xlabel,ylabel