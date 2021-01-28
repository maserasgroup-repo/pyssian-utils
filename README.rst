==============
pyssian-utils
==============

-------------------------------------------------------
A toolkit of scripts for everyday Maseras' group work
-------------------------------------------------------

.. project-description-start

This project is a repository of command-line tools developed using pyssian
(mostly) to facilitate the everyday work. From generating bash scripts to run
all calculations in a certain folder to more sofisticated ways of generating
and running gaussian input files.

.. setup-instructions

Getting Started
---------------

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes. See deployment for notes on
how to deploy the project on a live system.

Prerequisites
.............

- python >= 3.6
- python library: setuptools
- python library: numpy
- python library: matplotlib
- python library: pyssian

Installing the dependencies
...........................

python3.7 installation in Ubuntu 18.04 LTS

.. code:: shell-session

   $ sudo apt-get update
   $ sudo apt-get install python3.7 python3.7-dev


If for any reason it is not reachable:

.. code:: shell-session

   $ sudo add-apt-repository ppa:deadsnakes/ppa
   $ sudo apt-get update
   $ sudo apt-get install python3.7 python3.7-dev

Now you can skip this if you don't want to set up a virtual environment
(Remember to change NewFolder for the actual path of the directory where you
want the virtual environment)

.. code:: shell-session

   $ sudo apt-get install python3.7-venv
   $ python3.7 -m venv NewFolder
   $ source NewFolder/bin/activate

Now we install the python default installer pip

.. code:: shell-session

   $ python -m pip install pip
   $ python -m pip install --upgrade pip
   $ python -m pip install setuptools

If it proceeded without any errors (pip and setuptools should already be installed)

Now to install the optional dependencies (Skip if you don't desire them):

.. code:: shell-session

   $ python -m pip install numpy
   $ python -m pip install matplotlib

Installing pyssian-utils
........................


Get the source code either git or download and unpack it into "pyssian-utils"
(Currently you need the developer permission to access the code)

.. code:: shell-session

   $ git clone https://github.com/maserasgroup-repo/pyssian-utils.git pyssian-utils

Now install pyssian

.. code:: shell-session

   $ cd pyssian-utils
   $ python -m pip install .


Installing with the -e option before NewDir will make that all the changes in
the source files will have have effect when you call them through their alias.
However, you have to manually clean the folder generated in case of uninstalling
the package.

Uninstalling pyssian-utils
..........................

.. code:: shell-session

   $ cd pyssian-utils
   $ python -m pip uninstall pyssianutils


Developed with
--------------

- python 3.7.3
- Ubuntu 16.04 LTS

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

* **Raúl Pérez-Soto** - *Initial work* - [rperezsoto](https://github.com/rperezsoto)

See also the list of [contributors](https://github.com/rperezsoto/contributors) who participated in this project.

License
-------

(None currently)
