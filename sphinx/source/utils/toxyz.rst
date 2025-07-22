*****
toxyz 
*****

.. highlight:: sh

.. argparse::
   :module: pyssianutils.toxyz
   :func: parser
   :prog: pyssianutils toxyz

.. highlight:: default

Usage
=====

If we aim to extract a specific step of a given gaussian minimization or 
transition state search toxyz allows its extraction with the :code:`--step` 
However the main motivation for the development of this util was to simplify 
the visual inspection of the final geometries of multiple conformers. Lets say
that we 10 conformers in a folder with the names :code:`molecule_{00..10}.log`.
Using :code:`toxyz` we can generate an xzy with the last geometry of each 
conformer optimization by: 

.. code:: shell-session

   $ pyssianutils toxyz molecule_*.log -o all_conformers.xyz
   molecule_00.log
   molecule_01.log
   molecule_02.log
   molecule_03.log
   molecule_04.log
   molecule_05.log
   molecule_06.log
   molecule_07.log
   molecule_08.log
   molecule_09.log
   molecule_10.log

Now we can easily open the all conformers with :code:`jmol`, or any other 
visualization software in which we can easily switch between the different 
frames of a multimolecular xyz file. 
