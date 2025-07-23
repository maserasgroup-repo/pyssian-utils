*****
slurm 
*****

The :code:`slurm` util requires of the definition of templates which are 
in general adapted to each one of the SLURM HPC resources that you have access 
to. A key idea is to allow the user to have a setup that includes information 
about specifics of each HPC, such as partition names, number of cores, memories 
per core per partition, max walltimes ...

.. note::

   Note that the "script" name is a placeholder name for each one of the 
   template names that you might use. Which may have different options. A 
   general overview of what to expect for each of those templates is provided
   in the :doc:`slurm/template` section while how the available options shown and
   default values may be tweaked is shown in :doc:`slurm/create_a_template`. 
   Examples of the usage of the :code:`add-template`, :code:`check-template` and
   :code:`rm-template` commands is included also in :doc:`slurm/create_a_template`.

.. toctree::
   :maxdepth: 1

   slurm/create_a_template
   slurm/template
   slurm/check_add_rm

