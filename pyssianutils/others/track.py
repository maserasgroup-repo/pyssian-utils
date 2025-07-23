"""
Prints the name of the scanned variable, its value (in Bohrs or radians), 
derivative, Max Forces convergence Y/N, Cartesian forces value and Geometry 
index of the geometry in the file. If no variable is provided nor it is a scan
calculation it will print the variables that may be tracked and exit.
"""
import argparse

import re
from pathlib import Path

from pyssian import GaussianOutFile
from ..utils import write_2_file
from ..initialize import load_app_defaults

# Typing imports
from typing import Protocol
from pyssian.linkjobparsers import Link716,Link103

class Parameter(Protocol):
    Name:str|None
    Definition:str|None
    Value:float|int|None
    Derivative:float|int|None
class ConverItem(Protocol):
    Item:str|None
    Value:float|None
    Threshold:float|None
    Converged:bool|None
class Derivative(Protocol): 
    Var:str|None
    old:float|None
    dEdX:float|None
    dXl:float|None
    dXq:float|None
    dXt:float|None
    new:float|None

# Defaults and Globals
RE_CARTESIAN = re.compile(r'Cartesian.Forces\:.*Max\s*([0-9|\.]*).RMS\s*[0-9|\.]*')

DEFAULTS = load_app_defaults()
VALUE_FMT = DEFAULTS['others.track']['value_fmt']
DEDX_FMT = DEFAULTS['others.track']['dEdX_fmt']
FORCES_FMT = DEFAULTS['others.track']['forces_fmt']

# Utility Functions
def get_differential(Link:Link103,variable:Parameter):
    for item in Link.derivatives:
        if item.Var == variable.Name:
            break
    else:
        raise ValueError(f'Variable {variable.Name} not Found in {Link.__repr__()}')
    try:
        float(item.dEdX)
    except ValueError: 
        return item.dEdX
    else:
        return DEDX_FMT.format(float(item.dEdX))
def get_parameter_value(Link:Link103,variable:Parameter):
    for item in Link.parameters:
        if item.Name == variable.Name:
            break
    else:
        raise ValueError(f'Variable {variable.Name} not Found in {Link.__repr__()}')
    try:
        float(item.Value)
    except ValueError: 
        return item.Value
    else:
        return VALUE_FMT.format(float(item.Value))
def get_value_from_derivatives(link:Link103,variable:Parameter):
    for item in link.derivatives:
        if item.Var == variable.Name:
            break
    else:
        raise ValueError(f'Variable {variable.Name} not Found in {link.__repr__()}')
    return item.new
def get_convergence(link:Link103):
    for item in link.convergence:
        if item.Item =='Maximum Force':
            break
    else:
        raise RuntimeError('No Maximum Force Convergence item found')
    if item.Converged:
        return 'YES'
    return 'NO'
def get_cartesian_forces_max(link:Link716):
    re_match = RE_CARTESIAN.findall(link.text)
    if not re_match:
        return ''
    try: 
        float(re_match[0])
    except ValueError: 
        return re_match
    else:
        return FORCES_FMT.format(float(re_match[0]))

# Parser and Main definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('ifile',
                    help='Gaussian Output File')
parser.add_argument('variable',
                    nargs='?',default=None,
                    help='Internal variable name to track')
parser.add_argument('-o','--outfile',
                    default=None,dest='ofile',
                    help="""File to write the Data. If it exists, the data will 
                    be appended, if not specified it will print to the console""")
parser.add_argument('--scan',help="""Specify that the gaussian out file is a
                    a scan automatically detect the coordinate to track""",
                    action='store_true')

def main(
         ifile:str|Path,
         ofile:str|Path|None=None,
         scan:bool=False,
         variable:str|None=None
         ):
    
    ifile = Path(ifile)

    if ofile is not None:
        ofile = Path(ofile)
        write_output = write_2_file(ofile)
    else:
        write_output = print
    
    # Actual parsing
    if not ifile.exists(): #In the case of an empty filename, write an empty line
        raise ValueError(f'File {ifile} does not exist')
    
    with GaussianOutFile(ifile,[103,202,716]) as GOF:
        GOF.update()
    
    if variable is None and not scan: 
        link = GOF.get_links(103)[0]
        print(f'Available parameters to track for {ifile}')
        print(f'      Name    Definition    ')
        for parameter in link.parameters:
            print(f'    {parameter.Name:>6}    {parameter.Definition:<10}')
        return

    # Header to know which is each column
    msg_ini = '{: ^10}' + '\t{: ^10}'*5
    write_output(msg_ini.format(
        'Variable','Value','dE/dX','Conver','Car Forces','Geom Num')
    )

    # Format for the numbers
    txt = '{: ^10}\t{: ^10}\t{: ^10}\t{: ^10}\t{: ^10}\t{: ^10}'

    if scan: 
        link = GOF.get_links(103)[0]
        for var in link.parameters:
            if var.Derivative == 'Scan':
                target_var = var
                target_value = var.Value
                break
        else:
            raise ValueError("No 'Scan' variable found in the file")
        target_name = target_var.Name
    else:
        link = GOF.get_links(103)[0]
        for var in link.parameters:
            if var.Name == variable:
                target_var = var
                target_value = var.Value
                break
        else:
            raise ValueError(f"The variable '{variable}' is not an Internal Coordinate")
        target_name = variable

    geom_index = 0
    for l202,l716,l103 in zip(GOF[0][1:],GOF[0][2:],GOF[0][3:]):
        if (l202.number != 202 or l716.number != 716 or l103.number != 103):
            continue
        if l103.parameters and scan:
            target_value = get_parameter_value(l103,target_var)
        elif not scan:
            target_value = get_value_from_derivatives(l103,target_var)
        dEdX = get_differential(l103,target_var)
        convergence = get_convergence(l103)
        forces = get_cartesian_forces_max(l716)
        write_output(txt.format(target_name,target_value,dEdX,convergence,forces,geom_index+1))

        # Update geom index
        geom_index += 1    

