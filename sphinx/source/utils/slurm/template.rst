********
template
********

.. important:: 
   
   In order to view the available templates, running the :code:`slurm` util 
   without any subcommand will display the available names. 
   
   .. code:: shell-session

      $ pyssianutils slurm
      Available slurm templates:
          example
   
   A single template is packaged by default, under the name of "example".
   The following arguments are the ones generated for said "example" template.


.. highlight:: sh

.. argparse::
   :module: pyssianutils.submit.slurm
   :func: subparser
   :prog: pyssianutils slurm example

.. highlight:: default


.. important:: 

   The :code:`--guess-cores` and the :code:`--guess-mem` flags will show if 
   in the user defaults, the :code:`guess_default` value in the subsection 
   :code:`[submit.slurm]` is set to :code:`False`. If it is set to :code:`True`,
   the :code:`--fix-cores` and :code:`--fix-mem` will show instead. 

.. important:: 

   The :code:`--inplace` flag will only show if in the user defaults, the 
   :code:`inplace_default` value in the subsection of :code:`[submit.slurm]` is
   set to :code:`False`. If it is set to :code:`True` it will become the default
   behavior