#!/bin/usr/env python3
"""
Prints the name of the scanned variable, its value, derivative, Max Forces
conversion Y/N, Cartesian forces value and Geometry index of the geometry in
the file.
"""

import os
import re
from pathlib import Path

import argparse

from pyssian import GaussianOutFile
from pyssianutils.functions import write_2_file

__version__ = '0.0.0'

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('File',help='Gaussian Output File',)
parser.add_argument('Var',help='Internal variable name to track',nargs='?')
parser.add_argument('-O','--OutFile',help="""File to write the Data. If it
                    exists, the data will be appended, if not specified it will
                    print to the console""",default=None)
parser.add_argument('--scan',help="""Specify that the gaussian out file is a
                    a scan automatically detect the coordinate to track""",
                    action='store_true')

def GetDeriv(Link,Var):
    for item in Link.derivatives:
        if item.Var == Var.Name:
            return item.dEdX
    else:
        raise ValueError(f'Variable {Var.Name} not Found in {Link.__repr__()}')

def GetParameterValue(Link,Var):
    for item in Link.parameters:
        if item.Name == Var.Name:
            return item.Value
    else:
        raise ValueError(f'Variable {Var.Name} not Found in {Link.__repr__()}')

def GetValueFromDerivatives(Link,Var):
    for item in Link.derivatives:
        if item.Var == Var.Name:
            return item.new
    else:
        raise ValueError(f'Variable {Var.Name} not Found in {Link.__repr__()}')

def GetConversion(Link):
    for ConvItem in Link.conversion:
        if ConvItem.Item =='Maximum Force':
            if ConvItem.Converged:
                Out = 'YES'
            else:
                Out = 'NO'
            return Out
    else:
        raise RuntimeError('No Maximum Force Conversion item found')

re_Cartesian = re.compile(r'Cartesian.Forces\:.*Max\s*([0-9|\.]*).RMS\s*[0-9|\.]*')
def GetCartesianForcesMax(Link):
    Match = re_Cartesian.findall(Link.text)
    if Match:
        return Match[0]


if __name__ == "__main__":
    args = parser.parse_args()
    File = Path(args.File)
    OutFile = args.OutFile
    if args.OutFile is not None:
        OutFile = os.path.abspath(args.OutFile)
        WriteOutput = write_2_file(OutFile)
    else:
        WriteOutput = print
    # Header to know which is each column
    msg_ini = '{: ^10}' + '\t{: ^10}'*5
    WriteOutput(msg_ini.format('Variable','Value','dE/dX','Conver','Car Forces',
                    'Geom Num'))    
    # Format for the numbers
    txt = '{: ^10}\t{: ^10}\t{: ^10}\t{: ^10}\t{: ^10}\t{: ^10}' # {: 03.9f}
    # Actual parsing
    if not File.exists(): #In the case of an empty filename, write an empty line
        raise ValueError(f'File {File} does not exist')
    with GaussianOutFile(File,[103,202,716]) as GOF:
        GOF.update()
    
    if args.scan: 
        Link = GOF.get_links(103)[0]
        for var in Link.parameters:
            if var.Derivative == 'Scan':
                ScanVar = var
                Value = var.Value
                break
        else:
            raise ValueError("No 'Scan' variable found in the file")
        VarName = ScanVar.Name
    else:
        Link = GOF.get_links(103)[0]
        for var in Link.parameters:
            if var.Name == args.Var:
                ScanVar = var
                Value = var.Value
                break
        else:
            raise ValueError(f"The variable '{args.Var}' is not an Internal Coordinate")
        VarName = args.Var

    geom_index = 0
    for l202,l716,l103 in zip(GOF[0][1:],GOF[0][2:],GOF[0][3:]):
        if (l202.number != 202 or l716.number != 716 or l103.number != 103):
            continue
        if l103.parameters and args.scan:
            Value = GetParameterValue(l103,ScanVar)
        elif not args.scan:
            Value = GetValueFromDerivatives(l103,ScanVar)
        dEdX = GetDeriv(l103,ScanVar)
        Converged = GetConversion(l103)
        CartForces = GetCartesianForcesMax(l716)
        WriteOutput(txt.format(VarName,Value,dEdX,Converged,CartForces,geom_index+1))

        # Update geom index
        geom_index += 1    

