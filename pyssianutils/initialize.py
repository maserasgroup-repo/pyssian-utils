"""
The initialize module defines all the parser commands (and their behaviour)
related with the pyssianutils data and provides methods for easy access to said
resources.
"""
import shutil
import platformdirs
import platform
import warnings
import tarfile
import configparser
import importlib.resources

from pathlib import Path
from functools import cache

# Typing imports
import argparse

PKGDEFAULTNAME = 'pyssianutils_appdata'

# Utility Functions
@cache
def get_appdir(use_home:bool=True) -> Path:
    """
    If a pyssianutils app data exists return it. Otherwise return a suitable 
    path for its creation.

    Parameters
    ----------
    use_home : bool
        For Linux, to facilitate the access to the configuration files or 
        the templates stored in the app data a True value of this parameter 
        will favor returning a $HOME/.pyssianutils location instead of the 
        XDG recommended one in $HOME/.local/shared/pyssianutils.

    Returns
    -------
    Path
        path to the app data folder if it exists. Otherwise returns a suitable
        path for it.

    Raises
    ------
    RuntimeError
        Two pyssianutils appdata directories were found
    """
    system = platform.system()
    if system == 'Linux':
        home_path = Path.home()/'.pyssianutils'
        xdg_path = Path(platformdirs.user_data_dir(str(__package__)))
        if home_path.exists() and xdg_path.exists():
            raise RuntimeError(f"""Two pyssianutils app data directories have 
                               been found. Please manually remove one of them:
                               {home_path} and {xdg_path}""")
        elif home_path.exists():
            return home_path
        elif xdg_path.exists():
            return xdg_path
        elif use_home:
            return home_path
    return Path(platformdirs.user_data_dir(str(__package__)))

@cache
def get_resourcesdir() -> Path:
    """
    Returns the path to the resources as they were installed. Files in this 
    directory should not be changed and are removed upon pip uninstall.  

    Returns
    -------
    Path
        path to the resources folder.
    """
    resourcesdir = importlib.resources.files(__package__)/'resources'
    return resourcesdir
def pack_appdir(appdir:Path,target:Path=Path(f'{PKGDEFAULTNAME}.tar')):
    print(f'Creating {target}')
    with tarfile.open(target,'w') as tar:
        tar.add(appdir/'defaults.ini','defaults.ini')
        tar.add(appdir/'templates/','templates/')
    print('    finished')
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
    """
    Ensures that pyssianutils was initialized. If it was not it errors.

    Raises
    ------
    RuntimeError
        pyssianutils was not initialized
    """
    appdir = get_appdir()
    if not appdir.exists(): 
        raise RuntimeError(f"{appdir} does not exist. Please ensure to run pyssianutils 'init'")
@cache
def load_app_defaults() -> configparser.ConfigParser:
    """
    Looks for the configuration files in the resources and in the user's app 
    directory, loads and returns them

    Returns
    -------
    configparser.ConfigParser
        configuration defaults of pyssianutils for a given user
    """
    defaults = configparser.ConfigParser()
    # Order is important as we want to override any packaged defaults with the
    # User's defaults
    defaults.read([get_resourcesdir()/'defaults.ini',
                   get_appdir()/'defaults.ini'])
    return defaults

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
if platform.system() == 'Linux': 
    init_parser.add_argument('--xdg-default-appdir',
                             dest='use_home',default=True,action='store_false',
                             help="""If enabled it will store pyssianutils data
                             at $HOME/.local/share/pyssianutils instead of 
                             at $HOME/.pyssianutils""")
else:
    init_parser.set_defaults(use_home=False)

def init_main(
              package:None|Path|str=None,
              force:bool=False,
              use_home:bool=False,
              ):
    appdir = get_appdir(use_home)

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

    appdir = get_appdir()
    try:
        shutil.rmtree(appdir)
    except FileNotFoundError: 
        warnings.warn(f'pyssianutils installation at {appdir} was not found so nothing to clean')

pack_description = """
Packages the user app data into a tar file that can be used by pyssianutils init
to simplify exporting the user defaults and templates to a new machine.
"""
pack_parser = argparse.ArgumentParser(description=pack_description)
pack_parser.add_argument('name',nargs='?',
                         default=PKGDEFAULTNAME,
                         help="""name of the file that will contain the user's configuration""")
pack_parser.add_argument('--outputdir','-O',
                         default=Path.cwd(),
                         help="""Directory where the file will be created. 
                         Defaults to the CWD""")
def pack_main(name:str,
              outputdir:Path):

    appdir = get_appdir()
    pack_appdir(appdir,target=outputdir/f'{name}.tar')

defaults_description = """
Allows the display of default values and their modification from the command line.
"""

defaults_parser = argparse.ArgumentParser(description=defaults_description)
defaults_subparsers = defaults_parser.add_subparsers(help='sub-command help',dest='subcommand')
show_subparser = defaults_subparsers.add_parser('show',
                                                help="""Prints in the console the
                                                avaliable/selected default parameters
                                                and/or sections in which those 
                                                parameters are grouped""")
show_subparser.add_argument('parameter',
                            nargs='?', default=None,
                            help="""name of the parameter whose value should 
                            be displayed. 'all' will show all parameters.""")
show_subparser.add_argument('--section',
                            default=None,
                            help="""Allows to filter the parameters for a 
                            single section. If no section, no parameter 
                            and nbo other flag is requested. 
                            A list of the sections available will be 
                            displayed.""")
show_subparser.add_argument('--all',
                            dest='show_all',
                            default=False,action='store_true',
                            help='show all parameters')
show_subparser.add_argument('--path',
                            dest='show_path',
                            default=False,action='store_true',
                            help="shows the path to the 'defaults.ini' file")
set_subparser = defaults_subparsers.add_parser('set',
                                               help="sets/changes the value of a default")
set_subparser.add_argument('parameter',
                            help="name of the parameter whose value should set")
set_subparser.add_argument('value',
                            help="value to set in the parameter")
set_subparser.add_argument('--section',
                            default=None,
                            help="""Section of the parameter. If none provided
                            it will attempt to guess it. From guessing it if 
                            there is only one parameter with the provided name
                            it will set the new value. Otherwise it will refuse 
                            and will show the sections containing that parameter 
                            name""")
set_subparser.add_argument('--all',
                            dest='update_all',
                            default=False,action='store_true',
                            help="""If enabled it forces the update on all 
                            parameters with the same name""")

def defaults_main(subcommand:str,
                 **kwargs):
    
    if subcommand == 'show':
        _defaults_show(**kwargs)
    
    if subcommand == 'set': 
        _defaults_set(**kwargs)

def _defaults_show(parameter:str|None,
                  section:str|None,
                  show_all:bool=False,
                  show_path:bool=False):
    if show_path: 
        app_defaults = get_resourcesdir()/'defaults.ini'
        defaults_path = get_appdir()/'defaults.ini'
        print(f'packaged defaults ( do not modify): {app_defaults}')
        if defaults_path.exists():
            print(f'    user defaults (free to modify): {defaults_path}')
        else:
            print(f'    user defaults (free to modify): Not Found, please run "pyssianutils init"')
        return
    
    if parameter is not None and show_all:
        raise argparse.ArgumentError('specifying a parameter is not compatible with the --all flag')
    
    if parameter is None and section is not None and not show_all:
        raise argparse.ArgumentError('specifying only a --section also requires the --all flag')
    
    defaults = load_app_defaults()
    if parameter is None and section is None and show_all:
        for s in defaults.sections():
            print(f'[{s}]')
            for k in defaults.options(s):
                print(f'    {k} = {defaults[s][k]}')
    elif parameter is None and section is None: 
        for s in defaults.sections():
            print(f'[{s}]')
    elif parameter is None and show_all:
        if section not in defaults.sections():
            error_msg = f"section={section} not in defaults. " \
                "Please run 'pyssian default show  """.strip()
            raise ValueError(error_msg)

        for k in defaults.options(section):
            print(f'{k} = {defaults[section][k]}')
    elif parameter is not None and section is None:
        for s in defaults.sections():
            if parameter in defaults.options(s):
                print(f'[{s}]')
                print(f'    {parameter} = {defaults[s][parameter]}')
    elif parameter is None and section is not None:
        if section not in defaults.sections():
            error_msg = f"subsection={section} not in defaults. " \
                "Please run 'pyssian default show  """.strip()
            raise ValueError(error_msg)
        print(f'[{section}]')
        for k in defaults.options(s):
            print(f'    {k} = {defaults[s][k]}')

def _defaults_set(parameter:str,
                 value:str,
                 section:str|None=None,
                 update_all:bool=False):
    
    appdir = get_appdir()
    defaults_filepath = appdir/'defaults.ini'
    
    defaults = load_app_defaults()

    matches = []
    if section is None:
        for s in defaults.sections():
            if parameter in defaults.options(s): 
                matches.append((s,parameter))
    else: 
        if parameter in defaults.options(section): 
            matches.append((section,parameter))
    
    if len(matches) < 0: 
        raise ValueError(f'parameter={parameter} does not exist')
    elif len(matches) > 1 and not update_all:
        print(f'parameter={parameter} is present in more than one section:')
        print('\n'.join([f'    {s}' for s,_ in matches]))
        warnings.warn('The program cowardly refused to update the defaults values')
    elif len(matches) > 1: 
        for s,p in matches:
            print(f'    setting [{s}][{p}] = {value}')
            defaults[s][p] = value
    else:
        s,p = matches[0]
        print(f'    setting [{s}][{p}] = {value}')
        defaults[s][p] = value

    print('storing new defaults')
    with open(defaults_filepath,'w') as F: 
        defaults.write(F)

