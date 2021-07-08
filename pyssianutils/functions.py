"""
This module provides a set of functions with general utilities. If
matplotlib.pyplot is available the Plot Functions become available
"""

# General Utils
def write_2_file(File):
    """
    Creates a wrapper for appending text to a certain File. Assumes that each
    call is equivalent to writing a single line.
    """
    def Writer(txt):
        with open(File,'a') as OFile:
            OFile.write(txt)
            OFile.write('\n')
    return Writer

# GaussianOutFile utils
def thermochemistry(GOF):
    """
    Returns the Zero Point Energy, Enthalpy and Free Energy
    from a frequency calculation.

    Parameters
    ----------
    GOF : GaussianOutFile

    Returns
    -------
    tuple
        (Z, H, G)
    """
    Link = GOF[-1].get_links(716)[-1]
    Z = Link.zeropoint[-1]
    H = Link.enthalpy[-1]
    G = Link.gibbs[-1]
    return Z, H, G
def potential_energy(GOF,method='default'):
    """
    Returns the last potential energy of a GaussianOutFile of a certain
    method. The default is the energy of the SCF cycle ('SCF Done:')

    Parameters
    ----------
    GOF : GaussianOutFile
    Method : string
        For DFT and HF the default behavior is correct. For Post-HF methods
        it needs to be specified. Currently: ['mp2','mp2scs','MP4','ccsdt']
    Returns
    -------
    float
        Energy
    """
    if method == 'mp2': # Search for MP2 energy
        energy = GOF.get_links(804)[-1].MP2
    elif method == 'mp2scs':
        HF = GOF.get_links(502)[-1].energy
        SCS_corr = GOF.get_links(804)[-1].get_SCScorr()
        energy = HF + SCS_corr
    elif method == 'ccsdt': # Search for CCSD(T) energy or default to MP4
        Aux = GOF.get_links(913)[-1]
        energy = Aux.CCSDT
    elif method == 'mp4':
        Aux = GOF.get_links(913)[-1]
        energy = Aux.MP4
    else: # Otherwise go to the "Done(...)" Energy
        energy = None
        if 508 in GOF._Parsers: 
            energy = GOF.get_links(508)[-1].energy
        if 502 in GOF._Parsers and energy is None:
            energy = GOF.get_links(502)[-1].energy
    return energy

# Console Utils
def print_convergence(GOF,JobId,Last=False):
    """
    Displays the Convergence parameters for a certain InternalJob of a
    GaussianOutFile.

    Parameters
    ----------
    GOF : GaussianOutFile
        Gaussian File whose convergence parameters are going to be displayed.
    JobId : int
        InternalJob number in the Gaussian Output File.
    Last : bool
        If enabled only the last set of parameters is displayed
        (the default is False).
    """
    if Last:
        GOF[JobId].get_links(103)[-1].print_convergence()
    else:
        for i,L in enumerate(GOF[JobId].get_links(103)):
            print(i)
            L.print_convergence()
def print_thermo(GOF):
    """
    Prints in the console the thermochemistry of a GaussianOutFile.

    Parameters
    ----------
    GOF : GaussianOutFile
        Gaussian File whose thermochemistry is going to be displayed.
    """
    Z,H,G = thermochemistry(GOF)
    U = potential_energy(GOF)
    print(f"{'U': ^14}\t{'Z': ^14}\t{'H': ^14}\t{'G': ^14}")
    print(f"{U: 03.9f}\t{Z: 03.9f}\t{H: 03.9f}\t{G: 03.9f}")

# If the matplotlib module is available, create these functions
try:
    import matplotlib.pyplot as pyplot
except ImportError:
    pass
else:
    # Plotting Utils
    def PlotConvergence(GOF,JobId):
        """
        The plot version of print_convergence.

        Parameters
        ----------
        GOF : GaussianOutFile
            Gaussian File whose convergence parameters are going to be displayed.
        JobId : int
            InternalJob number in the Gaussian Output File.

        Returns
        -------
        matplotlib.figure.Figure, list 
            matplotlib figure object with the convergence already included and a
            list of numbers with the thresholds of convergence for each parameter.
        """
        HEIGHT = 800
        WIDTH = 600
        DPI = 100.0
        Links = GOF[JobId].get_links(103)
        #Items = [map(lambda x: x.Value,i.conversion) for i in Links
        #        if i.conversion]
        #Force, RMSForce, Disp, RMSDisp = zip(*Items)
        Force = []
        RMSForce = []
        Disp = []
        RMSDisp = []
        for i,items in enumerate([link.conversion for link in Links]):
            for item in items:
                if item.Item == "Maximum Force":
                    Force.append((i,item.Value))
                elif item.Item == "RMS Force":
                    RMSForce.append((i,item.Value))
                elif item.Item == "Maximum Displacement":
                    Disp.append((i,item.Value))
                elif item.Item == "RMS Displacement":
                    RMSDisp.append((i,item.Value))
        thresholds = []
        for item in items:
            if item.Item == "Maximum Force":
                thresholds.append(item.Threshold)
                break
        for item in items:
            if item.Item == "RMS Force":
                thresholds.append(item.Threshold)
                break
        for item in items:
            if item.Item == "Maximum Displacement":
                thresholds.append(item.Threshold)
                break
        for item in items:
            if item.Item == "RMS Displacement":
                thresholds.append(item.Threshold)
                break
        #f,((ax1,ax2),(ax3,ax4)) = pyplot.subplots(2,2,figsize=(HEIGHT/DPI,WIDTH/DPI))
        f = pyplot.figure(figsize=(HEIGHT/DPI,WIDTH/DPI))
        ## Handpicked axes positioning
        x_sep = 0.125
        y_sep = 0.075
        x_mar = y_mar = 0.1
        w = 0.35
        h = 0.375
        bot = y_mar
        left = x_mar
        mbot = bot + h + y_sep
        mleft = left + w + x_sep
        ax1 = f.add_axes([left,  mbot, w, h])
        ax2 = f.add_axes([mleft, mbot, w, h])
        ax3 = f.add_axes([left,  bot,  w, h])
        ax4 = f.add_axes([mleft, bot,  w, h])
        ## End
        Labels = ["Force","RMSForce","Displacement","RMSDisplacement"]
        axes = [ax1,ax2,ax3,ax4]
        x = range(len(Force))
        items = [Force, RMSForce, Disp, RMSDisp]
        for ax,label,item in zip(axes,Labels,items):
            if item:
                x,y = zip(*item)
                ax.set_ylabel(label)
                ax.plot(x,y)
        return f, thresholds
    def PlotThresholds(fig,thresholds=None):
        """
        Convenience function to plot horizontal lines for the figure produced
        by PlotConvergence.

        Parameters
        ----------
        fig : matplotlib.figure.Figure
            Figure where the thresholds are going to be drawn
        thresholds : list
            List of the threshold values of len==4
            (the default is [0.000450,0.0003,0.0018,0.0012]).

        """
        if thresholds is None:
            thresholds = [0.000450,0.0003,0.0018,0.0012]
        for i,j in zip(fig.axes,thresholds):
            xlim = i.get_xlim()
            i.plot(xlim,(j,j),'r')
            i.set_xlim(xlim)
    def PlotInternalEnergy(GOF,UnitConverter=None):
        """
        Function that plots the potential energy during a Gaussian calculation.

        Parameters
        ----------
        GOF : GaussianOutFile
            Gaussian File whose potential energy is going to be displayed.
        UnitConverter : (str,function)
            tuple where the first value is the unit to be used and the second
            the function to transform the values in hartrees to the desired unit
            (the default is None).

        Returns
        -------
        matplotlib.figure.Figure
            matplotlib figure object with the convergence already included
        """
        if UnitConverter is None:
            UnitConverter = ("hartree",lambda x: x)
        Energies = [Link.energy for Link in GOF.get_links(502) if Link.energy]
        Energy = list(map(UnitConverter[-1],Energies))
        x = range(len(Energy))
        HEIGHT = 800
        WIDTH = 600
        DPI = 100.0
        fig = pyplot.figure(figsize=(HEIGHT/DPI,WIDTH/DPI))
        ax = pyplot.gca()
        ax.plot(x,Energy)
        ax.set_ylabel(f"Potential Energy {UnitConverter[0]}")
        ax.set_xlabel("Step number")
        return fig
