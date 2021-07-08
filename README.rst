==============
pyssian-utils
==============

.. project-description-start

----------------------------------------------------------------------
A toolkit of scripts for usual computational tasks involving Gaussian
----------------------------------------------------------------------

This project is a repository of command-line tools developed using 
`pyssian <https://github.com/maserasgroup-repo/pyssian>`_ to facilitate the 
everyday work. From generating bash scripts to run all calculations in a certain 
folder to more sofisticated ways of generating and running gaussian input files.

.. project-description-end

Getting Started
---------------

.. setup-instructions

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes. See deployment for notes on
how to deploy the project on a live system.

Prerequisites
.............

- python >= 3.6
- python library: setuptools
- python library: pathlib
- python library: numpy
- python library: pyssian >= 1.0.0
- python library: matplotlib (optional)

Installing pyssian-utils
........................


Get the source code either git or download and unpack it into "pyssian-utils"

.. code:: shell-session

   $ git clone https://github.com/maserasgroup-repo/pyssian-utils.git pyssian-utils

Now install pyssian

.. code:: shell-session

   $ cd pyssian-utils
   $ python -m pip install .

.. note::
   It is recommended to download the source code in case some modifications 
   specific to your work environment are necessary. (i.e. modifying the default 
   options to suit your needs, different queue system, different queues...)

Future installation (not yet available)

.. code:: shell-session

   $ python -m pip install pyssianutils

Uninstalling pyssian-utils
..........................

.. code:: shell-session

   $ cd pyssian-utils
   $ python -m pip uninstall pyssianutils

.. note::
   In case of using the -e flag for the installation remember to remove the .egg
   folder that is generated upon installation after running 
   "pip uninstall pyssianutils" command.

Building the docs
-----------------

To build the docs go to the docs folder where you have the source code then run:

.. code:: shell-session

   $ cd sphinx/
   $ python -m pip install -r requirements.txt
   $ make html

Now if you go to the _docs/html folder you can open the index.html file in your 
folder and navigate through the documentation easily. 

Developed with
--------------

- python 3.7
- Ubuntu 16.04 LTS, 18.04 LTS and 20.04 LTS

Additional features
-------------------

The library comes with the following scripts with simple yet usefull utilities:

- pyssian-potential.py
- pyssian-thermo.py
- pyssian-submit.py
- pyssian-inputHT.py
- pyssian-asinput.py
- pyssian-tddft-cubes.py

.. examples-msg

Examples
--------

Please open the Examples.rst in github to visualize the basic usage examples
or read the documentation.

.. project-author-license

Authors
-------

* **Raúl Pérez-Soto** - [rperezsoto](https://github.com/rperezsoto)
* **Maria Besora** - [MaBeBo](https://github.com/MaBeBo)
* **Feliu Maseras** - [maserasgroup](https://github.com/maserasgroup)

License
-------

pyssianutils is freely available under an [MIT](https://opensource.org/licenses/MIT)

How to cite
-----------

If you consider that either pyssian-utils or the pyssian library provided 
enough support to your research that it deserves to cited please do cite the 
pyssian library using the DOI at the following address: 

.. image:: https://zenodo.org/badge/333841133.svg
   :target: https://zenodo.org/badge/latestdoi/333841133
