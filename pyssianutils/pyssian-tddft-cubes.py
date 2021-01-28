#!/bin/usr/env python3

"""
Takes a gaussian output file and a gaussian chk file and a list of Excited
States (by number) and creates a .in.sub file to generate only the cube files
of the orbitals involved in the transitions as well as a python script(s) to
generate the appropiate combination of the cubes.
"""

import argparse
from itertools import chain

from pyssian import GaussianOutFile
# from pyssian.classutils import CubeFile

__version__ = '0.0.0'

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

def Calc_Contributions(ES,ignoreReversed=True):
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
    orb2contr = {key:0 for key in orbitals}
    for d,a,c in zip(donors,acceptors,contributions):
        orb2contr[d] += c
        orb2contr[a] += c
    return orb2contr, set(donors), set(acceptors), orbitals
def Prepare_square_sum(File,ES,orb2contr,donors,acceptors):
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
def Prepare_sum_square(File,ES,orb2contr,donors,acceptors):
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

def Write2Script(File, ES, Head, Read, Scale, Donor, Acceptor,Tail):
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
    File.write(template)

def Prepare_Submit(Header,orbitals,Filler):
    commands = []
    fchk = Filler['fchkfile']
    nprocs = Filler['nprocs']
    for orb in sorted(list(orbitals)):
         commands.append(f'cubegen {nprocs} MO={orb} {fchk} MO_{orb}.cube 0 h')
    Filler['commands'] = '\n'.join(commands)
    return Header.format(**Filler)

################### Parser ########################

def CreateParser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('File',help='Gaussian Output File')
    parser.add_argument('chk',help='Gaussian Checkpoint File')
    parser.add_argument('-es','--excitedstates',nargs='+',required=True,
                        help=""" list of numbers that correspond to the excited
                        states whose output is desired""")
    group_calc = parser.add_mutually_exclusive_group(required=True)
    group_calc.add_argument('-sq','--squarefirst',help="""Calculates the cubes
                        squaring the cubes after the scaling and before summing
                        the donors and/or acceptors""",
                        action='store_true',dest='DoSquaresFirst')
    group_calc.add_argument('-sum','--sumfirst',help="""Calculates the cubes
                        squaring the cubes after summing the donors, acceptors
                        """,action='store_false',dest='DoSquaresFirst')
    parser.add_argument('-m','--multiple',help="""Generate one .py per
                        each Electronic State selected, otherwise a single .py
                        with all the Electronic states is generated """,
                        default=False,action='store_true')
    parser.add_argument('-n','--name', help="""name of the job for the
                        queue system""",default='CubeGenerator')
    parser.add_argument('-q','--queue', help=""" nprocs of the queue where the
                        .in.sub will be run (q4 for cq4m4, 4 for c4m8)""",
                        default='12')
    parser.add_argument('--version',action='version',
                        version='script version {}'.format(__version__))
    return parser
def ParseArguments(args):
    Queues = { '4': {'nprocs':'4','queue':'c4m8'},
              'q4': {'nprocs':'4','queue':'cq4m4'},
               '8': {'nprocs':'8','queue':'c8m24'},
              '12': {'nprocs':'12','queue':'c12m24'},
              '20': {'nprocs':'20','queue':'c20m48'},
              '24': {'nprocs':'24','queue':'c24m128'},
              '28': {'nprocs':'28','queue':'c28m128'} }
    Filler = dict(name=args.name,
                  queue=Queues[args.queue]['queue'],
                  nprocs=Queues[args.queue]['nprocs'],
                  chkfile=args.chk,
                  fchkfile=args.chk.rsplit('.')[0]+'.fchk',
                  commands='')
    excitedstates = set(int(i) for i in args.excitedstates)
    return Filler, args.File, excitedstates, args.DoSquaresFirst, args.multiple

################### Main ##########################

parser = CreateParser()
args = parser.parse_args()
Filler, IFile, SelectedStates, DoSquaresFirst, DoMulti = ParseArguments(args)

with GaussianOutFile(IFile,[914,]) as GOF:
    GOF.read()
l914 = GOF.GetLinks(914)[-1]

total_orbitals = set()

if DoMulti: # If one .py per each ES
    for ES in l914.excitedstates:
        if ES.number not in SelectedStates:
            continue
        orb2contr,donors,acceptors,orbitals = Calc_Contributions(ES)
        total_orbitals.update(orbitals)
        with open(f'ES_{ES.number}.py','w') as File:
            if DoSquaresFirst: # Square first then sum
                items = Prepare_square_sum(File,ES,orb2contr,donors,acceptors)
            else:         # Sum first then square
                items = Prepare_sum_square(File,ES,orb2contr,donors,acceptors)
            ReadB, ScaleB, Donor, Acceptor = items
            Write2Script(File = File, ES = ES,
                         Head = Head, Tail = Tail(ES),
                         Read = ReadB, Scale = ScaleB,
                         Donor = Donor, Acceptor = Acceptor)
else:
    with open(f'ES_all.py','w') as File:
        File.write(Head)
        for ES in l914.excitedstates:
            if ES.number not in SelectedStates:
                continue
            orb2contr,donors,acceptors,orbitals = Calc_Contributions(ES)
            total_orbitals.update(set(orb2contr.keys()))
            if DoSquaresFirst: # Square first then sum
                items = Prepare_square_sum(File,ES,orb2contr,donors,acceptors)
            else:         # Sum first then square
                items = Prepare_sum_square(File,ES,orb2contr,donors,acceptors)
            ReadB, ScaleB, Donor, Acceptor = items
            Write2Script(File = File, ES = ES,
                         Head = '', Tail = Tail(ES),
                         Read = ReadB, Scale = ScaleB,
                         Donor = Donor, Acceptor = Acceptor)

txt_submit = Prepare_Submit(SubHeader,total_orbitals,Filler)
with open(f'{args.name}.in.sub','w') as File:
    File.write(txt_submit)
