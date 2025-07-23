********
defaults
********

The :code:`defaults` util allows the display and modification of the user 
defaults. These defaults values control some basic behaviors of the different 
utils, such as the number of decimals shown for energies or the preferred 
suffixes used by the user ( for example :code:`.com` vs :code:`.gjf` vs 
:code:`.in` or :code:`.out` vs :code:`.log`). There are two main subactions:

.. contents::
   :local:
   :depth: 1

show
====

.. highlight:: sh

.. argparse::
   :module: pyssianutils.initialize
   :func: show_subparser
   :prog: pyssianutils defaults show

.. highlight:: default

Examples
--------

If the user prefers to change the defaults using a text editor, to know the 
location of the defaults file: 

.. code:: shell-session

   $ pyssianutils defaults show --path

Other examples of the usage of the "defaults show" command include:

Display all sections
^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults show 
   [common]
   [submit]
   ...
   [submit.slurm]

Display the values of all parameters in a specific section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults show --section common
   in_suffix = .com
   out_suffix = .log
   default_marker = new
   gaussian_in_suffixes = (.com,.gjf,.in)
   gaussian_out_suffixes = (.com,.gjf,.in)

Display the value of a specific parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults show in_suffix --section common
   in_suffix = .com

Display the value of all parameters with a specific name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults show color --all
   [plot.optview.gridA]
       color = k
   [plot.optview.gridB]
       color = k
   [plot.property]
       color = k

set
===

.. highlight:: sh

.. argparse::
   :module: pyssianutils.initialize
   :func: set_subparser
   :prog: pyssianutils defaults set

.. highlight:: default

Examples
--------


Change the value of all parameters with a specific name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults set color "#501616ff" --all
       setting [plot.optview.gridA][color] = #501616ff
       setting [plot.optview.gridB][color] = #501616ff
       setting [plot.property][color] = #501616ff
   storing new defaults


Change the value of a specific parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults set color "k" --section plot.property
       setting [plot.property][color] = k
   storing new defaults

Or if its name is unique: 

.. code:: shell-session

   $ pyssianutils defaults set in_suffix ".gjf"
       setting [common][in_suffix] = .gjf
   storing new defaults


reset
=====

.. highlight:: sh

.. argparse::
   :module: pyssianutils.initialize
   :func: reset_subparser
   :prog: pyssianutils defaults reset

.. highlight:: default

Examples
--------


Change the value of all parameters with a specific name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults reset color --all
       resetting [plot.optview.gridA][color] = k
       resetting [plot.optview.gridB][color] = k
       resetting [plot.property][color] = k
   storing new defaults


Change the value of a specific parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: shell-session

   $ pyssianutils defaults reset color --section plot.property
       resetting [plot.property][color] = k
   storing new defaults

Or if its name is unique: 

.. code:: shell-session

   $ pyssianutils defaults reset in_suffix
       setting [common][in_suffix] = .com
   storing new defaults
