*************************
Creating a slurm template
*************************

We tried to simplify as much as we could the process of generating a template 
that can be used by pyssianutils to generate slurm files. In this example we 
will show the steps of how the already packaged slurm script "example" was 
included.

.. contents::
   :local:

1. Find/create a script that already works
------------------------------------------

For this task we do not need something generic, we need something that we can 
test with a dummy gaussian calculation, that we can submit quickly and see 
if there are any errors in the submission or not. If the HPC has documentation 
available for their users they typically have working slurm scripts for 
running gaussian calculations, but sometimes you have to make your own. We 
already had some experience so we started from the following one: 

.. code-block:: bash
   :caption: test.slurm

   #!/bin/bash
   #SBATCH -c 2
   #SBATCH --mem 4GB
   #SBATCH -t 00:10:00
   #SBATCH --partition generic
   #SBATCH --job-name test
   #SBATCH -o %x.slurm.o%j
   #SBATCH -e %x.slurm.e%j
   
   #Set up gaussian environment
   module load gaussian/g16
   
   export GAUSS_SCRDIR=${SCRATCHGLOBAL}/job_${SLURM_JOBID}
   mkdir -p ${GAUSS_SCRDIR}; 
   
   job_name=test;
   
   g16 < ${job_name}.com > ${job_name}.log
   
   rm -r ${GAUSS_SCRDIR};

2. Duplicate any already existing brakets
-----------------------------------------

We are going to profit of python's format strings for the template creation, 
so in order to ensure that the curly brakets that are already in the slurm script
are retained we need to duplicate them: 

.. code-block:: none
   :caption: Duplicating Curly Brakets

   #!/bin/bash
   #SBATCH -c 2
   #SBATCH --mem 4GB
   #SBATCH -t 00:10:00
   #SBATCH --partition generic
   #SBATCH --job-name test
   #SBATCH -o %x.slurm.o%j
   #SBATCH -e %x.slurm.e%j
   
   #Set up gaussian environment
   module load gaussian/g16
   
   export GAUSS_SCRDIR=${{SCRATCHGLOBAL}}/job_${{SLURM_JOBID}}
   mkdir -p ${{GAUSS_SCRDIR}}; 
   
   job_name=test;
   
   g16 < ${{job_name}}.com > ${{job_name}}.log
   
   rm -r ${{GAUSS_SCRDIR}};


3. Identify the parts that you may want to change
-------------------------------------------------

Typically we want to be able to change the number of **cores**, **memory** and
**partition**. Also, if there are various versions of gaussian in the HPC, we 
may be interested in being able to switch those also which involves changing the
:code:`module load gaussian/g16` line as well as maybe changing the name of the 
gaussian executable :code:`g16`. Finally, the name of the job would also be 
interesting. 

4. Update the special parameters
--------------------------------

We will start by replacing all parameters by :code:`{parameter}`, however
from the previously identified parameters, pyssian only gives a special treatment
to the partition (as it becomes a required keyword for the template) and the 
module loading and the executable. These require a special name so we will first
update those: 

.. code-block:: none
   :caption: Special Parameters update

   #!/bin/bash
   #SBATCH -c 2
   #SBATCH --mem 4GB
   #SBATCH -t 00:10:00
   #SBATCH --partition {partition}
   #SBATCH --job-name test
   #SBATCH -o %x.slurm.o%j
   #SBATCH -e %x.slurm.e%j
   
   #Set up gaussian environment
   module load {moduleload}
   
   export GAUSS_SCRDIR=${{SCRATCHGLOBAL}}/job_${{SLURM_JOBID}}
   mkdir -p ${{GAUSS_SCRDIR}}; 
   
   job_name=test;
   
   {gauexe} < ${{job_name}}.com > ${{job_name}}.log
   
   rm -r ${{GAUSS_SCRDIR}};

Next we can replace the remaining ones:

.. code-block:: none
   :caption: Other Parameters update

   #!/bin/bash
   #SBATCH -c {cores}
   #SBATCH --mem {memory}
   #SBATCH -t {walltime}
   #SBATCH --partition {partition}
   #SBATCH --job-name {jobname}
   #SBATCH -o %x.slurm.o%j
   #SBATCH -e %x.slurm.e%j
   
   #Set up gaussian environment
   module load {moduleload}
   
   export GAUSS_SCRDIR=${{SCRATCHGLOBAL}}/job_${{SLURM_JOBID}}
   mkdir -p ${{GAUSS_SCRDIR}}; 
   
   job_name={jobname};
   
   {gauexe} < ${{job_name}}.com > ${{job_name}}.log
   
   rm -r ${{GAUSS_SCRDIR}};

5. check the template
---------------------

Now we will proceed to save the file and check if the contents are correct and 
if all the parameters are detected. Assuming we save the file with the name 
:code:`newtemplate.txt` we would run: 

.. code:: shell-session

   $ pyssianutils slurm check-template newtemplate.txt
      Keywords found in template newtemp.txt:
      * cores
      * gauexe
      * jobname
      * memory
      * moduleload
      * partition
      * walltime
   /home/user/somewhere/pyssianutils/submit/slurm.py:186: UserWarning:
   
   Key "in_suffix" was not found in the template
   
   /home/user/somewhere/pyssianutils/submit/slurm.py:186: UserWarning:
   
   Key "out_suffix" was not found in the template

First we ensure that all the parameters that we added were detected, which in 
this case those are correct. Next, we observe that there were no errors, but 
two warnings. This means that we could use the template as is, but it will 
probably benefit us if we include the :code:`in_suffix` and the :code:`out_suffix`
these two will be added based on our user defaults in pyssianutils, specifically
in the "common" section. So including them as parameters in the template could
potentially be usefull if one day we decide to start using .out instead of .log
for our gaussian outputs. Thus we modify again the template: 

.. code-block:: none
   :caption: Adding in_suffix and out_suffix

   #!/bin/bash
   #SBATCH -c {cores}
   #SBATCH --mem {memory}
   #SBATCH -t {walltime}
   #SBATCH --partition {partition}
   #SBATCH --job-name {jobname}
   #SBATCH -o %x.slurm.o%j
   #SBATCH -e %x.slurm.e%j
   
   #Set up gaussian environment
   module load {moduleload}
   
   export GAUSS_SCRDIR=${{SCRATCHGLOBAL}}/job_${{SLURM_JOBID}}
   mkdir -p ${{GAUSS_SCRDIR}}; 
   
   job_name={jobname};
   
   {gauexe} < ${{job_name}}{in_suffix} > ${{job_name}}{out_suffix}
   
   rm -r ${{GAUSS_SCRDIR}};

Now we re-run the check 

.. code:: shell-session

   $ pyssianutils slurm check-template newtemplate.txt
   Keywords found in template newtemp.txt:
       * cores
       * gauexe
       * in_suffix
       * jobname
       * memory
       * moduleload
       * out_suffix
       * partition
       * walltime

This time we get no warnings. Now we request the generation of a json file.


.. code:: shell-session

   $ pyssianutils slurm check-template newtemplate.txt --json newtemplate.json
   Keywords found in template newtemp.txt:
       * cores
       * gauexe
       * in_suffix
       * jobname
       * memory
       * moduleload
       * out_suffix
       * partition
       * walltime

It will generate the file: 

.. code-block:: json
   :caption: newtemplate.json

   {
       "defaults": {
           "partition": "default",
           "module": "default",
           "optionwithchoices": "choice0",
           "cores": "default",
           "jobname": "default",
           "memory": "default",
           "walltime": "default"
       },
       "descriptions": {
           "partition": "partition name of the HPC",
           "module": "alias for the executable and environment modules",
           "optionwithchoices": "Description of the option",
           "cores": "description of cores",
           "jobname": "description of jobname",
           "memory": "description of memory",
           "walltime": "description of walltime"
       },
       "partition": {
           "default": {
               "name": "default",
               "max_walltime": "00-00:00:00",
               "mem_per_cpu": 2000
           }
       },
       "module": {
           "default": {
               "exe": "g16",
               "load": "module0 gaussianmodule/version"
           }
       },
       "optionwithchoices": {
           "choice0": "choice0value",
           "choice1": "choice1value"
       }
   }

6. Personalize the template
---------------------------

The personalization of the template happens at the json file that we just 
generated. Although it might look scary it is easier to change than expected. 
We will open it with a text editor and modify the corresponding text. 

We will start by adding information about the HPC, lets say that there are two 
partitions available: short and long with max walltimes of 6h and 5 days 
respectively and both allow 4096 MB per core ( If we do not know this number 
we can use either 1000 or 2000 and those are typically below the actual maximum
memory per cpu in modern HPCs) 

.. code-block:: json
   :caption: partitions

       "partition": {
           "short": {
               "name": "short",
               "max_walltime": "00-06:00:00",
               "mem_per_cpu": 2000
           },
           "long": {
               "name": "long",
               "max_walltime": "05-00:00:00",
               "mem_per_cpu": 2000
           }
       }

Next we can add the different gaussian versions available and how to load them,
lets say that the hypothetical cluster has g09 and g16 and for both you also  
need to load a module named "presets". 

.. code-block:: json
   :caption: modules

       "module": {
           "g09": {
               "exe": "g09",
               "load": "presets gaussian/09"
           },
           "g16": {
               "exe": "g16",
               "load": "presets gaussian/16"
           }
       },

Now lets say that we want to restrict the calculations that we use to 
use only 2,8 or 16 cores. We can specify said constraint by adding : 

.. code-block:: json
   :caption: cores

       "cores": [2,8,16]

or if we want to give more other names to the options we can use the template 
"optionwithchoices" that is provided in the generated json

.. code-block:: json
   :caption: cores with names

           "cores": {
           "small": 2,
           "medium": 8,
           "large": 16
       }

If we want we can remove the descriptions, but those are what will appear in the
command line so it might be usefull to have simple descriptions of the parameters

.. code-block:: json
   :caption: descriptions

    "descriptions": {
        "cores": "size of the molecule for the calculation",
        "partition": "Partition name / Queue that will be used for the calculation",
        "module": "alias of the gaussian version and how to load it",
        "walltime": "Time requested for the calculation",
        "jobname": "default name for the job"
    }


Finally, we need to update the default values in case we ever become lazy and 
do not want to specify every single value through the command line. It is 
important that for those options that we have a small subset of choices, the 
default value matches one of the choices. All together it would look like: 

.. code-block:: json
   :caption: final.json

   {
       "defaults": {
           "partition": "short",
           "module": "g16",
           "cores": "small",
           "jobname": "dummy_name",
           "memory": "2GB",
           "walltime": "00-03:00:00"
       },
       "descriptions": {
           "cores": "size of the molecule for the calculation",
           "partition": "Partition name / Queue that will be used for the calculation",
           "module": "alias of the gaussian version and how to load it",
           "walltime": "Time requested for the calculation",
           "jobname": "default name for the job"
       },
       "partition": {
           "short": {
               "name": "short",
               "max_walltime": "00-06:00:00",
               "mem_per_cpu": 2000
           },
           "long": {
               "name": "long",
               "max_walltime": "05-00:00:00",
               "mem_per_cpu": 2000
           }
       },
       "module": {
           "g09": {
               "exe": "g09",
               "load": "presets gaussian/09"
           },
           "g16": {
               "exe": "g16",
               "load": "presets gaussian/16"
           }
       },
       "cores": {
           "small": 2,
           "medium": 8,
           "large": 16
       }
   }

7. Check that both files match
------------------------------

Now that we have the slurm and the json match. We run again the check template

.. code:: shell-session

   $ pyssianutils slurm check-template newtemplate.txt --json newtemplate.json
   Keywords found in template newtemp.txt:
       * cores
       * gauexe
       * in_suffix
       * jobname
       * memory
       * moduleload
       * out_suffix
       * partition
       * walltime
   Templates are compatible

Note that a new message, indicating that both templates are compatible has 
appeared.

8. Add the new template to your templates
-----------------------------------------

Finally we need to store it with out pyssianutils user data. For that we simply 
have to run: 

.. code:: shell-session

   $ pyssianutils slurm add-template newtemplate.txt myhpc --json newtemplate.json
   Successfully added /home/user/.pyssianutils/templates/slurm/myhpc.txt
   Successfully added /home/user/.pyssianutils/templates/slurm/myhpc.json

If we now type in: 

.. code:: shell-session 
   
   $ pyssianutils slurm 
   Available slurm templates:
       example
       myhpc

the newly added template shows up, meaning that we can now run 

.. code:: shell-session

   $ pyssianutils slurm myhpc --help 
   usage: pyssianutils myhpc [-h] [-l | -r] [-o OUTDIR] [--suffix SUFFIX] [-ow | --skip] [--memory MEMORY | --memory-per-cpu]
                             [--walltime WALLTIME | --use-max-walltime] [--guess-cores] [--guess-mem] [--add-memory | --rm-memory]
                             [--add-nprocs | --rm-nprocs] [--partition {short,long}] [--module {g09,g16}]
                             [--cores {small,medium,large}] [--jobname JOBNAME]
                             [inputfiles ...]
   
   positional arguments:
     inputfiles            Gaussian input files. If none is provided, it will create a 'dummy_job.slurm' to use as template.
   
   options:
     -h, --help            show this help message and exit
     -l, --listfile        When enabled instead of considering the files provided as the gaussian output files considers the file
                           provided as a list of gaussian output files
     -r, --folder          Takes the folder and its subfolder hierarchy and creates a new folder with the same subfolder structure.
                           Finds all the .log, attempts to find their companion .com files and creates the new inputs in their
                           equivalent locations in the new folder tree structure.
     -o OUTDIR, --outdir OUTDIR
                           Where to create the new files, defaults to the current directory
     --suffix SUFFIX       suffix of the generated files
     -ow, --overwrite      When creating the new files if a file with the same name exists overwrites its contents. (The default
                           behaviour is to raise an error to notify the user before overwriting).
     --skip                Skip the creation of slurm templates that already exist
     --memory MEMORY       Memory requested for the calculation. If None is provided it will attempt to guess it from the gaussian
                           input file.
     --memory-per-cpu      It will use the max memory per cpu of the partition
     --walltime WALLTIME   Fixed value of walltime in DD-HH:MM:SS format. If none is provided it will use the default value of
                           '00-03:00:00'
     --use-max-walltime    If enabled, use the selected partition's max walltime
     --guess-cores         attempt to guess the number of cores from the gaussian input file
     --guess-mem           attempt to guess the memory from the gaussian input file
     --partition {short,long}
                           Partition name / Queue that will be used for the calculation
     --module {g09,g16}    alias of the gaussian version and how to load it
     --cores {small,medium,large}
                           size of the molecule for the calculation
     --jobname JOBNAME     default name for the job
   
   inplace:
     Arguments to modify in-place the provided gaussian input files
   
     --add-memory          Add the "%mem" Link0 option to the provided files
     --rm-memory           Remove the "%mem" Link0 option of the provided files
     --add-nprocs          Add the "%nprocshared" Link0 option to the provided files
     --rm-nprocs           Remove the "%nprocshared" Link0 option of the provided files

that shows all options that we can do with our new template but also we can now
use it to generate slurm scripts for gaussian calculations, lets say we have 
the file myfile.com, which does not have the :code:`%nprocshared` set but has 
the :code:`%mem` set up to 48GB. We can now: 

.. code:: shell-session

   $ pyssianutils slurm myhpc --cores small --guess-mem myfile.com --add-nprocs --use-max-walltime
   Creating file myfile.slurm

The contents of :code:`myfile.slurm` will be now: 

.. code:: bash

   #!/bin/bash
   #SBATCH -c 2
   #SBATCH --mem 48GB
   #SBATCH -t 00-06:00:00
   #SBATCH --partition short
   #SBATCH --job-name myfile
   #SBATCH -o %x.slurm.o%j
   #SBATCH -e %x.slurm.e%j
   
   #Set up gaussian environment
   module load presets gaussian/16
   
   export GAUSS_SCRDIR=${SCRATCHGLOBAL}/job_${SLURM_JOBID}
   mkdir -p ${GAUSS_SCRDIR};
   
   job_name=myfile;
   
   g16 < ${job_name}.com > ${job_name}.log
   
   rm -r ${GAUSS_SCRDIR};

