"""
Takes a gaussian output file and a gaussian chk file and a list of Excited
States (by number) and creates a .in.sub file to generate only the cube files
of the orbitals involved in the transitions as well as a python script(s) to
generate the appropiate combination of the cubes.
"""
import argparse
import warnings
from pathlib import Path

from itertools import chain
from typing import TextIO

from pyssian import GaussianOutFile
from pyssian.linkjobparsers import Link914

# Utility variables and functions
SubHeader = """
#!/bin/bash
#$ -N {name}
#$ -cwd
#$ -pe {queue}_mpi {nprocs}
#$ -r n
#$ -masterq {queue}.q

#$ -o $JOB_NAME.o$JOB_ID
#$ -e $JOB_NAME.e$JOB_ID


####################################################
##########  CUBEGEN ENVIRONMENT VARS   #############
####################################################

. /etc/profile.d/modules.sh
module load gaussian/g09
export PARNODES=$NSLOTS
export PARA_ARCH=MPI

export TURBOTMPDIR=$PWD

####################################################
##########      CUBEGEN EXECUTION      #############
####################################################
formchk {chkfile} {fchkfile}
{commands}
""".strip()

Head = """
#!/bin/usr/env python3

from pyssian.classutils import Cube

""".lstrip()

Tail = """
CubeDiff = CubeAcceptor - CubeDonor
CubeDonor.write('ES_{0.number}_donor.cube')
CubeAcceptor.write('ES_{0.number}_acceptor.cube')
CubeDiff.write('ES_{0.number}_diff.cube')
""".strip().format

ALLOWEDQUEUES = {'unknown': {'nprocs':'1','queue':'unknown'},
                 '4': {'nprocs':'4','queue':'c4m8'},
                 'q4': {'nprocs':'4','queue':'cq4m4'},
                  '8': {'nprocs':'8','queue':'c8m24'},
                 '12': {'nprocs':'12','queue':'c12m24'},
                 '20': {'nprocs':'20','queue':'c20m48'},
                 '24': {'nprocs':'24','queue':'c24m128'},
                 '28': {'nprocs':'28','queue':'c28m128'},
                 '36': {'nprocs':'36','queue':'c36m192'} }

def calc_contributions(ES:Link914._ExcitedState,
                       ignoreReversed=True
                       ) -> tuple[dict[int,float],set[int],set[int],set[int]]:
    donors = []
    acceptors = []
    contributions = []
    for d,a,c,isreversed in ES.transitions:
        if (not isreversed) or (isreversed and not ignoreReversed):
            donors.append(d)
            acceptors.append(a)
            contributions.append(c)
    contributions = list(contributions)
    for i,contribution in enumerate(contributions):
        contributions[i] = 2*(contribution**2)
    orbitals = set(chain(donors,acceptors))
    orb2contr = {key:0.0 for key in orbitals}
    for d,a,c in zip(donors,acceptors,contributions):
        orb2contr[d] += c
        orb2contr[a] += c
    return orb2contr, set(donors), set(acceptors), orbitals

def prepare_square_sum(orb2contr:dict[int,float],
                       donors:list[int],
                       acceptors:list[int]) -> tuple[str]:
    keys = sorted(orb2contr.keys())
    ReadBlock = []
    ScaleBlock = []
    CubeDonor = []
    CubeAcceptor = []
    for orb in keys:
        ReadBlock.append(f"MO_{orb} = Cube.from_file('MO_{orb}.cube')")
        ScaleBlock.append(f"MO_{orb} = (MO_{orb} * {orb2contr[orb]})**2")
        if orb in donors:
            CubeDonor.append(f"MO_{orb}")
        if orb in acceptors:
            CubeAcceptor.append(f"MO_{orb}")
    ReadBlock_txt = '\n'.join(ReadBlock)
    ScaleBlock_txt = '\n'.join(ScaleBlock)
    CubeDonor_txt = f"CubeDonor = {' + '.join(CubeDonor)}"
    CubeAcceptor_txt = f"CubeAcceptor = {' + '.join(CubeAcceptor)}"
    return ReadBlock_txt, ScaleBlock_txt, CubeDonor_txt, CubeAcceptor_txt
def prepare_sum_square(orb2contr:dict[int,float],
                       donors:list[int],
                       acceptors:list[int]) -> tuple[str]:
    keys = sorted(orb2contr.keys())
    ReadBlock = []
    ScaleBlock = []
    CubeDonor = []
    CubeAcceptor = []
    for orb in keys:
        ReadBlock.append(f"MO_{orb} = Cube.from_file('MO_{orb}.cube')")
        ScaleBlock.append(f"MO_{orb} = MO_{orb} * {orb2contr[orb]}")
        if orb in donors:
            CubeDonor.append(f"MO_{orb}")
        if orb in acceptors:
            CubeAcceptor.append(f"MO_{orb}")
    ReadBlock_txt = '\n'.join(ReadBlock)
    ScaleBlock_txt = '\n'.join(ScaleBlock)
    CubeDonor_txt = f"CubeDonor = ({' + '.join(CubeDonor)})**2"
    CubeAcceptor_txt = f"CubeAcceptor = ({' + '.join(CubeAcceptor)})**2"
    return ReadBlock_txt, ScaleBlock_txt, CubeDonor_txt, CubeAcceptor_txt

def write2script(fd:TextIO, 
                 ES:Link914._ExcitedState, 
                 Head:str, 
                 Read:str, 
                 Scale:str, 
                 Donor:str, 
                 Acceptor:str,
                 Tail:str):
    Section = '{:#^60}'.format
    template = '\n'.join([Head,
                          Section(f' Excited State = {ES.number} '),
                          Section(' Read Block '),
                          Read,
                          Section(' Scale Block '),
                          Scale,
                          Section(' Cube Generations '),
                          Donor,
                          Acceptor,
                          Tail,
                          Section('')])
    fd.write(template)

def prepare_submit(header:str,
                   orbitals,
                   template_map:dict[str,str]):
    commands = []
    fchk = template_map['fchkfile']
    nprocs = template_map['nprocs']
    for orb in sorted(list(orbitals)):
         commands.append(f'cubegen {nprocs} MO={orb} {fchk} MO_{orb}.cube 0 h')
    template_map['commands'] = '\n'.join(commands)
    return header.format(**template_map)

# Parser and Main Definition
def prepare_map(name:str,
                queue:str='4',
                chk:str|None=None):

    if chk is None:
        chk = f'{name}.chk'

    final_map = dict(name=name,
                     queue=ALLOWEDQUEUES[queue]['queue'],
                     nprocs=ALLOWEDQUEUES[queue]['nprocs'],
                     chkfile=chk,
                     fchkfile=chk.rsplit('.')[0]+'.fchk',
                     commands='')
    
    return final_map

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('ifile',help='Gaussian Output File')
parser.add_argument('chk',help='Gaussian Checkpoint File')
parser.add_argument('-es','--excited-states',
                    dest='excited_states',
                    nargs='+',required=True,type=int,
                    help="list of numbers that correspond to the excited "
                    "states whose output is desired")
group_calc = parser.add_mutually_exclusive_group(required=True)
group_calc.add_argument('-sq','--squarefirst',
                        dest='do_squares_first', action='store_true',
                        help="Calculates the cubes squaring the cubes after "
                        "the scaling and before summing the donors and/or "
                        "acceptors")
group_calc.add_argument('-sum','--sumfirst',
                        dest='DoSquaresFirst', action='store_false',
                        help="Calculates the cubes squaring the cubes after "
                        "summing the donors, acceptors")
parser.add_argument('-m','--multiple',
                    dest='do_multiple',
                    default=False,action='store_true',
                    help="Generate one .py per each Electronic State selected, "
                    "otherwise a single .py with all the Electronic states is "
                    "generated")
parser.add_argument('-n','--name',
                    default='CubeGenerator',
                    help="name of the job for the queue system")
parser.add_argument('-q','--queue', 
                    choices=list(ALLOWEDQUEUES.keys()),
                    default='unknown',
                    help="name of the queue that will be used "
                    "which may be identified by the number of processors. "
                    "This is HPC specific")

def main(ifile:str|Path,
         chk:str,
         excited_states:list[int],
         do_squares_first:bool=False,
         do_multiple:bool=False,
         name:str='CubeGenerator',
         queue:str='unknown',
         ): 

    # Check arguments
    if len(set(excited_states)) != len(excited_states): 
        warnings.warn('Ignoring duplicated excited list in the provided list')
        excited_states = list(set(excited_states))

    template_map = prepare_map(name,
                               queue,
                               chk
    )

    with GaussianOutFile(ifile,[914,]) as GOF:
        GOF.read()
    l914 = GOF.get_links(914)[-1]

    total_orbitals = set()

    if do_multiple: # If one .py per each ES
        for ES in l914.excitedstates:
            if ES.number not in excited_states:
                continue
            
            orb2contr,donors,acceptors,orbitals = calc_contributions(ES)
            total_orbitals.update(orbitals)

            with open(f'ES_{ES.number}.py','w') as fd:

                if do_squares_first: # Square first then sum
                    items = prepare_square_sum(orb2contr,donors,acceptors)
                else:         # Sum first then square
                    items = prepare_sum_square(orb2contr,donors,acceptors)
                
                ReadB, ScaleB, Donor, Acceptor = items
                
                write2script(File=fd, 
                             ES=ES,
                             Head=Head,
                             Tail=Tail(ES),
                             Read=ReadB, 
                             Scale=ScaleB,
                             Donor=Donor,
                             Acceptor=Acceptor)
    else:
        with open(f'ES_all.py','w') as fd:

            fd.write(Head)
            for ES in l914.excitedstates:
                if ES.number not in excited_states:
                    continue
                
                orb2contr,donors,acceptors,orbitals = calc_contributions(ES)
                total_orbitals.update(set(orb2contr.keys()))
                
                if do_squares_first: # Square first then sum
                    items = prepare_square_sum(orb2contr,donors,acceptors)
                else:         # Sum first then square
                    items = prepare_sum_square(orb2contr,donors,acceptors)
                
                ReadB, ScaleB, Donor, Acceptor = items
                
                write2script(File=fd, 
                             ES=ES,
                             Head='',
                             Tail=Tail(ES),
                             Read=ReadB,
                             Scale=ScaleB,
                             Donor=Donor,
                             Acceptor=Acceptor)

    txt_submit = prepare_submit(SubHeader,total_orbitals,template_map)

    with open(f'{name}.in.sub','w') as File:
        File.write(txt_submit)
