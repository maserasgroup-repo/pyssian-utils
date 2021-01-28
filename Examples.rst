================
pyssian examples
================

.. contents:: Table of Contents
   :backlinks: none
   :local:


Packaged Scripts Examples
-------------------------

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

the *--quiet* or *-q* option is recommended when more than one file are feeded
otherwise if any calculation did not succeed it will raise an error and stop the
execution of pyssian-potential.py (and similarly for pyssian-thermo.py)

.. code:: shell-session

   $ pyssian-potential.py -q Path/To/Files/File*.log Path/To/Error/Error.log
                                 U
   Path/To/Files/File1.log     -11111
   Path/To/Files/File2.log     -22222
   Path/To/Files/File3.log     -33333
   Path/To/Error/Error.log

.. potential-end

pyssian-thermo
..............

.. thermo-start

Prints the Potential energy, Zero point energy, Enthalpy and Free energy
from a gaussian frequency calculation. By default the Potential energy is
the value of the 'Done'

.. code:: shell-session

   $ pyssian-thermo.py -L Files.txt -q
                                 U        Z       H       G
   Path/To/Files/File1.log     -11111  -11111  -11111  -11111
   Path/To/Files/File3.log     -33333  -33333  -33333  -33333
   Path/To/Files/File2.log     -22222  -22222  -22222  -22222

.. thermo-end

pyssian-submit
..............

.. submit-start

Checks all .in files in the current directory to generate a SubmitScript.sh
that properly sends them to their queues (Files with a matching .out file
are ignored as default). It checks in which queue they should go according
to the values of nprocshared and %mem. To use the generated script run in
kimikhome: 'chmod +x SubmitScript.sh; ./SubmitScript;'


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
   %opt1
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

User API Examples
-----------------

GaussianOutFile
...............

*pyssian.GaussianOutFile* can be opened as a file object. When reading an
already finished calculation file it is recommended to use the with statement as
in this first example. If the file is being written the recommended way to open
the file is as example 2 or 3.

.. code:: python

   from pyssian import GaussianOutFile
   # Example 1
   with GaussianOutFile(FilePath) as GOF1:
      GOF1.read()
   # Example 2
   GOF2 = GaussianOutFile(FilePath)
   GOF2.read()
   GOF2.close()
   # Example 3
   File = open(FilePath,'r')
   GOF3 = GaussianOutFile(File)
   GOF3.read()
   File.close()


It also accepts another parameter that indicates which Links are of interest.
The default behaviour (without specifying any value) is to consider all links.

A second option, only used to see the structure of the file without actually
storing any information of each link is to pass -1 as the first value:

.. code:: python

   File = open(FilePath,'r')
   with GaussianOutFile(File,parselist=[-1,]) as GOF:
       GOF.update(clean=False) # read is an alias for update(clean=True)


If you specify the numbers of the links to the GOF only those will be parsed and
will not be cleaned afterwards.

.. code:: python

   File = open(FilePath,'r')
   with GaussianOutFile(File,[1,103,202,502,9999]) as GOF:
       GOF.read()


LinkJob
.......

The *pyssian.LinkJob* class is the base class for all the LinkJob subclasses
And implements the two basic attributes of all Links, *.number* and *.text*.
Currently the specific parsers implemented are:

- Link1
- Link101
- Link103
- Link123
- Link202
- Link502
- Link508
- Link716
- Link804
- Link913

.. code:: python

   with GaussianOutFile(File) as GOF:
       GOF.read()
   Link = GOF[0][RandomPosition]
   # General Attributes of all LinkJob classes
   print(Link.number)
   print(Link.text)


Link1
+++++

.. code:: python

   # From the file Get the first Link1
   Link1 = GOF.GetLinks(1)[0]
   # Attributes of Link1
   Link1.commandline
   Link1.nprocs
   Link1.mem
   Link1.link0
   Link1.IOps
   Link1.info # Will be deprecated in the future


Link101 & Link103
+++++++++++++++++

.. code:: python

   Link101 = GOF.GetLinks(101)[0]
   Link101.spin
   Link101.charge

   Link103 = GOF.GetLinks(103)[0]
   Link103.mode
   Link103.state
   Link103.conversion
   Link103.parameters
   Link103.stepnumber
   Link103.scanpoint
   if Link103.mode == 'Iteration':
       Link103.print_convergence()

Link123
+++++++

.. code:: python

   Link123 = GOF.GetLinks(123)[0]
   Link123.orientation
   Link123.step
   Link123.reactioncoord


Link202
+++++++

.. code:: python

   Link202 = GOF[-1].GetLinks(202)[0]
   Link202.orientation
   Link202.DistanceMatrix
   Link202.print_orientation()

Link502 & Link508
+++++++++++++++++

.. code:: python

   ListOfLinks = GOF.GetLinks(502,508)
   Energies = [link.energy for link in ListOfLinks if link.energy is not None]

Link716
+++++++

.. code:: python

   Link716 = GOF[-1].GetLinks(716)[-1]
   Link716.dipole
   Link716.units
   Link716.zeropoint
   Link716.thermal_energy
   Link716.enthalpy
   Link716.gibbs
   Link716.EContribs
   Link716.IRSpectrum

Link804 & Link913
+++++++++++++++++

.. code:: python

   Link804 = GOF.GetLinks(804)[-1]
   Link804.MP2
   Link804.SpinComponents
   scs_corr = Link804.Get_SCScorr()

   Link913 = GOF.GetLinks(913)[-1]
   Link913.MP4
   Link913.CCSDT


GaussianInFile
..............

*pyssian.GaussianInFile* can be instantiated either from an existing input file
or to create a new file.

.. note::

   Currently it is in an early stage as proper support for method-basis
   management as well as oniom and zmatrix support require special attention.

The following Code snippet shows how to copy create a new input from an existing
one changing the geometry and method but retaining the rest of the options

.. code:: python

   from pyssian import GaussianInFile

   InitialTheoryFile = 'InitialTheory.in'
   InitialGeometryFile = 'InitialGeometry.in'
   OutputFile = 'Output.in'
   with GaussianInFile(InitialTheoryFile) as theory_file:
       theory_file.read()
   with GaussianInFile(InitialGeometry) as geometry_file:
       geometry_file.read()
   old_geometry = theory_file.geometry # In case we want to use it somewhere else
   theory_file.geometry = geometry_file.geometry
   theory_file.method = 'b3lyp'
   with open(OutputFile,'w') as F:
       theory_file.write(F)


It combines fairly well with pyssian.classutils.Geometry to create inputs from
outputs. The following code snippet is an example of how to create an input to
continue an optimization that failed due to exceeding the number of optimization
steps.

.. code:: python

   from pyssian import GaussianInFile, GaussianOutFile
   from pyssian.classutils import Geometry

   with GaussianOutFile('Old_Calc.out') as GOF:
      GOF.read()

   # Get the last geometry of the calculation
   geom = Geometry.from_l202(GOF.GetLinks(202)[-1])

   # Get the Link1 of the GaussianOutFile
   Link1 = GOF.GetLinks(1)[0]

   # Extract the calculation type and commands
   commandline = Link1.commandline
   nprocs = Link1.nprocs
   mem = Link1.mem
   Link0 = Link1.link0

   # Get Charge and spin from Link101
   Link101 = GOF.GetLinks(101)[0]
   charge = Link101.charge
   spin = Link101.spin

   # Now write the
   with GaussianInFile('New_Calc.in') as GIF:
       GIF.parse_commandline([commandline,])
       GIF.preprocessing = {key:'' for key in Link0}
       GIF.preprocessing['nprocshared'] = nprocs
       GIF.preprocessing['mem'] = mem
       GIF.title = 'New Title'
       GIF.spin = spin
       GIF.charge = charge
       GIF.geometry = geom
       GIF.write()



Usage Examples
..............

Code snippet to extract the last potential energy and geometry

.. code:: python

   from pyssian import GaussianOutFile as GOF

   MyFile = 'path-to-file'
   with GOF(MyFile) as F:
      F.read()

   Final_Geometry = F.GetLinks(202)[-1].orientation
   Last_Potential_Energy = F.GetLinks(502)[-1]
   print(Last_Potential_Energy)
   print(str(Final_Geometry))


Code snippet to display 'Filename HF MP2 MP2(SCS)'

.. code:: python

   from pyssian import GaussianOutFile as GOF

   MyFile = 'path-to-file'
   with GOF(MyFile,[1,502,804]) as F:
      F.read()

   HF = F.GetLinks(502)[-1].energy
   Link804 = F.GetLinks(804)[-1]
   MP2 = Link804.MP2
   MP2scs = H + Link804.Get_SCScorr()
   Output ='{filename}\t{HF}\t{MP2}\t{MP2scs}'.format
   print(Output(filename=MyFile,HF=HF, MP2=MP2, MP2scs=MP2scs))


Code Snippet using functutils

.. code:: python

   from pyssian import GaussianOutFile
   from pyssian.functutils import Potential, Thermochemistry

   with GaussianOutFile(MyFile,[1,502,508,716]) as F:
       F.read()
   E,Z,H,G = Thermochemistry(F)
   E = Potential(F,method='mp2scs')


Code Snippet to follow a file being written by gaussian

.. code:: python

   from time import sleep

   from pyssian import GaussianOutFile as GOF

   F = GOF(MyFile,[-1,])
   F.update(clean=False)
   print(F[-1][-1])
   sleep(10)
   F.update(clean=False)
   print(F[-1][-1])
   F.close()
