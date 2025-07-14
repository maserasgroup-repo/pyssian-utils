import shutil
import platform
import warnings
import tarfile
import importlib.resources

from pathlib import Path
from functools import cache

from .utils import register_main

# Typing imports
import argparse

# Utility Functions
@cache
def get_appdir() -> Path: 
    system = platform.system()
    if system == 'Linux': 
        return Path.home()/'.pyssianutils'
    raise NotImplementedError('Sorry I have only implemented this in Linux')
@cache
def get_resourcesdir() -> Path: 
    resourcesdir = importlib.resources.files(__package__)/'resources'
    return resourcesdir
    #raise NotImplementedError('If you are getting this error complain to the developer')
def pack_appdir(appdir:Path,target:Path=Path('default_appdata.tar')): 
    with tarfile.open(target,'w') as tar:
        tar.add(appdir/'defaults.ini','defaults.ini')
        tar.add(appdir/'templates/','templates/')
def unpack_appdir(ifile:Path,location:Path): 
    tar = tarfile.open(ifile)
    members = ['defaults.ini',]
    members += [m for m in tar.getmembers() if m.name.startswith("templates/")]  

    tar.extractall(path=location,
                   members=members,
                   filter='data')
    
    tar.close()
@cache
def check_initialization():
    appdir = get_appdir()
    if not appdir.exists(): 
        raise RuntimeError(f"{appdir} does not exist. Please ensure to run pyssianutils 'init'")

# Main APIs 
init_description = """
Should be run after a fresh installation. Creates the local 
directories where the user defaults and will application data will be stored
"""

init_parser = argparse.ArgumentParser(description=init_description)
init_parser.add_argument("--unpack",metavar='PACKAGE',dest='package',
                        help=""" package containing the configuration of a 
                        previous pyssianutils setup. Obtained through 
                        'pyssianutils pack myfile.pack' """,default=None)
init_parser.add_argument("--force",action='store_true',default=False,
                        help="""overwrite any previous pyssianutils 
                        application data if it already existed""")

def init_main(
              package:None|Path|str=None,
              force:bool=False
              ):
    appdir = get_appdir()

    if appdir.exists() and not force:
        raise RuntimeError('A previously existing app data directory was found')
    
    if appdir.exists(): 
        warnings.warn('overwriting previously existing pyssianutils app data')
        shutil.rmtree(appdir)
    
    appdir.mkdir(exist_ok=True)

    if package is not None: 
        unpack_appdir(package,appdir)
    else:
        resources = get_resourcesdir()
        shutil.copy(resources/'defaults.ini',appdir)
        shutil.copytree(resources/'templates',appdir/'templates')

clean_description = """
Removes the app data files and local directory where the pyssianutils data was 
stored. This is recommended before uninstalling the software
"""

clean_parser = argparse.ArgumentParser(description=clean_description)

def clean_main():

    check_initialization()

    appdir = get_appdir()
    shutil.rmtree(appdir)


