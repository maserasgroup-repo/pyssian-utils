******
others
******

The utils included here were custom made for some users that requested them, 
thus they have a much more narrow usage scope. Nonetheless we saw no reason 
to not disclose them.

track
=====

.. highlight:: sh

.. argparse::
   :module: pyssianutils.others.track
   :func: parser
   :prog: pyssianutils others track

.. highlight:: default

Usage
-----

The development of this tool was focused into inspecting optimizations and 
relaxed scan calculations in order to find good guesses for transition states
or detect at which step the transition state may have changed to converge to a 
different transition state than the desired one.

.. note:: 

   The output of the following example has been simplified with respect to the 
   actual output, and thus the presented results are not realistic. These are 
   merely used to illustrate how the output from :code:`pyssianutils other track`
   looks like and what it contains.

First we can inspect the gaussian output file by hand to extract the different 
internal coordinates definitions and select the one that we find the most 
relevant. Or we can instead use :code:`track` to simplify it a little bit: 

.. code:: shell-session

   $ pyssianutils others track path/to/example.log 
   Available parameters to track for path/to/example.log
         Name    Definition    
           R1    R(1,2)    
           R2    R(1,3)    
           R3    R(1,4)    
           R4    R(2,10)   
           R5    R(2,11)   
           A1    A(2,1,4)  
           A2    A(3,1,4)  
           A3    A(1,2,10) 
           A4    A(1,2,11) 
           D1    D(4,1,2,10)
           D2    D(4,1,2,11)
           D3    D(4,1,2,17)

Let's say that from those variables, we might think that distance "R3" is the 
most likely to be related to the TS that we are looking for. Then we can track 
that variable during the optimization: 

.. code:: shell-session

   $ pyssianutils others track path/to/example.log 
    Variable         Value           dE/dX           Conver        Car Forces       Geom Num 
       R3           4.84074         -0.00268           NO           0.002445317        1     
       R3           4.82437         -0.00127           NO           0.008095657        2     
       R3           4.85777         -0.00003           NO           0.004442530        3     
       R3           4.83914         -0.00210           NO           0.001962615        4     
       R3           4.79272         -0.00071           NO           0.002282302        5     
       R3           4.81657          0.00155           NO           0.004568041        6     
       R3           4.83462          0.00016           NO           0.001937148        7     
       R3           4.81713         -0.00064           NO           0.001487927        8     
       R3           4.80367          0.00044           NO           0.000762087        9     
       R3           4.81339          0.00094           NO           0.001016865        10    
       R3           4.81620          0.00030           NO           0.000505738        11    
       R3           4.81584          0.00004          YES           0.000310116        12    
       R3           4.81533         -0.00002          YES           0.000232864        13    
       R3           4.81447         -0.00003          YES           0.000098242        14    
       R3           4.81395         -0.00002          YES           0.000094327        15    
       R3           4.81378         -0.00000          YES           0.000086698        16    
       R3           4.81386          0.00001          YES           0.000053593        17    
       R3           4.81387          0.00000          YES           0.000017043        18    

Here we have the value of the variable, (in Bohrs for distances and in radians 
for angles and dihedrals) de differential of the energy relative to the variable,
if the cartesian forces have converged (YES/NO) and their actual value and finally
the number of the geometry. In the present example the numbers have been taken 
from an optimization to minima, therefore it makes sense that the geometry with
the highest cartesian forces value is at the initial geometries. However, we may
use the value of the cartesian forces or the differencial of the energy relative 
to the variable to select a new initial geometry for an optimization. 

cubes-tddft
===========

.. highlight:: sh

.. argparse::
   :module: pyssianutils.others.cubestddft
   :func: parser
   :prog: pyssianutils others cubes-tddft

.. highlight:: default


Usage
-----

**This is probably the util with the narrowest scope**. The original aim of the 
present tool was to simplify and automate the generation of cubefiles 
containing the molecular orbitals involved in transitions of excited states. 
This util outputs two scripts, a shell script that is used to generate the 
cubefiles with cubegen in individual files and a python script, that using 
the Cube class of pyssian, simplifies the process of combining the different 
cube files ( which could potentialy involve a large amount of individual 
commands as some utils only allow the combination of a maximum of 2 cubefiles 
at the same time)

.. warning:: 

   This tool has not been maintained in a long time, thus it is likely to break.
   If you face troubles trying to use it we heavily recommend that you contact 
   the main developer. 