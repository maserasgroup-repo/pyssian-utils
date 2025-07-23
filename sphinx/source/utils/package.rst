******************
init, clean & pack
******************

The commands included in this section are used to handle the 
installation/cleanup of pyssianutils.

.. contents::
   :depth: 1
   :local:

init
====

.. highlight:: sh

.. argparse::
   :module: pyssianutils.initialize
   :func: init_parser
   :prog: pyssianutils init

.. highlight:: default

clean
=====

.. highlight:: sh

.. argparse::
   :module: pyssianutils.initialize
   :func: clean_parser
   :prog: pyssianutils clean

.. highlight:: default

pack
====

.. highlight:: sh

.. argparse::
   :module: pyssianutils.initialize
   :func: pack_parser
   :prog: pyssianutils pack

.. highlight:: default

Copying a user's data into a different PC
=========================================

Setting up a specific pyssianutils' user configuration and templates is as 
simple as copying the defaults.ini and templates/ folders. However, in order to
allow the user more control through the CLI we included the 
:code:`pyssianutils pack` and the :code:`pyssianutils init --unpack` options.

First on a computer/user with an existing installation of pyssianutils we will
run:

.. code:: shell-session

   $ pyssianutils pack 
   Creating pyssianutils_appdata.tar
       finished

Which will create a tar file in the current directory. Next we need to copy that
tar file to either the new user or the computer where we want to transfer our 
pyssianutils setup. After, installing pyssianutils in the destination computer 
we now proceed to unpack our pyssianutils data: 

.. code:: shell-session

   $ pyssianutils init --unpack pyssianutils_appdata.tar

With this we have finished transfering our setup from one computer to another, 
or to a new user.