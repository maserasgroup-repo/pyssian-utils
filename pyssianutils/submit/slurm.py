"""
Generate slurm scripts for gaussian calculations.
"""
import shutil
import argparse
import re
import json
import string
from functools import cached_property
from collections.abc import Mapping
from pathlib import Path
import warnings

from pyssian import GaussianInFile

from ..initialize import get_appdir, load_app_defaults
from ..utils import DirectoryTree

from typing import Any

# Set up default values
DEFAULTS = load_app_defaults()
GAUSSIAN_IN_SUFFIX = DEFAULTS['common']['in_suffix']
GAUSSIAN_OUT_SUFFIX = DEFAULTS['common']['out_suffix']
DEFAULT_WALLTIME = DEFAULTS['submit.slurm']['walltime']
DEFAULT_MEMORY = DEFAULTS['submit.slurm']['memory']
DEFAULT_JOBNAME = DEFAULTS['submit.slurm']['jobname']
DEFAULT_GUESS =  DEFAULTS['submit.slurm'].getboolean('guess_default')
DEFAULT_INPLACE = DEFAULTS['submit.slurm'].getboolean('inplace_default')
SLURM_SUFFIX = DEFAULTS['submit.slurm']['slurm_suffix']

# Maybe I need to create the "CandidateTemplate" class, a simpler version to 
# avoid throwing errors during instantiation to simplify the checking process

# Actually, I may need a "TextTemplate" for the check as well as for an initial
# Inspection. This TextTemplate may have a raise_errors initialization option 
# somehow to allow its use for "analysis of the template" as well as for 
# "checking the correctness of the template"

class MissingDefault(KeyError): 
    pass
class ErrorDefault(ValueError):
    pass

class TemplateJson(object):
    def __init__(self,filepath:str|Path|None=None): 
        
        if filepath is None:
            self.defaults = dict()
            self.descriptions = None
            self.choices = dict()
            return
         
        with open(filepath,'r') as F: 
            data = json.loads(F.read())
        
        self.defaults = data.pop('defaults')
        if 'descriptions' in data: 
            self.descriptions = data.pop('descriptions')
        else:
            self.descriptions = None

        self.choices = data
        self._make_choices_mappable()
    
    def _make_choices_mappable(self):
        for k,v in self.choices.items(): 
            if not isinstance(v,Mapping):
                self.choices[k] = {i:i for i in v}

    def ensure_reasonable_defaults(self):
        for k,v in self.defaults.items(): 
            if k in self.choices: 
                if v not in self.choices[k]: 
                    raise ErrorDefault(f"default value {k}={v} is not within "
                                       f"the available choices {list(self.choices[k].keys())}. "
                                        "Please modify the json accordingly")

    @property
    def keywords(self): 
        return list(self.defaults.keys())

    def write(self,filepath:str|Path):
        if self.descriptions is not None: 
            data = dict(defaults=self.defaults,
                        descriptions=self.descriptions,
                        **self.choices)
        else:
            data = dict(defaults=self.defaults,
                        **self.choices)
        with open(filepath,'w') as F: 
            json.dump(data,F,indent=4, separators=(',', ': '))

    def update_parser(self,parser:argparse.ArgumentParser,ignore:list[str]|None=None): 
        if ignore is None: 
            ignore = set()
        for k in self.keywords:
            if k in ignore:
                continue
            default = self.defaults[k] # All keys MUST have a default

            description = None
            if self.descriptions is not None: 
                description = self.descriptions.get(k,None)
            
            valid_choices = self.choices.get(k,None)

            kwargs = dict()
            kwargs['default'] = default
            if description is not None: 
                kwargs['help'] = description
            if valid_choices is not None: 
                kwargs['choices'] = [c for c in valid_choices]
                # Ensure proper types based on the json
                # by creating a mapping between their text and the actual value
                mapper = {str(c):c for c in valid_choices}
                kwargs['type'] = mapper.get
            
            parser.add_argument(f'--{k}',**kwargs)

    @classmethod
    def basic_with_kwds(cls,*keywords):
        template = cls()
        template.choices['partition'] = dict()
        template.choices['partition']['default'] = dict()
        template.choices['partition']['default']['name'] = 'default'
        template.choices['partition']['default']['max_walltime'] = '00-00:00:00'
        template.choices['partition']['default']['mem_per_cpu'] = 2000 # MB
        template.choices['module'] = dict()
        template.choices['module']['default'] = dict()
        template.choices['module']['default']['exe'] = 'g16'
        template.choices['module']['default']['load'] = 'module0 gaussianmodule/version'
        template.choices['optionwithchoices'] = dict() 
        template.choices['optionwithchoices']['choice0'] = 'choice0value'
        template.choices['optionwithchoices']['choice1'] = 'choice1value'

        template.defaults['partition'] = 'default'
        template.defaults['module'] = 'default'
        template.defaults['optionwithchoices'] = 'choice0'

        template.descriptions = dict()
        template.descriptions['partition'] = 'partition name of the HPC'
        template.descriptions['module'] = 'alias for the executable and environment modules'
        template.descriptions['optionwithchoices'] = 'Description of the option'

        for keyword in keywords: 
            if keyword in ['partition','module','optionwithchoices']: 
                continue
            template.defaults[keyword] = 'default'
            template.descriptions[keyword] = f'description of {keyword}'
        
        return template

class TemplateText(object):
    """
    Base class for the TemplateSlurm that does not interact with a Json. Used 
    for file inspection before they are actually used.
    """
    _minimal_keywords = ['module','partition']
    # Keywords expected but set up based on the minimal or general DEFAULTS
    _special_keywords = ['gauexe','moduleload','in_suffix','out_suffix'] 

    def __init__(self,base_text:str):
        self._base_text = base_text
        self._memory_isfixed = False
        self._use_walltime_from_queue = True
        self.in_suffix = GAUSSIAN_IN_SUFFIX
        self.out_suffix = GAUSSIAN_OUT_SUFFIX
        
    @cached_property
    def expected_keywords(self): 
        keywords = set([k for _,k,_,_ in string.Formatter().parse(self._base_text) 
                        if k is not None]) # k is none in situations like "{{}}"
        keywords = list(sorted(keywords))
        return keywords
    
    @cached_property
    def keywords(self): 
        return [k for k in self.expected_keywords if k not in self._special_keywords]
    
    def check_minimal_keys(self,raise_error=False):
        for k in ['partition',] + self._special_keywords: 
            if k not in self.expected_keywords and raise_error:
                raise KeyError(f'Key "{k}" was not found in the template')
            elif k not in self.expected_keywords:
                warnings.warn(f'Key "{k}" was not found in the template')

    @classmethod
    def from_file(cls,
                  filepath:str|Path):
        
        with open(filepath,'r') as F: 
            base_text = F.read()
        return cls(base_text)

class TemplateSlurm(TemplateText):
    """
    Working class for the TemplateSlurm that interacts with a Json. Used 
    for actual file generation.
    """

    def __init__(self,
                 base_text:str,
                 choices:dict[str,dict[str,Any]],
                 defaults:dict[str,Any],
                 **kwargs):
        
        super().__init__(base_text)
        self.choices = choices
        self.defaults = defaults
        
        for attr,item in defaults.items():
            
            value = kwargs.get(attr,item)

            if attr == 'walltime': 
                self.walltime = value
                continue
            
            if attr == 'partition':
                self.partition = self.choices['partition'][value]
                continue

            if attr == 'module': 
                self.module = self.choices['module'][value]
                continue

            if attr in self.choices:
                try:
                    value = self.choices[attr][value]
                except KeyError:
                    raise ErrorDefault(f"{attr}={value} is not within the" 
                                       f"available choices {self.choices[attr].keys()}")
            self.__setattr__(attr,value)
        
        # checks
        if not hasattr(self,'partition'): 
            raise RuntimeError('A slurm template was created without a partition attribute')
        
        for key in self.expected_keywords:
            if key in self._special_keywords:
                continue
            if not hasattr(self,key):
                msg = (f'The slurm template created requires the keyword {key}'
                        'that has no default specified')
                raise MissingDefault(msg)
        
        if not hasattr(self,'cores'): 
            warnings.warn('The created slurm script does not have a "cores" attr')

    def __str__(self): 
        kwargs = self._as_format_map()
        return self._base_text.format_map(kwargs)

    def _as_format_map(self) -> dict: 
        kwargs = dict()
        for key in self.expected_keywords:
            
            match key:
                case 'moduleload': 
                    kwargs['moduleload'] = self.module['load']
                case 'gauexe': 
                    kwargs['gauexe'] = self.module['exe']
                case 'partition': 
                    kwargs['partition'] = self.partition['name']
                case _:
                    kwargs[key] = getattr(self,key)

        return kwargs

    def set_mem_from_cpu(self):
        """
        Will use the number of CPUs and the queue to figure out the requested 
        memory.
        """
        self._memory_isfixed = False
    def use_max_walltime(self): 
        self._use_walltime_from_queue = True

    @property
    def memory(self): 
        if self._memory_isfixed: 
            return self._memory
        
        mem_per_core = self.partition['mem_per_cpu']
        cores = int(self.cores)
        return f'{cores*mem_per_core}MB'
    @memory.setter
    def memory(self,other):
        # If a single value is assigned to the memory, assume the user wants 
        # a fixed value. 
        self._memory_isfixed = True
        self._memory = other

    @property
    def walltime(self): 
        if not self._use_walltime_from_queue: 
            return self._walltime
        return self.partition['max_walltime']
    @walltime.setter
    def walltime(self,other):
        # If a single value is assigned to the memory, assume the user wants 
        # a fixed value. 
        self._use_walltime_from_queue = False
        self._walltime = other

    def _guess_cores(self,text:str):
        """
        Guesses the values of the number of processors from a gaussian input 
        file contents.

        Parameters
        ----------
        text : str
            Contents of the Gaussian Input File as a str
        """
        matches = re.findall(r"\%([nN][pP]roc[sS]hared|[nN][pP]roc)=([0-9]+)",text)
        
        if matches:
            self.cores = int(matches[0][1])
        else:
            warnings.warn('Could not identify "cores"')
    def _guess_memory(self,text:str): 
        """
        Guesses the values of the total memory from a gaussian input file 
        contents.  

        Parameters
        ----------
        text : str
            Contents of the Gaussian Input File as a str
        """
        matches = re.findall(r"\%([mM]em)=([0-9]+[KMGT][BW])",text)
        if matches:
            self.memory = matches[0][1]
        else:
            warnings.warn(f'Could not identify "memory"')

    def guess_fromfile(self,
                       ifile:str|Path,
                       guesscores:bool=True,
                       guessmemory:bool=True) -> None:
        """
        Guesses the values of the number of processors, jobname, and memory
        requested from the gaussian input file provided, and sets them as the 
        values for the slurm template. If it does not find the values it prints 
        a warning and fails silently. 

        Parameters
        ----------
        ifile : str | Path
            filepath to the gaussian input file.
        guesscores : bool, optional
            if true it attempts to guess the number of cores from the file 
            contents, by default True
        guessmemory : bool, optional
            if true it attempts to guess the total memory from the file 
            contents, by default True
        """

        ifile = Path(ifile) # Cast to Path object if it is a str, otherwise copy
        if ifile.suffix != self.in_suffix: 
            self.in_suffix = ifile.suffix

        if hasattr(self,'jobname'):
            self.jobname = ifile.stem

        if not any([guesscores,guessmemory]):
            return 
        
        with open(ifile) as F: 
            txt = F.read()

        if guesscores: 
            self._guess_cores(txt)
        
        if guessmemory:
            self._guess_memory(txt)

    def copy_with(self,**kwargs):
        cls = self.__class__
        all_kwargs = self._as_format_map()
        all_kwargs.update(kwargs)
        for k in cls._special_keywords:
            all_kwargs.pop(k,None)
        all_kwargs['in_suffix'] = self.in_suffix
        all_kwargs['out_suffix'] = self.out_suffix
        return cls(self._base_text,
                   self.choices,
                   self.defaults,
                   **all_kwargs)

    @classmethod
    def from_file(cls,
                  filepath:str|Path,
                  jsontemplate:None|str|Path|TemplateJson=None,
                  **kwargs):
        
        with open(filepath,'r') as F: 
            base_text = F.read()
        
        if isinstance(jsontemplate,TemplateJson):
            pass
        elif jsontemplate is None: # Try to guess the path
            jsonpath = Path(filepath).with_suffix('.json')
            jsontemplate = TemplateJson(jsonpath)
        else: # Assume it is a path
            jsontemplate = TemplateJson(jsontemplate)
        
        choices = jsontemplate.choices
        defaults = jsontemplate.defaults
        return cls(base_text,choices,defaults,**kwargs)

# Attempt to read user defaults and templates
# Each key (template name) must have a tuple of (slurmpath,jsontemplate)
USERTEMPLATES:dict[str,tuple[Path,TemplateJson]] = dict()
appdir = get_appdir() 
for jsonfile in sorted((appdir/'templates'/'slurm').glob('*.json')): 
    name = jsonfile.stem
    templatefile = jsonfile.with_suffix('.txt') 
    if not templatefile.exists(): 
        continue
    else:
        USERTEMPLATES[name] = (templatefile,TemplateJson(jsonfile))

# Utility functions
def check_templates_agreement(filepath:str|Path,
                              json_t:TemplateJson,
                              raise_errors:bool=True):
    
    json_t.ensure_reasonable_defaults()

    both_agree = True
    try: 
        template = TemplateSlurm.from_file(filepath,json_t)
    except ErrorDefault as e: 
        both_agree = False
        msg = (str(e) + '\nplease check the provided json file')
        if raise_errors:
            raise ErrorDefault(msg)
        else: 
            warnings.warn(msg)
    except MissingDefault as e: 
        both_agree = False
        msg = (str(e) + '\nplease check the provided json file')
        if raise_errors:
            raise MissingDefault(msg)
        else:
            warnings.warn(msg)
    return both_agree
def inplace_transformations(filepath:Path,
                            template:TemplateSlurm,
                            inplace_mem:str|None,
                            inplace_nprocs:str|None
                            ): 
    assert inplace_mem in [None, 'add', 'rm']
    assert inplace_nprocs in [None, 'add', 'rm']

    if inplace_nprocs is None and inplace_mem is None: 
        return
    
    with GaussianInFile(filepath) as GIF: 
        GIF.read() 
    
    l0_kwds = {k.lower():k for k in GIF.preprocessing.keys()}

    if inplace_nprocs == 'rm': 
        nprocs_aliases = ['nprocs','nprocshared']
        for k in nprocs_aliases:
            if k in l0_kwds: 
                GIF.pop_l0_kwd(l0_kwds[k])
    
    if inplace_mem == 'rm': 
        mem_aliases = ['mem']
        for k in mem_aliases:
            if k in l0_kwds: 
                GIF.pop_l0_kwd(l0_kwds[k])

    if inplace_mem == 'add': 
        GIF.mem = template.memory

    if inplace_nprocs == 'add':
        try: 
            GIF.nprocs = template.cores
        except AttributeError:
            try: 
                GIF.nprocs = template.defaults['cores']
            except KeyError: 
                warnings.warn("refusing to modify in-place the gaussian input "
                              "file as no default 'cores' nor specific value "
                              "had been assigned to the template")
                return

    GIF.write(filepath=filepath)

# File(s) manipulation functions
def prepare_suffix(suffix:str): 
    if suffix.startswith('.'): 
        return suffix.rstrip()
    return f'.{suffix.strip()}'
def prepare_filepaths(filepaths:list[str|Path],
                      outdir:str|Path|None,
                      in_suffix:str,
                      out_suffix:str,
                      is_folder:bool,
                      is_listfile:bool,
                      is_inplace:bool=False,
                      do_overwrite:bool=False,
                      skip:bool=False,
                      ) -> tuple[list[Path]]:
    """
    This function encapsulates all the logic related to the generation of the
    final paths to the files, directory and subdirectory creation as well as
    paths to the template files.

    Parameters
    ----------
    folder : Namespace
        Output of the ArgumentParser.parse_args function

    Returns
    -------
    templates,geometries,newfiles
        A tuple of three lists of the same size. Templates represents the
        previously existing '.in' files. geometries the '.out' files provided
        by the user and newfiles the '.in' files that are to be created.

    """

    # Prepare folder structure
    if is_folder:
        folder = filepaths[0]
        if not is_inplace and outdir is None:
            outdir = Path.cwd()
        ifiles,newfiles = prepare_filepaths_folder(folder,
                                                   outdir,
                                                   in_suffix,
                                                   out_suffix)
    else:
        ifiles,newfiles = prepare_filepaths_nofolder(filepaths,
                                                     outdir,
                                                     out_suffix,
                                                     is_inplace,
                                                     is_listfile)
    if not do_overwrite:
        ifinal,nfinal = [],[]
        for ifile,nf in zip(ifiles,newfiles): 
            if nf.exists() and not skip:
                raise FileExistsError(f"{nf} would be overwritten, and maybe "
                                      "other files. If that is the desired action "
                                      "please enable the --overwrite flag")
            ifinal.append(ifile)
            nfinal.append(nf)
        
    return ifiles, newfiles
def prepare_filepaths_folder(folder:Path|str,
                             odir:str|Path|None,
                             in_suffix:str,
                             out_suffix:str) -> tuple[list[Path]]:
    """
    This function encapsulates the logic of the path generation when the
    --folder flag is enabled.
    """
    dir = DirectoryTree(folder,in_suffix,out_suffix)
    if odir is not None:
        odir = Path(odir)
        dir.set_newroot(odir)
        # create output folders
        print(f"Folders Created at '{odir}'")
        dir.create_folders()
    
    # Find the gaussian output files
    ifiles = list(dir.infiles)
    newfiles = [dir.newpath(path).with_suffix(out_suffix) for path in ifiles]

    return ifiles, newfiles
def prepare_filepaths_nofolder(files:list[str|Path],
                               odir:str|Path|None,
                               out_suffix:str,
                               is_inplace:bool=False,
                               is_listfile:bool=False,
                               ) -> tuple[list[Path]]:
    """
    This function encapsulates the logic of the path generation when the
    --folder flag is not enabled.
    """
    if not is_inplace:
        if odir is None:
            odir = Path.cwd()
        else:
            odir = Path(odir)
        odir.mkdir(parents=False,exist_ok=True)

    if is_listfile:
        with open(Path(files[0]),'r') as F:
            ifiles = [Path(line.strip()) for line in F if line.strip()]
    else:
        ifiles = [Path(f) for f in files]
    
    newfiles = [path.with_suffix(out_suffix) for path in ifiles]

    if not is_inplace:
        newfiles = [odir/g.name for g in newfiles]

    return ifiles, newfiles

# Parser Creation Utils
def add_template_common_options(parser:argparse.ArgumentParser,
                                walltime_default:str,
                                jobname_default:str,
                                defaul_memory:str,
                                has_cores:bool=False,
                                has_memory:bool=False): 
    parser.add_argument('inputfiles',
                        nargs='*',
                        help=f"Gaussian input files. If none is provided, it "
                        f"will create a '{jobname_default}{SLURM_SUFFIX}' to use as "
                        "template.")
    group_input = parser.add_mutually_exclusive_group()
    group_input.add_argument('-l','--listfile',
                            dest='is_listfile',
                            action='store_true',default=False,
                            help="When enabled instead of considering the "
                            "files provided as the gaussian output files "
                            "considers the file provided as a list of gaussian "
                            "output files")
    group_input.add_argument('-r','--folder',
                            dest='is_folder',
                            action='store_true',default=False,
                            help="Takes the folder and its subfolder "
                            "hierarchy and creates a new folder with the same "
                            "subfolder structure. Finds all the "
                            f"{GAUSSIAN_OUT_SUFFIX}, attempts to find their "
                            f"companion {GAUSSIAN_IN_SUFFIX} files and creates the "
                            "new inputs in their equivalent locations in the new "
                            "folder tree structure.")
    if DEFAULT_INPLACE: 
        parser.add_argument('-o','--outdir',
                            default=None,type=Path,
                            help="Where to create the new files, defaults "
                            "to the current directory")
        parser.set_defaults(is_inplace=True)
    else:
        group_output = parser.add_mutually_exclusive_group()
        group_output.add_argument('-o','--outdir',
                                default=None,type=Path,
                                help="Where to create the new files, defaults "
                                "to the current directory")
        group_output.add_argument('--inplace',
                                dest='is_inplace',
                                action='store_true',default=False,
                                help="Creates the new files in the same "
                                "locations as the files provided by the user")
    parser.add_argument('--suffix',
                        default=SLURM_SUFFIX,
                        help="suffix of the generated files")
    overwriting = parser.add_mutually_exclusive_group()
    overwriting.add_argument('-ow','--overwrite',
                             dest='do_overwrite',
                             action='store_true',default=False,
                             help="When creating the new files if a file with the "
                             "same name exists overwrites its contents. (The default "
                             "behaviour is to raise an error to notify the user before "
                             "overwriting).")
    overwriting.add_argument('--skip',
                             dest='skip',
                             action='store_true',default=False,
                             help="Skip the creation of slurm templates that "
                             "already exist")
    
    memory = parser.add_mutually_exclusive_group()
    memory.add_argument('--memory',
                        default=defaul_memory,
                        help="Memory requested for the calculation. If None is "
                        "provided it will attempt to guess it from the gaussian input file.") 
    memory.add_argument('--memory-per-cpu',
                        dest='memory_per_cpu',
                        default=False,action='store_true',
                        help="It will use the max memory per cpu of the partition")

    walltime = parser.add_mutually_exclusive_group()
    walltime.add_argument('--walltime',
                          default=walltime_default,
                          help="Fixed value of walltime in DD-HH:MM:SS format. "
                          "If none is provided it will use the default value of "
                          f"'{walltime_default}'",)
    walltime.add_argument('--use-max-walltime',
                          dest='use_max_walltime', 
                          default=False, action='store_true',
                          help="If enabled, use the selected partition's max walltime")
    if has_cores and DEFAULT_GUESS:
        parser.add_argument('--fix-cores',
                            dest='guess_cores',
                            action='store_false',default=True,
                            help="Do not attempt to guess the number of cores "
                            "from the gaussian input file")
    elif has_cores: 
        parser.add_argument('--guess-cores',
                            dest='guess_cores',
                            action='store_true',default=False,
                            help="attempt to guess the number of cores from "
                            "the gaussian input file")
    if has_memory and DEFAULT_GUESS:
        parser.add_argument('--fix-mem',
                            dest='guess_memory',
                            action='store_false',default=True,
                            help="Do not attempt to guess the memory "
                            "from the gaussian input file")
    elif has_memory:
        parser.add_argument('--guess-mem',
                            dest='guess_memory',
                            action='store_true',default=False,
                            help="attempt to guess the memory from "
                            "the gaussian input file")
    inplace = parser.add_argument_group(title='inplace modifications',
                                        description="Arguments to modify "
                                        "in-place the provided gaussian input files")

    memory = inplace.add_mutually_exclusive_group()
    memory.add_argument('--add-memory',
                        dest='inplace_mem',
                        action='store_const',const='add',default=None,
                        help='Add the "%%mem" Link0 option to the provided files')
    memory.add_argument('--rm-memory',
                        dest='inplace_mem',
                        action='store_const',const='rm',default=None,
                        help='Remove the "%%mem" Link0 option of the provided files')

    nprocs = inplace.add_mutually_exclusive_group()
    nprocs.add_argument('--add-nprocs',
                        dest='inplace_nprocs',
                        action='store_const',const='add',default=None,
                        help='Add the "%%nprocshared" Link0 option to the provided files')
    nprocs.add_argument('--rm-nprocs',
                        dest='inplace_nprocs',
                        action='store_const',const='rm',default=None,
                        help='Remove the "%%nprocshared" Link0 option of the provided files')

# Define Parser and Main
parser = argparse.ArgumentParser(description=__doc__)
parser.set_defaults(slurm_mode=None)
subparsers = parser.add_subparsers(help='sub-command help',dest='slurm_mode')

# Templatenames should each be a parser
for name,(slurm_t,json_t) in USERTEMPLATES.items():
    subparser = subparsers.add_parser(name,help=f'Generate slurm files using template "{name}"')
    # The following defaults should technically never be used except when 
    # the setup is not correctly configured and as this code is executed before
    # actually running the app it is better if it does not raise KeyErrors
    walltime_default = json_t.defaults.get('walltime',DEFAULT_WALLTIME)
    memory_default = json_t.defaults.get('memory',DEFAULT_MEMORY)
    has_cores = 'cores' in json_t.defaults
    add_template_common_options(subparser,
                                walltime_default,
                                DEFAULT_JOBNAME,
                                memory_default,
                                has_cores,
                                has_memory=True)
    json_t.update_parser(subparser,
                         ignore=['walltime','memory','in_suffix','out_suffix'])

def _main_generate(templatename:str,
                   inputfiles:list[Path],
                   memory:str|None,
                   outdir:str|Path|None=None,
                   is_folder:bool=False,
                   is_listfile:bool=False,
                   is_inplace:bool=False,
                   do_overwrite:bool=False,
                   skip:bool=False,
                   suffix:str=SLURM_SUFFIX,
                   memory_per_cpu:bool=False,
                   use_max_walltime:bool=False,
                   guess_cores:bool=False,
                   guess_memory:bool=False,
                   inplace_mem:None|str=None,
                   inplace_nprocs:None|str=None,
                   **kwargs):

    slurmpath,json_t = USERTEMPLATES[templatename]
    json_t.ensure_reasonable_defaults()

    suffix = prepare_suffix(suffix)

    base_template = TemplateSlurm.from_file(slurmpath,
                                            json_t,
                                            **kwargs)
    updated_params = dict(**kwargs)
    if not guess_memory and not memory_per_cpu: 
        updated_params['memory'] = memory
    elif memory_per_cpu: 
        base_template.set_mem_from_cpu() 
    if use_max_walltime:
        base_template.use_max_walltime()

    if len(inputfiles) == 0: 
        print(f'Creating base template: {base_template.jobname}{suffix}')
        with open(f'{base_template.jobname}{suffix}','w') as F: 
            F.write(str(base_template))
        return 

    ifiles,newfiles = prepare_filepaths(inputfiles,
                                        outdir,
                                        GAUSSIAN_IN_SUFFIX,
                                        suffix,
                                        is_folder,
                                        is_listfile,
                                        is_inplace,
                                        do_overwrite,
                                        skip)
                                        
    for ifile,newfile in zip(ifiles,newfiles):
        print(f'Creating file {newfile}')
        template = base_template.copy_with(**updated_params)
        template.guess_fromfile(ifile,
                                guesscores=guess_cores,
                                guessmemory=guess_memory)
        with open(newfile,'w') as F: 
            F.write(str(template))
        
        if inplace_mem is not None or inplace_nprocs is not None: 
            inplace_transformations(ifile,template,inplace_mem,inplace_nprocs)

check = subparsers.add_parser('check-template',
                              help="""Inspects a template to display the keywords
                              in present, and ensures that it contains the 
                              minimal keywords""")
check.add_argument('filepath',
                   type=Path,
                   help='path to the template that will be inspected')
check.add_argument('--json',
                   dest='jsonfile',
                   type=Path,default=None,
                   help="If provided and it is an existing file, it will check "
                   "the agreement between the template and the json. If it is a "
                   "non-existing file it will create a basic json file containing "
                   "the minimal information to be filled by the user with the "
                   "specifics of the template that was inspected. If not provided "
                   "it will only check the template.")
def _main_check_template(filepath:Path,
                         jsonfile:Path|None):
    # Create a "TextTemplate" instance from filepath
    template = TemplateText.from_file(filepath)
    
    print(f'Keywords found in template {filepath.name}:')
    # Display the keywords found in the template
    for key in template.expected_keywords: 
        print(f'   * {key}')

    template.check_minimal_keys(raise_error=False) 

    # If the jsonfile is enabled
    if jsonfile is None: 
        return
    elif jsonfile.exists(): 
        json_t = TemplateJson(jsonfile)
        both_agree = check_templates_agreement(filepath,json_t,raise_errors=False)
        if both_agree: 
            print('Templates are compatible')
        else:
            print('Templates are not compatible. Please check the json default values')
    else:
        json_t = TemplateJson.basic_with_kwds(*template.keywords)
        json_t.write(jsonfile)

addtemplate = subparsers.add_parser('add-template',
                                    help="Adds a template to the user templates")
addtemplate.add_argument('filepath',
                         type=Path,
                         help='path to the template that will be added')
addtemplate.add_argument('name',
                         nargs='?',default=None,
                         help="Name under which the template will be stored. "
                         "If none is provided it will be based on the stem of the "
                         "file, e.g. myfile.txt would be saved as 'myfile' ")
addtemplate.add_argument('--json',
                         dest='jsonfile',
                         default=None,type=Path,
                         help="If provided instead of adding a basic json file "
                         "that needs to be modified it will assume that the "
                         "provided json is correct and will store it with the "
                         "template.")
def _main_add_template(filepath:Path,
                       name:str|None,
                       jsonfile:Path|None):
    # Attempt to instantiate the template (TextTemplate class)
    template = TemplateText.from_file(filepath)
    try:
        template.check_minimal_keys(raise_error=True) 
    except KeyError as e: 
        raise KeyError(str(e) + 
                       ' Consider running "pyssianutils submit slurm check-template" first')

    if jsonfile is not None: 
        check_templates_agreement(filepath,TemplateJson(jsonfile),raise_errors=True)

    # if no error occurs, store them appropiatedly
    appdir = get_appdir()
    if name is None: 
        name = filepath.stem
    shutil.copy(filepath,appdir/'templates'/'slurm'/f'{name}.txt')
    print(f"Successfully added {appdir/'templates'/'slurm'/f'{name}.txt'}")
    if jsonfile is not None:
        shutil.copy(jsonfile,appdir/'templates'/'slurm'/f'{name}.json')
        print(f"Successfully added {appdir/'templates'/'slurm'/f'{name}.json'}")
    else:
        jsonpath = appdir/'templates'/'slurm'/f'{name}.json'
        TemplateJson.basic_with_kwds(*template.keywords).write(jsonpath)
        print(f"a template json for the just added template was created at {jsonpath}")
        print(f"Please update its contents before attempting to use the template")

rmtemplate = subparsers.add_parser('rm-template',
                                   help="removes a template from the user templates")
rmtemplate.add_argument('name',
                        help="Name under which the template is stored.")
def _main_rm_template(name:str|None):
    if name is None: 
        _display_template_names()
        return 
    
    appdir = get_appdir()
    slurmpath = appdir/'templates'/'slurm'
    # Ensure it exists
    if name not in USERTEMPLATES:
        raise ValueError(f"Template '{name}' is not detected by pyssianutils" 
                         "as a template. Please check available templates by"
                         "with 'pyssianutils submit slurm' or manually remove"
                         f"the file located at {slurmpath}") 
    
    (slurmpath/f'{name}.txt').unlink(missing_ok=True)
    print(f"successfully removed {slurmpath/f'{name}.txt'}")
    (slurmpath/f'{name}.json').unlink(missing_ok=True)
    print(f"successfully removed {slurmpath/f'{name}.json'}")

def _display_template_names():
    print('Available slurm templates:')
    for key in USERTEMPLATES: 
        print(f'    {key}')

def main(
        slurm_mode:str,
        **kwargs
        ):
    match slurm_mode: 
        case None: # Display available slurm template names
            _display_template_names()
        case 'check-template': 
            _main_check_template(**kwargs)
        case 'add-template': 
            _main_add_template(**kwargs)
        case 'rm-template': 
            _main_rm_template(**kwargs)
        case _:
            if slurm_mode not in USERTEMPLATES: 
                raise RuntimeError(f"Slurm template name {slurm_mode} is not"
                                   "defined for the current user")
            _main_generate(templatename=slurm_mode,
                           **kwargs)