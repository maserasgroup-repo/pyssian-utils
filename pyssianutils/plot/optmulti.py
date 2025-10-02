"""
Generate an interactive figure for a multiple gaussian output calculation 
including key convergence variables of an optimization. 
"""

import argparse
from pathlib import Path

from pyssian import GaussianOutFile
from ..initialize import load_app_defaults

try:
    import numpy as np

    from matplotlib.cm import get_cmap
    from matplotlib.colors import to_hex

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from plotly.io import to_html
except ImportError as e: 
    LIBRARIES_LOADED = False
    LIBRARIES_ERROR = e
else:
    LIBRARIES_LOADED = True

DEFAULTS = load_app_defaults()


# Utility Functions
def get_energy(l502,l508):
    if l508.energy is not None: 
        return l508.energy
    return l502.energy

def parse_gaussian_data(ifile):

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

    _error_count = 0

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
        if has_508: 
            l508 = links[1]
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

    return energies, forces, rmsforces, displacements, rmsdisplacements, thresholds


# Parser and main definition
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',help='Gaussian Output Files',nargs='+')
parser.add_argument('--outfile',nargs='?',
                    default=DEFAULTS['plot.optmulti']['outfile'],
                    help="Output html file where the interactive figure will "
                    "be written to")
parser.add_argument('--browser',
                    dest='in_browser',
                    action='store_true',default=False,
                    help="If enabled instead of saving to a file it will "
                    "open a browser window and show the figure. To exit the "
                    "process in the terminal remember to Ctrl+C")

def main(
         files:list[str|Path],
         outfile:str|Path,
         in_browser:bool=False
         ):
    
    # We want to delay any errors of optional libraries to the 
    # actual moment when they would be required
    if not LIBRARIES_LOADED: 
        raise LIBRARIES_ERROR
    
    files = [Path(f) for f in files]
    vertical_spacing    = DEFAULTS['plot.optmulti'].getfloat('vertical_spacing')
    marker_size         = DEFAULTS['plot.optmulti'].getfloat('marker_size')
    marker_opacity      = DEFAULTS['plot.optmulti'].getfloat('marker_opacity')
    threshold_color     = DEFAULTS['plot.optmulti']['threshold_color']
    threshold_linewidth = DEFAULTS['plot.optmulti'].getfloat('threshold_linewidth')
    cmap_name           = DEFAULTS['plot.optmulti']['cmap_name']

    # Create subplots
    fig = make_subplots(2, 4,
                        shared_xaxes=True,
                        shared_yaxes=False,
                        specs=[[{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter", "colspan": 2,"rowspan":2}, None],
                               [{"type": "scatter"}, {"type": "scatter"}, None, None]],
                        vertical_spacing = vertical_spacing
                        )
    #fig['layout']['xaxis']['title']  = 'iteration'
    #fig['layout']['xaxis2']['title'] = 'iteration'
    fig['layout']['xaxis3']['title'] = 'iteration'     # 2x2
    fig['layout']['xaxis4']['title'] = 'iteration'    
    fig['layout']['xaxis5']['title'] = 'iteration'

    fig['layout']['yaxis']['title']  = 'Maximum Force'
    fig['layout']['yaxis2']['title'] = 'RMS Force'
    fig['layout']['yaxis3']['title'] = 'Energy, hartree'    # 2x2
    fig['layout']['yaxis4']['title'] = 'Maximum Displacement'    # None
    fig['layout']['yaxis5']['title'] = 'RMS Displacement'

    cmap = get_cmap(cmap_name,len(files))
    colors = {f.stem:to_hex(cmap(i)) for i,f in enumerate(files)}
    button_list = []

    thresholds = None

    for ifile in files: 
        
        legendname = ifile.stem
        color = colors[legendname]
        try: 
            energies, forces, rmsforces, displacements, rmsdisplacements, _thresholds = parse_gaussian_data(ifile)
        except (AttributeError,ValueError):
            continue

        if (not energies and 
            not forces and 
            not rmsforces and 
            not displacements and
            not rmsdisplacements):
            continue
        
        if (thresholds is None) and (_thresholds is not None):
            thresholds = _thresholds

        x = [i+1 for i in range(len(energies))]
        fig.add_trace(go.Scatter(x=x,
                                 y=energies,
                                 marker=dict(color=color,opacity=marker_opacity,size=marker_size),
                                 line=dict(color=color),
                                 mode='lines+markers',
                                 hoverinfo='skip',
                                 name=legendname,
                                 legendgroup=legendname,
                                 showlegend=True),
                     row=1,col=3)
        fig.add_trace(go.Scatter(x=x,
                                 y=forces,
                                 marker=dict(color=color,opacity=marker_opacity,size=marker_size),
                                 line=dict(color=color),
                                 mode='lines+markers',
                                 hoverinfo='skip',
                                 name=legendname,
                                 legendgroup=legendname,
                                 showlegend=False),
                     row=1,col=1)
        fig.add_trace(go.Scatter(x=x,
                                 y=rmsforces,
                                 marker=dict(color=color,opacity=marker_opacity,size=marker_size),
                                 line=dict(color=color),
                                 mode='lines+markers',
                                 hoverinfo='skip',
                                 name=legendname,
                                 legendgroup=legendname,
                                 showlegend=False),
                     row=1,col=2)
        fig.add_trace(go.Scatter(x=x,
                                 y=displacements,
                                 marker=dict(color=color,opacity=marker_opacity,size=marker_size),
                                 line=dict(color=color),
                                 mode='lines+markers',
                                 hoverinfo='skip',
                                 name=legendname,
                                 legendgroup=legendname,
                                 showlegend=False),
                     row=2,col=1)
        fig.add_trace(go.Scatter(x=x,
                                 y=rmsdisplacements,
                                 marker=dict(color=color,opacity=marker_opacity,size=marker_size),
                                 line=dict(color=color),
                                 mode='lines+markers',
                                 hoverinfo='skip',
                                 name=legendname,
                                 legendgroup=legendname,
                                 showlegend=False),
                     row=2,col=2)

        button_list.append(legendname)
    
    #if thresholds is not None:
    fig.add_hline(y=thresholds[0], row=1, col=1, line_color=threshold_color, line_width=threshold_linewidth)
    fig.add_hline(y=thresholds[1], row=1, col=2, line_color=threshold_color, line_width=threshold_linewidth)
    fig.add_hline(y=thresholds[2], row=2, col=1, line_color=threshold_color, line_width=threshold_linewidth)
    fig.add_hline(y=thresholds[3], row=2, col=2, line_color=threshold_color, line_width=threshold_linewidth)

    fig.update_xaxes(matches='x')

    updatemenus=[dict(active=0,buttons=[]),]
    buttons = updatemenus[0]['buttons']

    ntraces_per_item = 5
    total_traces = ntraces_per_item*len(button_list)

    for i,button_label in enumerate(button_list): 
        visible = [False,]*total_traces
        start = ntraces_per_item*i
        stop = ntraces_per_item*(i+1)
        visible[start:stop] = [True,]*ntraces_per_item
        button = dict(method='update',
                      label=button_label,
                      visible=True,
                      args=[{"visible": visible*5}])
        buttons.append(button)

    # add a button to toggle all traces on and off
    button = dict(method='update',
                label='All',
                visible=True,
                args=[{'visible':True}])
    
    buttons.append(button)

    # add dropdown menus to the figure
    fig.update_layout(updatemenus=updatemenus)

    # LEGACY CODE:
    #if enable_legend:
    #    fig.update_layout(showlegend=True)

    if in_browser: 
        fig.show(renderer='browser')
    else:
        with open(outfile,'w') as F: 
            F.write(to_html(fig))
