******
submit 
******

.. automodule:: pyssianutils.submit

.. contents::
   :local:


custom
------

.. attention:: 

   On the future plans, we are aiming to furhter generalizing the slurm to allow
   the definition of templates for non-slurm HPCs. If that ends up happening 
   the slurm tool will be renamed as submit, and the custom util will be 
   converter into a specific template for whoever uses it and will not be i
   included in the pyssianutils distribution.


.. highlight:: sh

.. argparse::
   :module: pyssianutils.submit.custom
   :func: parser
   :prog: pyssianutils submit custom

.. highlight:: default


slurm
-----

Although the :code:`slurm` subcommand is part of submit, to simplify its input 
we decided to allow its usage directly from pyssianutils. Thus the documentation
of :code:`submit slurm` is available at the section :doc:`slurm`
