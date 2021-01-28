#!/bin/usr/env python3

"""
Generates a gaussian input files from the last geometry of gaussian output files
or from the geometry of gaussian input files using a Header and/or Tail Files
which contain everything but the geometry and spin/charge
"""

import os
import argparse
from functools import partial

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry

__version__ = '0.0.0'

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('Files',help='Gaussian Input/Output Files',nargs='+')
parser.add_argument('-L','--ListFile',help="""When enabled instead of
                    considering the files provided as the gaussian output files
                    considers the file provided as a list of gaussian output
                    files""",action='store_true')
group_marker = parser.add_mutually_exclusive_group()
group_marker.add_argument('-m','--marker',help="""Text added to the filename to
                    differentiate the original .out file from the newly created
                    one. """,default='new')
group_marker.add_argument('--no-marker',help="""Files will be created with the
                    same file name as the provided files but with the '.in'
                    extension""", action='store_true',default=False,
                    dest='no_marker')
parser.add_argument('-O','--OutDir',help=""" Where to create the new files,
                    defaults to the current directory""",default='')
parser.add_argument('--Step',help=""" Will attempt to access the ith
                    optimization step of a gaussian output file to extract its
                    geometry on all files provided. 'initial geometry'='1'""",
                    default=None)
parser.add_argument('-H','--Header',help="""Header File that contains the queue,
                    memory as well as the gaussian calculation instructions
                    The output will start at the charge-spin line """,
                    default=None)
parser.add_argument('-T','--Tail',help="""Tail File that contains the extra
                    options, such as pseudopotentials, basis sets """,
                    default=None)
parser.add_argument('--version',version='script version {}'.format(__version__),
                    action='version')

Extension2Class = { 'in':'Input',
                   'com':'Input',
                   'gjf':'Input',
                   'log':'Output',
                   'out':'Output'}

FileStruct = '{Header}\n\n{Title}\n\n{charge} {spin}\n{Coords}\n\n{Tail}\n\n\n'

if __name__ == "__main__":
    args = parser.parse_args()

    if args.ListFile:
        with open(args.Files[0],'r') as F:
            Files = [line.strip() for line in F]
    else:
        Files = args.Files

    if args.Step is not None:
        args.Step = int(args.Step)

    if  args.no_marker:
        marker = ''
    else:
        marker = '_' + args.marker

    OutDir = os.path.abspath(args.OutDir)+'/{{}}{}.in'.format(marker)


    # Prepare Header
    if args.Header is None:
        Header = ''
    else:
        with open(os.path.abspath(args.Header),'r') as F:
            Aux = [line.strip() for line in F]
        while len(Aux)>=1 and not Aux[0]:
            _ = Aux.pop(0)
        while len(Aux)>=1 and not Aux[-1]:
            _ = Aux.pop(-1)
        Header = '\n'.join(Aux)
    # Prepare Tail
    if args.Tail is None:
        Tail = ''
    else:
        with open(os.path.abspath(args.Tail),'r') as F:
            Aux = [line.strip() for line in F]
        while len(Aux)>=1 and not Aux[0]:
            _ = Aux.pop(0)
        while len(Aux)>=1 and not Aux[-1]:
            _ = Aux.pop(-1)
        Tail = '\n'.join(Aux)



    for IFile in Files:
        print(IFile)
        InFilepath = os.path.abspath(IFile)
        Name = InFilepath.split('/')[-1].split('.')[0]
        extension = InFilepath.rsplit('.')[-1]
        FileClass = Extension2Class[extension]
        OutFile = OutDir.format(Name)
        if FileClass == 'Input':
            with GaussianInFile(InFilepath) as GIF:
                GIF.read()
            Geom = Geometry.from_Input(GIF)
            spin = GIF.spin
            charge = GIF.charge
        elif FileClass == 'Output':
            with GaussianOutFile(InFilepath,[1,101,202]) as GOF:
                GOF.update()
            L101 = GOF.GetLinks(101)[0]
            spin = L101.spin
            charge = L101.charge
            if args.Step is None:
                L202 = GOF.GetLinks(202)[-1]
            else:
                L202 = GOF[0].GetLinks(202)[args.Step-1]
            Geom = Geometry.from_L202(L202)
        else:
            msg = 'File {} was ignored due to unrecognized extension {}'
            print(msg.format(Name,extension))
        with open(OutFile,'w') as F:
            txt = FileStruct.format(Header=Header,Tail=Tail,spin=spin,
                                Coords=str(Geom),Title=Name+marker,
                                charge=charge)
            F.write(txt)
