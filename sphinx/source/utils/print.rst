*****
print
*****

The :code:`print` util allows the display through console of some key properties
of the gaussian output files. There options are:

.. contents::
   :local:
   :depth: 1

potential
=========

.. highlight:: sh

.. argparse::
   :module: pyssianutils.print.potential
   :func: parser
   :prog: pyssianutils print potential

.. highlight:: default

Usage
-----

The simplest way to use the :code:`print potential` utils is to extract the
potential energy of a single molecule: 

.. code:: shell-session

   $ pyssianutils print potential File1.log
   File1.log     -11111

We can also specify multiple files manually: 

.. code:: shell-session

   $ pyssianutils print potential File1.log File2.log
   File1.log     -11111
   File2.log     -22222
   $ pyssianutils print potential File*.log
   File1.log     -11111
   File2.log     -22222
   File3.log     -33333

Another option is to provide a file where each line points to a gaussian output.
pyssianutils will respect the order of the file, which may be useful for some 
users. For example lets assume a file name :code:`Files.txt` with the contents: 

.. code:: none
   
   Path/To/Files/File1.log
   Path/To/Files/File3.log
   Path/To/Files/File2.log

We can pass this file to pyssianutils with the :code:`-l` flag: 

.. code:: shell-session

   $ pyssianutils print potential -l Files.txt
   Path/To/Files/File1.log     -11111
   Path/To/Files/File3.log     -33333
   Path/To/Files/File2.log     -22222

Finally the *--verbose* or *-v* option will raise an error for files that do 
not have a potential energy and will stop the execution.

thermo
======

.. highlight:: sh

.. argparse::
   :module: pyssianutils.print.thermo
   :func: parser
   :prog: pyssianutils print thermo

.. highlight:: default

Usage
-----

The simplest way to use the :code:`print thermo` utils is to extract the
thermochemistry of a single calculation: 

.. code:: shell-session

   $ pyssianutils print thermo File1.log
   File             E         Z         H         G  
   File1.log     -11111    -11111    -11111    -11111

If the thermochemistry is not available but the potential energy is available,
only the potential energy will be shown

.. code:: shell-session

   $ pyssianutils print thermo File1*.log
   File               E         Z         H         G  
   File1.log       -11111    -11111    -11111    -11111
   File1_SP.log    -11111                              

.. hint:: 

   As with the :code:`potential` util. We can specify multiple files either 
   manually or using a file that contains one filepath per line. 

Finally the :code:`--only-stem` flag allows to shorten full filepaths to only 
the filenames, without the suffix: 


.. code:: none
   
   
   Path/To/Files/File3.log
   Path/To/Files/File2.log

We can pass this file to pyssianutils with the :code:`-l` flag: 

.. code:: shell-session

   $ pyssianutils print thermo Path/To/Files/File1.log Path/To/Files/File1_SP.log --only-stem
   File               E         Z         H         G  
   File1           -11111    -11111    -11111    -11111
   File1_SP        -11111                              

which, without the flag would instead output 

.. code:: shell-session

   $ pyssianutils print thermo Path/To/Files/File1.log Path/To/Files/File1_SP.log
   File                             E         Z         H         G  
   Path/To/Files/File1.log       -11111    -11111    -11111    -11111
   Path/To/Files/File1_SP.log    -11111                              

summary
=======

.. highlight:: sh

.. argparse::
   :module: pyssianutils.print.summary
   :func: parser
   :prog: pyssianutils print summary

.. highlight:: default

Usage
-----

The simplest way to use the :code:`print summary` utils is to extract the
thermochemistry of a single calculation: 

.. code:: shell-session

   $ pyssianutils print summary File1.log
   File             E         Z         H         G  
   File1.log     -11111    -11111    -11111    -11111

If the thermochemistry is not available but the potential energy is available,
only the potential energy will be shown

.. code:: shell-session

   $ pyssianutils print summary File1*.log
   File               E         Z         H         G  
   File1.log       -11111    -11111    -11111    -11111
   File1_SP.log    -11111                              

.. note:: 

   For all terms and purposes :code:`print summary` behaves like 
   :code:`print thermo` while the :code:`--with-sp` is not specified. 

When the :code:`--with-sp` flag is enabled, the util will attempt to find files 
matching the name with a specific pattern at the end of the file stem (which 
may be specified with the :code:`--pattern` flag. For the files in which it 
finds a match it will display the :code:`E(SP)` and the :code:`G(SP)` computed 
as

.. math:: 
    
    G_{SP} = E_{SP} + (G - E)

Therefore, going back to the previous example: 

.. code:: shell-session

   $ pyssianutils print summary File1*.log --with-sp
   File        File_SP            E         Z         H         G       E(SP)     G(SP)
   File1.log   File1_SP.log    -11111    -11111    -11111    -11111    -11111    -11111
