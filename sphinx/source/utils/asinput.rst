*******
asinput
*******

.. highlight:: sh

.. argparse::
   :module: pyssianutils.input.asinput
   :func: parser
   :prog: pyssianutils asinput

.. highlight:: default

Usage
=====

The main use-cases of :code:`asinput` is for the generation of single point 
inputs as well as for re-running finished calculations with common changes
(changing the basis, method, solvation, solvent, adding some text to all 
inputs such as "g09defaults" or "empiricaldispersion"). 

For example purposes lets assume that we have the following folder structure: 

.. code:: none
   
   - project
   | - minima
   | | - A.com
   | | - A.log
   | | - B.com
   | | - B.log
   | | - AB.com
   | | - AB.log
   | - ts
   | | - ts_01.com
   | | - ts_01.log
   | | - ts_02.com
   | | - ts_02.log

Let us also assume that all calculations have the method and basis specified in 
the command line, e.g. :code:`wb97xd` and :code:`6-31+g(d)`

First, we could generate a single point input for A by running: 

.. code:: shell-session

   $ pyssianutils asinput project/minima/A.log --inplace --as-SP --basis "6-311+g(d,p)" 

this will change the folder structure to:

.. code:: none
   
   - project
   | - minima
   | | - A.com
   | | - A.log
   | | - A_SP.com
   | | - B.com
   | | - B.log
   | | - AB.com
   | | - AB.log
   | - ts
   | | - ts_01.com
   | | - ts_01.log
   | | - ts_02.com
   | | - ts_02.log

by specifying :code:`--inplace` we indicate that we want the new input to be in 
the same folder as the logfile from which it was generated. By specifying
:code:`--as-SP` everything but the :code:`opt` and :code:`freq` keywords are 
copied from the reference input file (:code:`A.com`, which is the :code:`.com` 
with the same name and in the same folder as the provided :code:`.log`). Finally,
the :code:`--basis "6-311+g(d,p)"` changes the basis of the template file to the
provided one, :code:`6-311+g(d,p)` If we wanted to specify the basis at the end
of the file, we would instead :code:`--basis genecp` and also :code:`--tail tail.txt`
where :code:`tail.txt`'s contents would be the basis set specification as we 
would at the end of a gaussian input file (see also :doc:`inputht` )

Instead of specifying just a single output file, we can instead specify various 
files, either directly in the command line or by providing a file that lists the
output files to consider and the :code:`--listfile` (similar mechanisms 
are included in :doc:`inputht`, :doc:`print` or :doc:`toxyz` ) Therefore the 
command:

.. code:: shell-session

   $ pyssianutils asinput project/minima/*.log --inplace --as-SP --basis "6-311+g(d,p)" 

would change our file structure to: 

.. code:: none
   
   - project
   | - minima
   | | - A.com
   | | - A.log
   | | - A_SP.com
   | | - B.com
   | | - B.log
   | | - B_SP.com
   | | - AB.com
   | | - AB.log
   | | - AB_SP.com
   | - ts
   | | - ts_01.com
   | | - ts_01.log
   | | - ts_02.com
   | | - ts_02.log

If we have multiple folders and we want the same operation for all folders 
and subfolders we can instead specify it as: 

.. code:: shell-session

   $ pyssianutils asinput -r project --inplace --as-SP --basis "6-311+g(d,p)" --suffixes .com .log

which will update our folder structure to: 

.. code:: none
   
   - project
   | - minima
   | | - A.com
   | | - A.log
   | | - A_SP.com
   | | - B.com
   | | - B.log
   | | - B_SP.com
   | | - AB.com
   | | - AB.log
   | | - AB_SP.com
   | - ts
   | | - ts_01.com
   | | - ts_01.log
   | | - ts_01_SP.com
   | | - ts_02.com
   | | - ts_02.log
   | | - ts_02_SP.com

.. note::

   If we had run the previous commands sequentially, an error would have shown 
   at the second command, complaining that :code:`A_SP.com` already existed, and
   that if we wanted to overwrite it the flag :code:`-ow` is necessary. This was 
   done to avoid overwriting by mistake already existing files. 

With the help, of :code:` pyssianutils submit slurm` we can generate a slurm 
script for each one of the SP calculations (see more at :doc:`slurm`) After 
running the calculations our folder would look like: 

.. code:: none
   
   - project
   | - minima
   | | - A.com
   | | - A.log
   | | - A_SP.com
   | | - A_SP.log
   | | - B.com
   | | - B.log
   | | - B_SP.com
   | | - B_SP.log
   | | - AB.com
   | | - AB.log
   | | - AB_SP.com
   | | - AB_SP.log
   | - ts
   | | - ts_01.com
   | | - ts_01.log
   | | - ts_01_SP.com
   | | - ts_01_SP.log
   | | - ts_02.com
   | | - ts_02.log
   | | - ts_02_SP.com
   | | - ts_02_SP.log

If we wanted to re-do the project with a different functional we can easily 
generate a new folder that respects the folder structure of our project folder

.. code:: shell-session

   $ pyssianutils asinput -r project --outdir project_m06 --suffixes .com .log --no-marker

Now we will have a new folder with the contents: 

.. code:: none
   
   - project_m06
   | - minima
   | | - A.com
   | | - A_SP.com
   | | - B.com
   | | - B_SP.com
   | | - AB.com
   | | - AB_SP.com
   | - ts
   | | - ts_01.com
   | | - ts_01_SP.com
   | | - ts_02.com
   | | - ts_02_SP.com

where all the inputs have :code:`m06` as functional instead of :code:`wb97xd`.
we could then run first all the optimizations, re-generate the single points as 
we did previously, and re-run the single point calculations. 
