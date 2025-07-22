import os
import subprocess
import yaml 
from pathlib import Path

MAINBRANCH = 'master'
BUILD_DIR = '../_docs'
PAGES_DIR = '../docs'
SPHINXSOURCE = './source'

def build_doc(version, tag):
    os.environ['current_version'] = version
    # checkout to the tagged commit
    subprocess.run(f'git checkout {tag}', shell=True)
    # Recover the latest conf.py and latest versions.yaml
    subprocess.run(f'git checkout {MAINBRANCH} -- {SPHINXSOURCE}/conf.py', shell=True)
    subprocess.run(f'git checkout {MAINBRANCH} -- {SPHINXSOURCE}/versions.yaml', shell=True)
    # build the docs
    subprocess.run("make html", shell=True)

def move_dir(src, dst):
    Path(dst).mkdir(exist_ok=True)
    if not src.endswith('/'):
        src = f'{src}/'
    subprocess.run(f'mv {src}* {dst}', shell=True)

os.environ['build_all_docs'] = str(True)
os.environ['pages_root'] = 'https://maserasgroup-repo.github.io/pyssian-utils' 

build_doc('latest', MAINBRANCH)
move_dir(f'{BUILD_DIR}/html/', f'{PAGES_DIR}/')

with open(f'{SPHINXSOURCE}/versions.yaml', 'r') as yaml_file:
  docs = yaml.safe_load(yaml_file)

for version, details in docs.items():
    tag = details.get('tag', '')
    build_doc(version, tag)
    move_dir(f'./{BUILD_DIR}/html/', f'../{PAGES_DIR}/{version}/')