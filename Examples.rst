======================
pyssian-utils overview
======================

.. contents:: Table of Contents
   :backlinks: none
   :local:


Packaged Scripts overview
-------------------------

All scripts come with a detailed --help option, which will always be more 
updated than this documentation. Please remember to check it in case of doubt.

pyssian-potential
.................

.. potential-start

Prints the Potential energy. Defaults to the 'Done' of l502 or l508

As the -thermo and -inputHT scripts it has 3 general ways to specify inputs:

.. code:: shell-session

   $ echo Files.txt
   Path/To/Files/File1.log
   Path/To/Files/File3.log
   Path/To/Files/File2.log
   $ pyssian-potential.py Path/To/Files/File1.log
   $ pyssian-potential.py Path/To/Files/File*.log
                                 U
   Path/To/Files/File1.log     -11111
   Path/To/Files/File2.log     -22222
   Path/To/Files/File3.log     -33333
   $ pyssian-potential.py -L Files.txt
                                 U
   Path/To/Files/File1.log     -11111
   Path/To/Files/File3.log     -33333
   Path/To/Files/File2.log     -22222

the *--verbose* or *-v* option is will raise an error for files that do not have
a potential energy or thermochemistry and will stop the execution.

.. code:: shell-session

   $ pyssian-potential.py Path/To/Error/Error.log Path/To/Files/File*.log 
                                 U
   Path/To/Error/Error.log                              
   Traceback (most recent call last):
   File "/path/to/the/pyssianutils/installation/pyssian-thermo.py", line 7, in <module>
      exec(compile(f.read(), __file__, 'exec'))
   File "/path/to/the/pyssianutils/installation/pyssian-thermo.py", line 91, in <module>
      raise e
   File "/path/to/the/pyssianutils/installation/pyssian-thermo.py", line 88, in <module>
      Z,H,G = thermochemistry(GOF)
   File "/path/to/the/pyssianutils/installation/functions.py", line 33, in thermochemistry
      Link = GOF[-1].get_links(716)[-1]
   IndexError: list index out of range
   

.. potential-end

pyssian-thermo
..............

.. thermo-start

Prints the Potential energy, Zero point energy, Enthalpy and Free energy
from a gaussian frequency calculation. By default the Potential energy is
the value of the 'Done'

.. code:: shell-session

   $ pyssian-thermo.py -L Files.txt
                                 U        Z       H       G
   Path/To/Files/File1.log     -11111  -11111  -11111  -11111
   Path/To/Files/File3.log     -33333  -33333  -33333  -33333
   Path/To/Files/File2.log     -22222  -22222  -22222  -22222
   Path/To/Files/SPFile.log    -22222                        

.. thermo-end

pyssian-submit
..............

.. submit-start

Checks all .in files in the current directory or the provided folder
to generate a SubmitScript.sh that properly sends them to their queues 
(Files with a matching .out file are ignored as default). It checks in which 
queue they should go according to the values of %nprocshared and %mem. To use 
the generated script run in the cluster:

.. code:: shell-session
   
   chmod +x SubmitScript.sh 
   ./SubmitScript

or 

.. code:: shell-session

   bash SubmitScript.sh


.. note::

   This script is customized for the current Maseras' group needs and work 
   environment. This script will nontheless end without any error upon execution
   but the generated submission script will be likely useless unless the 
   submission system is equal or similar to the Maseras' group. 


.. code:: shell-session

   $ pyssian-submit.py
   $ ssh user@server-that-uses-qs-and-gaussian
   $ chmod +x SubmitScript.sh
   $ ./SubmitScript
   Job 13169 has been successfully queued

.. submit-end

pyssian-inputHT
...............

.. inputHT-start

Generates a gaussian input files from the last geometry of gaussian output files
or from the geometry of gaussian input files using a Header and/or Tail Files
which contain everything but the geometry and spin/charge

.. code:: shell-session

   $ ls *
   File1.log File2.gjf FilesA.out FilesB.out FilesC.out
   $ pyssian-inputHT.py File1.log File2.gjf Files*.out -H Header.txt -T Tail.txt -m MARKER
   $ ls *
   File1.log File2.gjf FilesA.out FilesB.out FilesC.out
   File1_MARKER.in File2_MARKER.in FilesA_MARKER.in FilesB_MARKER.in FilesC_MARKER.in
   $ cat File1_MARKER.in
   ##########################
        HEADER contents
   %opt1
   %opt2
   #p method basis keywd ...
   #########################

   File1_MARKER

   c s
   X    0.0000    0.0000     0.0000
   X    0.0000    0.0000     0.0000
   X    0.0000    0.0000     0.0000
   X    0.0000    0.0000     0.0000
   X    0.0000    0.0000     0.0000

   ########################
         TAIL contents

   ########################

.. inputHT-end

pyssian-asinput
...............

.. asinput-start

Takes a gaussian output file and creates a gaussian input file with its last
geometry either using a provided input file as template or using a .in file with
the same name as the provided output file.

This script was mainly developed to generate new calculations from existing 
calculations while maintaining a similar directory structure. It shares the 
input options of pyssian-inputHT however it does provide an extra input option
"-r" or "--folder" which switches the input from a file to a folder and attempts
to automatically discover all output files on all subfolders with matching input
files. 

It also provides different options on how to place the newly generated input 
files. "--inline" will attempt to create the new inputs in the same locations as
their original inputs and outputs. "--OutDir" will place the generated inputs 
in the specified directory (when used with --folder will create the same folder
hierarchy in the specified OutDir)  

To simplify the modification of the basis set it is recommended to specify it 
in the gen or genecp section, at the tail of the file. With this just passing 
a new file with the contents of the new basis set allows an easy change of 
the basis set.

Some extra options allow for standard modifications of the new files such as 
modifying the method or functional (i.e changing b3lyp for m06 or for hf), 
generating SP calculations from optimizations, removing/adding solvation or 
adding a specific text to the command line (i.e. adding "Int=(grid=UltraFine)" or
"nosymm", or both "Int=(grid=UltraFine) nosymm" )

Finally it integrates the functionality of pyssian-submit generating a 
SubmitScript that traverses all the necessary directories and submits the 
calculations.

Lets assume the following project structure:

.. code:: shell-session

   $ ls *
   project-folder
   $ ls project-folder/*/
   minima/ ts/
   $ ls project-folder/minima/*
   A.in A.out B.gjf B.log
   $ ls project-folder/ts/*
   TS1.in TS1.out

Lets assume that all were calculated with b3lyp in vacuum and we want to change 
them to wb97xd with dichloromethane and smd to re-optimize them in a new folder

.. code:: shell-session

   $ pyssian-asinput -r project-folder -O project-folder-wb97xd --method wb97xd \
   --solvent dichloromethane --smodel smd --no-marker 

Now we check our directory

.. code:: shell-session

   $ ls *
   project-folder project-folder-wb97xd SubmitScript.sh
   $ ls project-folder-wb97xd/*/
   minima/ ts/
   $ ls project-folder-wb97xd/minima/*
   A.in B.in
   $ ls project-folder-wb97xd/ts/*
   TS1.in

Now, lets assume that we run the calculations and all of them end without trouble. 
And we want to run a SP in water, to see the effect of the solvent. But we want 
each SP in the same folder as the optimization.

.. code:: shell-session

   $ pyssian-asinput -r project-folder-wb97xd --inline --solvent water

Now our directory will look like this: 

.. code:: shell-session

   $ ls *
   project-folder project-folder-wb97xd SubmitScript.sh
   $ ls project-folder-wb97xd/*/
   minima/ ts/
   $ ls project-folder-wb97xd/minima/*
   A.in A.out A_SP.in B.in B.out B_SP.in
   $ ls project-folder-wb97xd/ts/*
   TS1.in TS1.out TS1_SP.in

If we check the contents of the SubmitScript we will see that it is completely 
changed to only run the SP calculations.

.. asinput-end

pyssian-track
.............

.. track-start

Prints the name of the tracked variable, its value, derivative, Max Forces
conversion Y/N, Cartesian forces value and Geometry index of the geometry in
the file.

This script was designed to follow the details of scans when looking for a 
plausible TS structure, so the --scan flag switches to automatically detect the 
scanned variable (only works for 1D scans). Otherwise any other internal 
variable can be specified to see how it evolves during the calculation. 

.. track-end

pyssian-tddft-cubes
...................

.. tddft-start

Takes a gaussian output file and a gaussian chk file and a list of Excited
States (by number) and creates a .in.sub file to generate only the cube files
of the orbitals involved in the transitions as well as a python script(s) to
generate the appropiate combination of the cube files.

This script was tailor-made for a very specific request of automating the 
workflow needed to visualize how the electronic density changes for some 
specified excited states. 

More detailed documentation will be added in the future. 

.. tddft-end