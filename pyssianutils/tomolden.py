#!/bin/usr/env python3
"""
Generates a molden file from the provided gaussian files. To see more details on
the reference molden format see: https://www.theochem.ru.nl/molden/molden_format.html
"""

from pathlib import Path
import argparse
from typing import NamedTuple
import warnings
import re

from pyssian import GaussianOutFile, GaussianInFile
from pyssian.classutils import Geometry
from pyssian.chemistryutils import PeriodicTable

from .initialize import load_app_defaults

# typing imports
from pyssian.linkjobs import Link716, Link202, Link502, Link508, Link103

AU2A = 0.529177210544 # a.u. (Bohrs) to Angstroms factor

class MoldenBlock(NamedTuple): 
    title:str
    lines:list[str]
    option:None|str = None

    def __str__(self):
        if self.option is None: 
            return f"[{self.title}]\n{'\n'.join(self.lines)}"
        return f"[{self.title}] {self.option}\n{'\n'.join(self.lines)}"

class MoldenFile: 
    def __init__(self): 
        self.blocks = dict()

    def add(self,block:MoldenBlock,raise_err=False): 
        if block.title in self.blocks and not raise_err: 
            warnings.warn(f'overwriting the contents of block: {block.title}') 
        elif raise_err: 
            raise RuntimeError(f'overwriting the contents of block: {block.title}') 
        self.blocks[block.title] = block
    
    def read_geometry(self,geom:Geometry): 
        coordinates_a = []
        coordinates_au = []
        coordinates_atoms = []
        for i,(at,(x,y,z)) in enumerate(zip(geom.atoms,geom.coordinates)):
            try:
                at + 5
            except ValueError: # "at" is a string
                if sym[0].isdigit(): 
                    atn = int(at)
                    sym = PeriodicTable[atn]
                else: 
                    sym = at
                    atn = PeriodicTable[sym]
            else: 
                atn = at
                sym = PeriodicTable[atn]
            
            coordinates_atoms.append(f'{sym} {i+1} {atn} {x:.6f} {y:.6f} {z:.6f}')
            coordinates_a.append(f'{sym} {x:.6f} {y:.6f} {z:.6f}')
            coordinates_au.append(f'{sym} {x/AU2A:.6f} {y/AU2A:.6f} {z/AU2A:.6f}')
        
        self.add(MoldenBlock('ATOMS',coordinates_atoms,option='Angs'))
        self.add(MoldenBlock('FR-COORD',coordinates_au))
        n = len(coordinates_au)
        coordinates = [n,''] + coordinates_au
        m = self.blocks.get('GEOMETRIES',MoldenBlock('GEOMETRIES',[],option='XYZ'))
        m.lines.extend(coordinates)
        self.blocks['GEOMETRIES'] = m

    def add_geometry(self,geom:Geometry):
        coordinates_a = []
        for at,(x,y,z) in zip(geom.atoms,geom.coordinates):
            try:
                at + 5
            except ValueError: # "at" is a string
                if sym[0].isdigit(): 
                    atn = int(at)
                    sym = PeriodicTable[atn]
                else: 
                    sym = at
                    atn = PeriodicTable[sym]
            else: 
                atn = at
                sym = PeriodicTable[atn]
            coordinates_a.append(f'{sym} {x:.6f} {y:.6f} {z:.6f}')
        
        m = self.blocks.get('GEOMETRIES',MoldenBlock('GEOMETRIES',[],option='XYZ'))
        m.lines.extend(coordinates_a)
        self.blocks[m.title] = m
    
    def read_Link202(self,l202:Link202): 
        geom = Geometry.from_L202(l202)
        self.read_geometry(geom)
    
    def add_L202(self,l202:Link202): 
        geom = Geometry.from_L202(l202)
        self.add_geometry(geom)

    def read_Link716(self,l716:Link716):
        
        if hasattr(l716,'frequencies') and l716.frequencies: 
            frequencies = []
            intensities = []
            for f in l716.frequencies: 
                frequencies.append(f'{f.freq:.5f}')
                intensities.append(f'{f.IRint:.5f}')
            
            self.add(MoldenBlock('FREQ',frequencies))
            self.add(MoldenBlock('INT',intensities))

        if hasattr(l716,'freq_displacements') and l716.freq_displacements: 
            lines = []
            for i,f in enumerate(l716.freq_displacements):
                lines.append(f'vibration {i}')
                for x,y,z in f.xyz:
                    lines.append(f'{x:.6f} {y:.6f} {z:.6f}')
            self.add(MoldenBlock('FR-NORM-COORD',lines))


        return '\n'.join(lines)

    def read_scf_link(self,scflink:Link502|Link508): 
        energies = re.findall(r' E= (-?[0-9]+\.[0-9]+)',scflink.text)
        if not energies:
            return
        n = len(energies)
        lines = [f'scf-first 1 through {n}'] + energies
        self.add(MoldenBlock('SCFCONV',lines))

    def read_geom_convergence(self,energies:list[str],l103s:list[Link103],l202s:list[Link202]):
        lines = []
        lines.append('energy')
        lines.extend(energies)
        items = dict()
        items['max_forces'] = []
        items['rms_forces'] = []
        items['max_step'] = []
        items['rms_step'] = []
        name2key = dict()
        name2key['Maximum Force'] = 'max_forces'
        name2key['RMS Force'] = 'rms_forces'
        name2key['Maximum Displacement'] = 'max_step'
        name2key['RMS Displacement'] = 'rms_step'
        for l103 in l103s: 
            for converitem in l103.convergence: 
                key = name2key[converitem.Item] 
                items[key].append(converitem.Value)
        
        for key in ['max-force','rms-force','max-step','rms-step']: 
            lines.append(key)
            lines.extend(items[key])
        
        for l202 in l202s: 
            self.add_L202(l202)

    def write(self,filepath=None,allowed_sections=[]) -> str|None:
        blocks = []
        for block in self.blocks.values():
            if (not allowed_sections) or block.title in allowed_sections: 
                blocks.append(str(block)) 

        if filepath is None:
            return '\n'.join(blocks)+'\n'
        
        with open(filepath,'w') as F: 
            F.write('\n'.join(blocks)+'\n')
        return None

DEFAULTS = load_app_defaults()
GAUSSIAN_IN_SUFFIXES = DEFAULTS['common']['gaussian_in_suffixes'][1:-1].split(',')
GAUSSIAN_OUT_SUFFIXES = DEFAULTS['common']['gaussian_out_suffixes'][1:-1].split(',')
DEFAULT_OUTFILE = Path(DEFAULTS['toxyz']['outfile'])
# Utility Functions
def select_input_files(files,is_listfile=False): 
    if is_listfile:
        with open(files[0],'r') as F:
            inputfiles = [line.strip() for line in F]
    else:
        inputfiles = files
    return list(sorted(inputfiles))
def info_from_gau_output(filepath) -> MoldenFile: 
    
    with GaussianOutFile(filepath) as GOF:
        GOF.read()

    m = MoldenFile()

    has_l508 = bool(GOF.get_link(508))

    geoconv = []
    geoms = []
    geom_energies = []
    for internaljob in GOF.internaljobs: 
        if internaljob.type == 'Optimization':
            links = internaljob.get_links(103,202,502,508)
            for i,link in enumerate(links):
                if link.number == 103 and link.mode == 'Iteration': 
                    start = i
                    break
            else:
                continue
            links = links[start:]
            for i,link in enumerate(links): 
                if link.number == 103: 
                    geoconv.append(link)
                if link.number == 202: 
                    geoms.append(link) 
                if link.number == 502 and has_l508: 
                    if links[i+1].energy is None:
                        geom_energies.append(link.energy)
                    elif links[i+1].number == 508:
                        geom_energies.append(link[i+1].energy)
                    else:
                        raise RuntimeError('Unexpected link sequence found in gaussian file')
                    
    m.read_geom_convergence(geom_energies,geoconv,geoms)

    scflinks = GOF.get_links(502,508)
    scflink = scflinks[-1]
    if GOF[-1].type == 'Frequency Calculation':
        scflinks = GOF[-2].get_links(502,508)
        scflink = scflinks[-1]
    if scflink.energy is None: 
        scflink = scflinks[-2]
    m.read_scf_link(scflink)

    l202 = GOF.get_links(202)[-1]
    m.read_Link202(l202) # Must be done after the convergence

    if l716s:=GOF.get_links(716): 
        m.read_Link716(l716s[-1])

    return m
def info_from_gau_input(filepath) -> MoldenFile:
    with GaussianInFile(filepath) as GIF:
        GIF.read()
    geom = Geometry.from_Input(GIF)
    mfile = MoldenFile()
    mfile.read_geometry(geom)
    return mfile
def info_from_xyz(filepath) -> MoldenFile:
    geom = Geometry.from_xyz(filepath)
    mfile = MoldenFile()
    mfile.read_geometry(geom)
    return mfile
def parse_file(filepath) -> MoldenFile: 
    suffix = Path(filepath).suffix
    if suffix in GAUSSIAN_IN_SUFFIXES: 
        return info_from_gau_input(filepath)
    if suffix in GAUSSIAN_OUT_SUFFIXES:
        return info_from_gau_output(filepath)
    if suffix == '.xyz': 
        return info_from_xyz(filepath)
    raise NotImplementedError(f'files with suffix "{suffix}" cannot be interpreted')
def choose_allowed_sections(atoms:bool=False,
                            basis:bool=False,
                            orbitals:bool=False,
                            scfconver:bool=False,
                            geoconver:bool=False,
                            frequencies:bool=False,
                            allow_all:bool=False): 
    allowed_sections = []

    if allow_all or atoms: 
        allowed_sections.append('ATOMS')
    if allow_all or basis: 
        allowed_sections.extend(['GTO','STO'])
        warnings.warn('The option --basis is currently not implemented'
                      'If this could be usefull please contact the developer'
                      'as it should not be too difficult to do.')
    if allow_all or orbitals: 
        allowed_sections.append('MO')
        warnings.warn('The option --orbitals is included merely for completeness'
                      'there is currently no implementation as all information '
                      'of MO orbitals cannot be read from gaussian output files '
                      'directly')
    if allow_all or scfconver: 
        allowed_sections.append('SCFCONV')

    if allow_all or geoconver: 
        allowed_sections.extend(['GEOCONV','GEOMETRIES'])

    if allow_all or geoconver:
        allowed_sections.extend(['FREQ', 'FR-COORD', 'FR-NORM-COORD','INT'])

    return allowed_sections

# Parser and main definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Input/Output Files',nargs='+')
parser.add_argument('-l','--listfile',
                    dest='is_listfile',
                    action='store_true',default=False,
                    help="When enabled instead of considering the files "
                    "provided as the gaussian output files considers the file "
                    "provided as a list of gaussian output files")
parser.add_argument('-o','--outfile',
                    type=Path,
                    default=DEFAULT_OUTFILE,
                    help="Name of the xyz file with all the provided "
                    "geometries sorted by filename")
parser.add_argument('--atoms',
                    default=False, action='store_true',
                    help=("Will attempt to write the section"
                          "[ATOMS]"))
parser.add_argument('--basis',
                    default=False, action='store_true',
                    help=("Will attempt to write the sections"
                          "[GTO] or [STO]"))
parser.add_argument('--orbitals',
                    default=False, action='store_true',
                    help=("Will attempt to write the section"
                          "[MO]"))
parser.add_argument('--scfconver',
                    default=False, action='store_true',
                    help=("Will attempt to write the section"
                          "[SCFCONV]"))
parser.add_argument('--geoconver',
                    default=False, action='store_true',
                    help=("Will attempt to write the sections"
                          "[GEOCONV], [GEOMETRIES]"))
parser.add_argument('--frequencies',
                    default=False, action='store_true',
                    help=("Will attempt to write the sections"
                          "[FREQ], [FR-COORD], [FR-NORM-COORD] and [INT]"))
parser.add_argument('--all',
                    default=False,dest='allow_all', action='store_true',
                    help="Will write each molden file with all information it finds")

def main(files:list[str|Path],
         outfile:Path=DEFAULT_OUTFILE,
         is_listfile:bool=False,
         atoms:bool=False,
         basis:bool=False,
         orbitals:bool=False,
         scfconver:bool=False,
         geoconver:bool=False,
         frequencies:bool=False,
         allow_all:bool=False,
         ):
    
    allowed_sections = choose_allowed_sections(atoms=atoms,
                                               basis=basis,
                                               orbitals=orbitals,
                                               scfconver=scfconver,
                                               geoconver=geoconver,
                                               frequencies=frequencies,
                                               allow_all=allow_all)


    inputfiles = select_input_files(files,is_listfile)

    for ifile in inputfiles:
        infilepath = Path(ifile)
        ofile = infilepath.with_suffix('.molden').name
        print(f'{ifile} -> {ofile}')
        moldenfile = parse_file(infilepath)
        moldenfile.write(filepath=ofile,allowed_sections=allowed_sections)

