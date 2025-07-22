.. pyssianutils documentation master file, created by
   sphinx-quickstart on Mon Feb 10 17:35:46 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

######################################
Welcome to pyssianutils documentation!
######################################

.. include:: ../../README.rst
   :start-after: project-description-start
   :end-before: project-description-end

.. warning:: 

   pyssian (and therefore pyssianutils) work on the basis that your gaussian 
   input files have the additional printout requested. In other words, the 
   command line section of your gaussian input file **MUST** start with 
   :code:`#p` otherwise pyssian (and therefore pyssianutils) will be able to 
   parse and extract the data from your gaussian output files. If the userbase
   of pyssian and pyssianutils grows and it is requested, we are more than happy
   to adapt it to be able to handle the case where gaussian input files did not 
   have the additional printout.

********
Contents
********

.. toctree::
   :maxdepth: 1
   :caption: Quick Start

   installation
   usage


.. toctree::
   :maxdepth: 1
   :caption: Main Utils

   utils/package
   utils/defaults
   utils/print
   utils/plot
   utils/submit
   utils/slurm
   utils/toxyz
   utils/inputht
   utils/asinput
   utils/distortts
   utils/others


.. toctree::
   :maxdepth: 2
   :caption: Python API

   pyssianutils

******************
Indices and tables
******************

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
