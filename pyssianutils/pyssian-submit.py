#!/bin/usr/env python3

"""
Checks all .in files in the current directory to generate a SubmitScript.sh
that properly sends them to their queues (Files with a matching .out file
are ignored as default). It checks in which queue they should go according
to the values of nprocshared and %mem. To use the generated script run in
kimikhome: 'chmod +x SubmitScript.sh; ./SubmitScript;'
"""

import os
import warnings
import argparse
from collections import namedtuple

__version__ = '0.0.0'

Queue = namedtuple('Queue','nprocesors memory'.split())
QUEUES = {4:Queue(4,8),8:Queue(8,24),
          12:Queue(12,24),20:Queue(20,48),
          24:Queue(24,128),28:Queue(28,128),
          'q4':Queue('q4',4)}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('software',choices=['g09','g16'],default='g09',
                    nargs='?')
parser.add_argument('--ascomments',help="""If enabled found .in files with a
                matching .out are included as comments""",action='store_true')
parser.add_argument('--norun',help="""If enabled the submit command will instead
                just generate the .in.sub file""",action='store_true')
parser.add_argument('--version',version=f'script version {__version__}',
                    action='version')


class NotFoundError(RuntimeError):
    pass

def InspectFile(Filename):
    with open(Filename,'r') as F:
        Text = [line.strip() for line in F]
    # Find nproc
    for line in Text:
        if 'nproc' in line:
            QueueNum = int(line.strip().split("=")[-1])
            break
    else:
        raise NotFoundError(f'nproc not found in {Filename}')
    # Find Mem
    for line in Text:
        if '%mem' in line:
            memory = int(line.strip().split("=")[-1][:-2])
            break
    else:
        warnings.warn(f'mem not found in {Filename}, ignoring "cq4m4 queue"')
        return Filename, QUEUES[QueueNum]
    if QueueNum == 4 and memory < 4000:
        queue = QUEUES['q4']
    else:
        queue = QUEUES[QueueNum]
    return Filename,queue
def PrepareScript(items,IgnoreOuts,TxtScript):
    Header = ['#!/bin/bash\n','# Automated Submit Script\n']
    Tail = []
    Output = []

    for line in Header:
        Output.append(line)

    for File,queue,IsFinished in items:
        if IsFinished:
            if not IgnoreOuts:
                Output.append('#'+TxtScript.format(GAU_Vers,queue,File))
        else:
            Output.append(TxtScript.format(GAU_Vers,queue,File))

    for line in Tail:
        Output.append(line)
    return Output


if __name__ == "__main__":
    args = parser.parse_args()
    SubmitText = 'qs {0}.c{1.nprocesors}m{1.memory} {2}'
    if args.norun:
        SubmitText = 'qs {0}.c{1.nprocesors}m{1.memory} 0 {2}'
    IgnoreOuts = not args.ascomments
    GAU_Vers = args.software
    Aux = []
    Files = os.listdir('.')
    Finished_Calculations = tuple([File for File in Files if File.endswith('.out')])
    for Item in Files:
        if Item.endswith('.in'):
            Name,queue = InspectFile(Item)
            if Name.rsplit('.')[0]+'.out' in Finished_Calculations:
                IsFinished = True
            else:
                IsFinished = False
            Aux.append((Name,queue,IsFinished))
    Out = PrepareScript(Aux,IgnoreOuts,SubmitText)
    with open('SubmitScript.sh','w') as F:
        F.write('\n'.join(Out))
