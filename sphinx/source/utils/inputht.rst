*******
inputht
*******

.. highlight:: sh

.. argparse::
   :module: pyssianutils.input.inputht
   :func: parser
   :prog: pyssianutils inputht

.. highlight:: default

Usage
=====

The util :code:`inputht` comes from **Input from Head and Tail** were both, 
head and tail refer to the top and bottom of a file. In general, in gaussian 
input files the geometry is placed in the middle of the file, where the actual 
calculation requested is in the top of the file and some extra input is placed 
at the bottom of the file. Thus, normally we find similar file headers for all 
optimizations to minima, optimizations to ts, single points... and the same 
for the file tails. :code:`inputht` works on the basis of having stored two 
files, one with the header and one with the tail, and generating a gaussian 
input file from those. 

Lets say we have the files: 

.. code-block:: none
   :caption: minima.head

   %nprocshared=2
   %mem=4GB
   #p opt freq pbepbe genecp nosymm

.. code-block:: none
   :caption: basis.tail

   -C -O -N -H 0
   6-31+g(d,p)
   ****

This type of setup allows the modification of the basis set with relative ease, 
and will not lead to an error if one of the atom types specified in the 
basis set section is missing. 

We can now create a gaussian input by providing files containing geometries. 
For example, if we use gaussview, we can draw a specific geometry, check the 
charge and spin and save the file as :code:`example1.gjf` without any specifics 
of the calculation. To generate the gaussian with the actual theory and keywords 
that we have selected: 

.. code:: shell-session

   $ pyssianutils inputht example1.gjf -H minima.head -T basis.tail --no-marker --suffix .com
   example1.gjf

This command will generate a file named :code:`example1.com` which will contain 
the charge, spin and geometry of :code:`example1.gjf`, it will start with the 
contents of :code:`minima.head` and it will end with the contents of 
:code:`basis.tail`. If the :code:`--no-marker` is not used, the generated file 
will have a "marker" in the file name. With the default marker the name would 
have been :code:`example1_new.com`. The :code:`--suffix` flag is not necessary 
in this specific case (as its default value is ".com") but controls the suffix 
of the generated files.

We can also specify multiple files instead of a single one: 

.. code:: shell-session

   $ pyssianutils inputht example*.gjf -H minima.head -T basis.tail --no-marker --suffix .com
   example1.gjf
   example2.gjf
   example3.gjf
   [...]

We may instead be interested in re-using a previous gaussian optimization for 
different reasons. We just need to provide the files.

.. code:: shell-session

   $ pyssianutils inputht example*.log -H minima.head -T basis.tail --marker run2
   example1.log
   example2.log
   example3.log
   [...]

Here we specified :code:`--marker run2` to avoid overwriting the input files of 
the already existing input files from the outputs that we provided. By default 
the last geometry of the optimization will be used, and the charge and spin 
used in the calculation will be considered. 

If we want to generate an input from a geometry that is not the last one of the
calculation we can also do it with the :code:`--step` keyword. 

.. code:: shell-session

   $ pyssianutils inputht example1.log -H minima.head -T basis.tail --step 10 --marker step10
   example1.log

We can force a specific value of charge and spin by specifying the 
:code:`--charge` and :code:`--spin` flags:

.. code:: shell-session

   $ pyssianutils inputht example1.gjf -H minima.head -T basis.tail --charge 0 --spin 1
   example1.gjf

.. attention::

   note that charge-spin consistency is not checked at this stage, so if you 
   specified a wrong combination, the gaussian calculation will error out almost
   instantly. 

Finally, if we generated the geometries with a different software, we can also 
use .xyz files.

.. code:: shell-session

   $ pyssianutils inputht example1.xyz -H minima.head -T basis.tail --charge 0 --spin 1
   example1.xyz

.. note:: 
    
   However note that the :code:`--charge` and :code:`--spin` flags
   become specially relevant for .xyz files. Otherwise the default values will 
   be used.

Two final remarks to consider is that if we want to provide a file listing all 
the files with the geometries that we want to use, we can simply use the 
:code:`--listfile` flag and use the file with the list as input. The second 
remark is that we can mix the different types of file containing a geometry 
within the same command. In other words:

.. code:: shell-session

   $ pyssianutils inputht example1.com example2.log example3.xyz -H minima.head -T basis.tail
   example1.com
   example2.log
   example3.xyz

This command will yield correct inputs, but note that example3.xyz will have the 
default charge and spin, and specifying the :code:`--charge` and :code:`--spin` 
would instead force them into example1.com and example2.log. 