"""
Generate a figure for a single gaussian output calculation including key 
convergence variables of an optimization. 
"""

import argparse
import warnings
from pathlib import Path

from pyssian import GaussianOutFile
from ..initialize import load_app_defaults

try:
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError as e: 
    LIBRARIES_LOADED = False
    LIBRARIES_ERROR = e
else:
    LIBRARIES_LOADED = True

DEFAULTS = load_app_defaults()
WIDTH = DEFAULTS['plot.optview'].getfloat('width')
HEIGHT = DEFAULTS['plot.optview'].getfloat('height')
DPI = DEFAULTS['plot.optview'].getfloat('dpi')


# Utility Functions
def get_energy(l502,l508):
    if l508.energy is not None: 
        return l508.energy
    return l502.energy

# Parser and main definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('ifile',help='Gaussian Output File')
parser.add_argument('--outfile',
                    nargs='?',default=Path('screen.png'),
                    help='Output image file')
parser.add_argument('--width',
                    type=float,default=WIDTH,
                    help=f'figure width in inches (default {WIDTH})')
parser.add_argument('--height',
                    type=float,default=HEIGHT,
                    help=f'figure height in inches (default {HEIGHT})')
parser.add_argument('--dpi',
                    type=int,default=DPI,
                    help=f"Figure's Dots Per Inch (default {DPI})")
if DEFAULTS['plot.property'].getboolean('default_interactive'): 
    parser.add_argument('--static',
                        dest='is_interactive',
                        action='store_false', default=True,
                        help="Write to a file instead of showing the figure in a new window")
else:
    parser.add_argument('--interactive',
                        dest='is_interactive',
                        action='store_true',default=False,
                        help="Instead of writing to a file open a window showing the figure")

def main(
        ifile:str|Path,
        outfile:str|Path,
        width:float=WIDTH,
        height:float=HEIGHT,
        dpi:float=DPI,
        is_interactive:bool=False
        ):
    
    # We want to delay any errors of optional libraries to the 
    # actual moment when they would be required
    if not LIBRARIES_LOADED: 
        raise LIBRARIES_ERROR
    
    if Path(outfile).suffix == '.svg':
        matplotlib.rcParams['svg.fonttype'] = 'none'

    if is_interactive: 
        msg = ("We have observed that while the figure generated "
              "when writing to a file maintains all desired proportions "
              "when showing it interactively "
              "fontsizes and relative positions are not respected.")
        warnings.warn(msg)
    
    with GaussianOutFile(ifile) as GOF:
        GOF.read()

    if len(GOF) > 1: 
        links_502 = GOF[0].get_links(502) + GOF[1].get_links(502)
        links_508 = GOF[0].get_links(508) + GOF[1].get_links(508) 
        links_103 = GOF[0].get_links(103) + GOF[1].get_links(103)[1:]
    else:
        links_502 = GOF[0].get_links(502)
        links_508 = GOF[0].get_links(508)
        links_103 = GOF[0].get_links(103)

    has_508 = len(links_508) > 0

    energies = []
    forces = []
    rmsforces = []
    displacements = []
    rmsdisplacements = []
    #Maximum Displacement     0.723929     0.001800     NO 
    thresholds = None
    ylabels = None

    if has_508:
        items = (links_502,links_508,links_103[1:])
    else:
        items = (links_502,links_103[1:])

    for links in zip(*items):
        
        if has_508: 
            l502,l508,l103 = links
        else:
            l502,l103 = links
        
        try:
            force,rmsforce,displacement,rmsdisplacement = l103.convergence
        except ValueError:
            force,rmsforce,displacement,rmsdisplacement = np.nan,np.nan,np.nan,np.nan
            _error_count += 1
            if _error_count >= 3: 
                raise ValueError
        
        energy = l502.energy
        if l508.energy is not None: 
            energy = l508.energy
        energies.append(energy)

        forces.append(force.Value)
        rmsforces.append(rmsforce.Value)
        displacements.append(displacement.Value)
        rmsdisplacements.append(rmsdisplacement.Value)
        if thresholds is None: 
            thresholds = (force.Threshold, rmsforce.Threshold, 
                        displacement.Threshold, rmsdisplacement.Threshold)
            ylabels = (force.Item, rmsforce.Item, displacement.Item, rmsdisplacement.Item)

    # prepare figure
    if is_interactive:
        fig = plt.figure(figsize=(width,height))
    else: 
        fig = plt.figure(figsize=(width,height),dpi=dpi)

    # We create the grid_A
    gridspec_A_kwds = dict()
    gridspec_A_kwds['left'] = DEFAULTS['plot.optview.gridA'].getfloat('left')
    gridspec_A_kwds['right'] = DEFAULTS['plot.optview.gridA'].getfloat('right')
    gridspec_A_kwds['top'] = DEFAULTS['plot.optview.gridA'].getfloat('top')
    gridspec_A_kwds['bottom'] = DEFAULTS['plot.optview.gridA'].getfloat('bottom')
    gridspec_A_kwds['ncols'] = 2
    gridspec_A_kwds['nrows'] = 2
    gridspec_A_kwds['hspace'] = DEFAULTS['plot.optview.gridA'].getfloat('hspace')
    gridspec_A_kwds['wspace'] = DEFAULTS['plot.optview.gridA'].getfloat('wspace')

    subgrid = grid_A = fig.add_gridspec(**gridspec_A_kwds)

    # We create the grid_B
    gridspec_B_kwds = dict()
    gridspec_B_kwds['left'] = DEFAULTS['plot.optview.gridB'].getfloat('left')
    gridspec_B_kwds['right'] = DEFAULTS['plot.optview.gridB'].getfloat('right')
    gridspec_B_kwds['top'] = DEFAULTS['plot.optview.gridB'].getfloat('top')
    gridspec_B_kwds['bottom'] = DEFAULTS['plot.optview.gridB'].getfloat('bottom')

    grid_B = fig.add_gridspec(**gridspec_B_kwds)

    # Now we create the axes
    ax_A00 = fig.add_subplot(subgrid[0,0])
    ax_A01 = fig.add_subplot(subgrid[0,1])
    ax_A10 = fig.add_subplot(subgrid[1,0])
    ax_A11 = fig.add_subplot(subgrid[1,1])
    A_axes = [ax_A00,ax_A10,ax_A01,ax_A11]
    ax_B = fig.add_subplot(grid_B[0])

    # Drawing
    x = [i+1 for i in range(len(energies))]

    # Energies
    color_B = DEFAULTS['plot.optview.gridB']['color']
    size_B = DEFAULTS['plot.optview.gridB'].getfloat('scattersize')
    ax_B.plot(x,energies,color=color_B)
    ax_B.scatter(x,energies, facecolor=color_B, s=size_B)
    ax_B.set_xlabel('iteration')
    ax_B.set_ylabel('energy, hartree')

    # Convergence
    color_A = DEFAULTS['plot.optview.gridA']['color']
    threshold_color_A = DEFAULTS['plot.optview.gridA']['threshold_color']
    size_A = DEFAULTS['plot.optview.gridA'].getfloat('scattersize')
    try:
        xlims = min(x), max(x)
    except ValueError: 
        xlims = None
    yvals = [forces,rmsforces,displacements,rmsdisplacements]
    for ax,t,yl,y in zip(A_axes,thresholds,ylabels,yvals):
        if xlims is not None: 
            ax.hlines([t,],xlims[0],xlims[1],color=threshold_color_A)
        ax.set_ylabel(yl)
        ax.set_xlabel('iteration')
        ax.plot(x,y,color=color_A)
        ax.scatter(x,y,facecolor=color_A,s=size_A)

    if is_interactive:
        plt.show(block=True)
    else:
        print(f'writing -> {outfile}')
        fig.savefig(outfile,dpi=dpi)