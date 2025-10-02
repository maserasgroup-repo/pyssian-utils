############
pyssianutils
############


***********************************************************************
A command line toolkit for common tasks involving Gaussian Calculations
***********************************************************************

.. project-description-start

This project is a repository of command-line tools developed using 
`pyssian <https://github.com/maserasgroup-repo/pyssian>`_ to facilitate the 
everyday tasks of a computational chemist using Gaussian. From generating slurm
scripts to run all calculations in a certain folder to more sofisticated ways 
of generating and running gaussian input files, extracting information from the 
calculations or even plotting that information. 

.. project-description-end

How to cite
===========

.. citation-start

If you consider that either pyssian-utils or the pyssian library provided 
enough support to your research that it deserves to cited please do cite the 
pyssian library using the DOI at the following address: 

.. image:: https://zenodo.org/badge/333841133.svg
   :target: https://zenodo.org/badge/latestdoi/333841133

.. citation-end

Getting Started
===============

.. setup-instructions

These instructions will get you a copy of the project up and running on your
local machine.

Prerequisites
-------------

- python >= 3.10 (Developed with python 3.12)
- python library: setuptools
- python library: pathlib
- python library: numpy
- python library: pyssian >= 1.1.0
- python library: matplotlib (optional)
- python library: plotly (optional)

Installing pyssian-utils
------------------------

Basic installation 

.. code:: shell-session

   $ python -m pip install pyssianutils

Or to ensure that the dependencies for plotting are included:

.. code:: shell-session

   $ python -m pip install pyssianutils[plotting]

Since pyssianutils>=1.0.0, to allow the user to customize pyssianutils to their 
preferences we have added a prerequisite step between installation and using 
pyssianutils. We need to initialize pyssianutils for the user: 

.. code:: shell-session 

   $ pyssianutils init


Installation from source
^^^^^^^^^^^^^^^^^^^^^^^^

Get the source code either git or download and unpack it into "pyssian-utils"

.. code:: shell-session

   $ git clone https://github.com/maserasgroup-repo/pyssian-utils.git pyssian-utils/

Now proceed to install it 

.. code:: shell-session

   $ python -m pip install ./pyssian-utils

Or to ensure that the dependencies required for plotting are included

.. code:: shell-session

   $ python -m pip install ./pyssian-utils[plotting]

Finally we ensure that pyssianutils is initialized: 

.. code:: shell-session

   $ pyssianutils init


Uninstalling pyssianutils
-------------------------

.. important:: 

   Since pyssianutils>=1.0.0, to ensure a complete removal of all pyssianutils 
   files we need to run the 'clean' command before using pip to uninstall it. 
   If we do not do it some configuration files will remain in the users app 
   directory. 

.. code:: shell-session

   $ pyssianutils clean
   $ python -m pip uninstall pyssianutils

.. setupend

Developed with
==============

.. developed-start

- python 3.12
- Ubuntu 22.04 LTS

.. developed-end

.. project-author-license

Authors
=======

* **Raúl Pérez-Soto** - [rperezsoto](https://github.com/rperezsoto)
* **Maria Besora** - [MaBeBo](https://github.com/MaBeBo)
* **Feliu Maseras** - [maserasgroup](https://github.com/maserasgroup)

License
=======

pyssianutils is freely available under an [MIT](https://opensource.org/licenses/MIT)
