***********
Basic Usage
***********

Since version 1.0.0 :code:`pyssianutils` is a command line application that 
aggregates together multiple scripts for the manipulation of gaussian inputs and
gaussian outputs. After installation, we will use pyssianutils with the general 
syntax: 

.. code:: shell-session

   $ pyssianutils [command] [subcommand] inputs*.log --options

At any point during the construction of the command line input we can add a 
--help option. For example to display the available main commands: 

.. code:: shell-session

    $ pyssianutils --help

For a specific command (for example :code:`inputht`) we may check the different 
required inputs and options by typing: 

.. code:: shell-session 

    $ pyssianutils inputht --help

Or if we want to check for any special options mid-construction of the command 
line input: 

.. code:: shell-session 

    $ pyssianutils print potential myfile1.log myfile2.log --help

Commonly used command inputs
============================

Let us assume that in our current directory we have 6 files: 

.. code:: none

   - comp_00.com
   - comp_00.log
   - comp_00_SP.com
   - comp_00_SP.log
   - comp_01.com
   - comp_01.log

To print the final Potential energies:

.. code:: shell-session 

    $ pyssianutils print potential comp_00*.log

Or the thermochemistry and SP corrected Free energy: 

.. code:: shell-session 

    $ pyssianutils print summary comp_00*.log --with-sp

To generate a new SP calculation named :code:`comp_00_pbeSP.com` from the final geometry
if :code:`comp_00.log` : 

.. code:: shell-session 

    $ pyssianutils asinput comp_00.log --as-SP --method pbe -m pbeSP

To generate a slurm script for the newly generated input file: 

.. code:: shell-session 

    $ pyssianutils submit slurm example comp_00_pbeSP.com --guess-cores --guess-mem

Change the user defaults to make cores and memory guessing the default
behaviour

.. code:: shell-session 

    $ pyssianutils defaults set --section submit.slurm guess_default True

Visualize the convergence criteria and energy of a single optimization:

.. important:: 

   For any plotting related feature, the matplotlib and/or plotly libraries must
   be installed

.. code:: shell-session 

    $ pyssianutils plot optview comp_00.log --interactive

Interactive visualization of multiple optimizations: 

.. code:: shell-session 

    $ pyssianutils plot optmulti comp_00.log comp_01.log --interactive

Visualize how an angle changes over the optimization

.. code:: shell-session 

    $ pyssianutils plot property geometry comp_00.log 1 2 3 --interactive
