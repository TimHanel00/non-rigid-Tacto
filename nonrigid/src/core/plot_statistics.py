from math import floor, sqrt
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import os
from typing import Tuple, Dict, List
import numpy as np
import warnings
import matplotlib.ticker as mticker

from utils import dict_utils
from core.log import Log


def plot_histogram(
        data: dict,
        key: str,
        display_name: str = None,
        path: str =".",
        save: bool = True,
        **kwargs,
) -> (plt.figure, plt.axes):
    """ Plot a histogram of a statistic value as .eps file.

    Args:
        data: Nested dictionary of sample statistics/configs as
                    {sample.id: sample.statistics} = {sample.id: {key: value}}.
        key: Which statistic to plot: key of `statistics` dictionary. Also used as filename.
        display_name: Names of the statistic to be shown as x-axis label.
        path: Filepath (folder) to save the resulting plot to.
        save: If the plot should be saved to disk.

    Returns:
        fig, ax: The active matplotlib figure and axis for downstream styling control. The figure label
                 is the filename (without extension) that the plot has been/would have been saved to.

    """
    filename = f"{key}.eps"

    if save:
        plt.clf()
        fig = plt.gcf()
    else:
        fig = plt.figure()

    fig.set_label(f"{key}")
    ax = plt.gca()

    v = dict_utils.extract_values( data, [key] )
    values = v[0]
    if len(values) == 0:
        Log.log(severity="WARN", msg=f"No values passed to histogram! Skipping {filename}.", module="Analysis")
        return

    Log.log(module="Analysis", severity="INFO", msg=f"Plotting {key}, number of samples: {len(data)}")

    num_bins = max(floor(sqrt(len(data))), 20)
    plt.hist(values, bins=num_bins)

    full_filename = os.path.join(path, filename)
    if display_name is not None:
        plt.xlabel(display_name)
    else:
        plt.xlabel(key)
    plt.ylabel("# Samples")
    ax.yaxis.set_ticks_position('both')

    if save:
        plt.savefig(full_filename, bbox_inches='tight')

    Log.log(module="Analysis", severity="INFO", msg="Saved plot: " + full_filename)
    return fig, ax


def plot_xy(
        data,
        y_key: str,
        x_key = None,
        name: str = None,
        path: str = ".",
        x_label: str = "",
        y_label: str = "",
        save: bool = True,
        scatter: bool = False,
        **kwargs
) -> (plt.figure, plt.axes):
    """Create a simple line plot or scatter plot as .eps file.

    Args:
        y_key: Key of Y values to be plotted.
        x_key: X values associated with the y values. If None, x values will be the 0-based index of the y values.
        name: Filename for saving the plot (without extension).
        path: Filepath (folder) to save the resulting plot to.
        x_label: X axis display label.
        y_label: Y axis display label.
        save: If the plot should be saved to disk.
        scatter: Create scatter plot instead of line plot

    Returns:
        fig, ax: The active matplotlib figure and axis for downstream styling control. The figure label
                 is the filename (without extension) that the plot has been/would have been saved to.

    """
    if name is not None:
        filename = f"{name}.eps"
    elif x_key is not None:
        if scatter:
            filename = f"{y_key}_over_{x_key}_scatter.eps"
        else:
            filename = f"{y_key}_over_{x_key}_line_plot.eps"
    else:
        if scatter:
            filename = f"{y_key}_scatter.eps"
        else:
            filename = f"{y_key}_line_plot.eps"

    if save:
        plt.clf()
        fig = plt.gcf()
    else:
        fig = plt.figure()

    fig.set_label(f"{name}")
    ax = plt.gca()

    if x_key is not None:
        v = dict_utils.extract_values( data, [x_key, y_key] )
        x_vals = v[0]
        y_vals = v[1]
    else:
        v = dict_utils.extract_values( data, [y_key] )
        y_vals = v[0]
        x_vals = [i for i in range(len(y_vals))]

    if len(y_vals) == 0:
        Log.log(severity="WARN", msg=f"No values passed to line plot! Skipping {filename}.", module="Analysis")
        return

    # good to start plots at 0 most of the time
    xmax = max(x_vals)
    xmin = min(x_vals)
    ymax = max(y_vals)
    ymin = min(y_vals)
    if xmax > 0 and xmin > 0:
        plt.xlim(0, xmax + xmax / 20)
    elif xmax < 0 and xmin < 0:
        plt.xlim(xmin - xmin / 20, 0)
    if ymax > 0 and ymin > 0:
        plt.ylim(0, ymax + ymax / 20)
    elif ymax < 0 and ymin < 0:
        plt.ylim(ymin - ymin / 20, 0)

    if scatter == True:
        plt.scatter( x_vals, y_vals )
    else:
        plt.plot( x_vals, y_vals )

    full_filename = os.path.join(path, filename)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    ax.xaxis.set_ticks_position('both')
    ax.yaxis.set_ticks_position('both')
    plt.grid()
    ax.set_aspect('auto')
    ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins='auto', steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins='auto', steps=[1, 2, 5, 10]))

    if save:
        plt.savefig(full_filename, bbox_inches='tight')

    Log.log(module="Analysis", severity="INFO", msg = "Saved plot: " + full_filename)
    return fig, ax

def plot_boxplot(
        data: dict,
        keys: List[str],
        name: str,
        labels: List[str] = [],
        path: str = ".",
        y_label: str = "",
        save: bool = True,
        **kwargs
) -> (plt.figure, plt.axes):
    """ Create boxplot of data as .eps file.

    Args:
        data: Data as {display name of data series: data series (numerical)}.
        name: Name of the file to save the resulting plot to (without extension).
        path: Filepath (folder) to save the resulting plot to.
        y_label: Y axis display label.
        save: If the plot should be saved to disk.

    Returns:
        fig, ax: The active matplotlib figure and axis for downstream styling control. The figure label
                 is the filename (without extension) that the plot has been/would have been saved to.

    """
    filename = f"{name}.eps"

    if save:
        plt.clf()
        fig = plt.gcf()
    else:
        fig = plt.figure()

    fig.set_label(f"{name}")
    ax = plt.gca()

    values = dict_utils.extract_values( data, keys )

    if len(data) == 0:
        Log.log(severity="WARN", msg=f"Data dictionary passed to boxplot is empty! Skipping {filename}.",
                module="Analysis")
        return

    print("PLOTTING:", labels, keys)
    if len(labels) == 0:
        labels = keys

    print("PLOTTING:", labels, keys)

    msg = f"Plotting boxplot {filename}, number of boxes: {len(values)}"
    Log.log( module="Analysis", severity="INFO", msg=msg )

    # Ignore a warning introduced by changes in numpy: 
    warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    plt.boxplot( values, labels = labels )

    full_filename = os.path.join(path, filename)
    plt.xticks(rotation = 45, ha='right')
    plt.ylabel( y_label )

    if save:
        plt.savefig(full_filename, bbox_inches='tight')

    Log.log(module="Analysis", severity="INFO", msg = "Saved plot: " + full_filename)
    return fig, ax

def create_plot( plot_config, data, path ):

    if plot_config["type"] == "HISTOGRAM":
        plot_histogram( data,
                path = path,
                **plot_config
                )
    elif plot_config["type"] == "SCATTER":
        plot_xy( data,
                path = path,
                scatter = True,
                **plot_config
                )
    elif plot_config["type"] == "LINE":
        plot_xy( data,
                path = path,
                scatter = False,
                **plot_config
                )
    elif plot_config["type"] == "BOX":
        plot_boxplot( data,
                path = path,
                **plot_config
                )


#if __name__ == "__main__":
#
#    import argparse
#    import yaml
#
#    parser = argparse.ArgumentParser()
#    parser.add_argument("statistics_file", type=str)
#
#    args = parser.parse_args()
#
#
#    with open(args.statistics_file) as f:
#        statistics = yaml.load(f, Loader=yaml.SafeLoader)
#
#    print(f"Loaded statistics for {len(statistics)} samples.")
#
#    plot_histogram(statistics, "mean_displacement")
#    plot_histogram(statistics, "max_displacement")
#    plot_histogram(statistics, "partial_surface_area")

