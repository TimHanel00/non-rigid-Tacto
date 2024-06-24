###############################################################
# Plotting example using the Dataset class
# -------------------------------------------------------------
# This example demonstrates how to use the plotting utilities
# separated from a pipeline instance to inspect statistics
# and configuration values of a previously generated dataset.
# It generates:
# - histograms of statistic values
# - scatter plots of a statistic value over a config value
# - a line plot of cumulative time per sample and block
# - a box plot of time taken to run each block
# A dataset with the necessary configs and statistics can be
# obtained by running run_nonrigid_displacement.py.
# Run "python3 src/plot_results.py --help" for an
# overview of parameters.
# For more usage examples of the Dataset class see analyze.py.
# -------------------------------------------------------------
# Copyright: 2022, Micha Pfeiffer, Eleonora Tagliabue
###############################################################

import argparse
import os
import matplotlib.pyplot as plt

from core.dataset import Dataset
import core.plot_statistics as splot
from utils import dict_utils

# Todo: example dataset to docs or to git

# Todo: make sure that run_nonrigid_displacement.py generates these stats and configs:
#  ["partial_surface_area", "max_displacement"]
#  [("BaseObjectFactory|surface0.stl|young_modulus", "mean_displacement")]
#  "Timing_.."

######################################
## Argument parsing:
parser = argparse.ArgumentParser("Sample plot script")
Dataset.add_arguments(parser)
args = parser.parse_args()


######################################
## Data loading:
# create a dataset object from the dataset in the chosen folder
dataset = Dataset(**vars(args))
dataset.print_state()

# aggregate information about statistics and config values
statistics = dataset.aggregate_statistics(inspect_sample_past=True)
dataset.load_configs()
configs = dataset.aggregate_configs(inspect_sample_past=True)

# until statistics are stored in order of writing, we need some information about the block order in the previous run
block_order = {"RandomSceneBlock": 0,
               "GmshMeshingBlock": 1,
               "SimulationBlock": 2,
               "RigidDisplacementBlock": 3,
               "SurfaceExtractionBlock": 4,
               "AddSurfaceNoiseBlock": 5,
               "CalcDisplacementBlock": 6,
               "VoxelizationBlock": 7}


######################################
## Plot histograms for selected statistics and save:

# choose statistics values from statistics.yaml
# take care that these statistics have been produced for the chosen dataset
histogram_keys = ["partial_surface_area", "max_displacement"]
# give the statistics descriptive names as axis labels
histogram_display_names = ["Partial surface area", "Maximum displacement (m)"]

# make sure labels match specified statistics keys
histogram_display_names = splot.equalize_display_names(histogram_keys, histogram_display_names)

# create the plots and save to the dataset folder
# this can be done for all plot types
for i, stat_name in enumerate(histogram_keys):
    splot.plot_histogram(statistics, stat_name, histogram_display_names[i],
                                             path=dataset.data_path)


######################################
## Plot scatter plot for selected config-statistic pairs and obtain control over figure without saving:

# choose config value - statistics pairs from config.yaml and statistics.yaml
# configs are stored in a nested dictionary, key levels can be separated by | or : (see utils.extract_config)
# take care that these configs and statistics have been produced for the chosen dataset
scatter_key_pairs = [("BaseObjectFactory|surface0.stl|young_modulus", "mean_displacement")]
# give the configs and statistics descriptive names as axis labels
scatter_display_names = [["Young's modulus (Pa)", "Mean displacement (m)"]]

# make sure labels match specified configs-statistics pairs
scatter_display_names = splot.equalize_display_names(scatter_key_pairs, scatter_display_names)

# create the plots without saving and obtain control over figure for further downstream styling
# this can be done for all plot types
scatter_figs = []
for i, pair in enumerate(scatter_key_pairs):
    # don't save plot
    scatter_fig, scatter_ax = splot.plot_scatter(statistics, configs, pair, scatter_display_names[i],
                                                 path=dataset.data_path, save=False)
    # do some uniform styling
    scatter_fig.set_tight_layout(True)
    scatter_ax.yaxis.set_ticks_position('both')
    scatter_figs.append((scatter_fig, scatter_ax))

# do some individual styling
chosen_fig = scatter_figs[0][0]
chosen_fig.set_size_inches(5, 4)
# save in desired format
filename_without_extension = chosen_fig.get_label()
full_filename = os.path.join(dataset.data_path, f"{filename_without_extension}.svg")
chosen_fig.savefig(full_filename, transparent=True)


######################################
## Plot line for sample cumulative time consumption per block recorded in statistics:
# --------------------------
# collect time that each block took on the first sample
blocks = []
times = []
first_sample = list(statistics.keys())[0]
for key in statistics[first_sample].keys():
    if "Timing_" in key:
        block_name = key.split('_')[1]
        blocks.append(block_name)
        print(block_name)
        times.append(statistics[first_sample][key])
# sort block timings by order of pipeline processing
num_blocks = len(blocks)
ordered_vals = [val for (_, val) in sorted(zip(blocks, times), key=lambda x: block_order[x[0]])]
y_vals = [sum(ordered_vals[:(i+1)]) for i in range(len(ordered_vals))]
labels = sorted(blocks, key=lambda x: block_order[x])

# plot result
fig, ax = splot.plot_line(y_vals, name="first_sample_timeline", xlabel="Block", ylabel="seconds",
                          path=dataset.data_path, save=False)
ax.set_xticklabels(labels)
plt.xticks(rotation = 45)
filename = os.path.join(dataset.data_path, f"{fig.get_label()}.png")
fig.savefig(filename, bbox_inches='tight')


######################################
## Plot box plot for block timing recorded in statistics:
# --------------------------
# collect time per block over all samples
block_timings = {}
# find keys for all available timings in statistics, assuming that all samples have the same statistics
timing_keys = []
first_sample = list(statistics.keys())[0]
for key in statistics[first_sample].keys():
    if "Timing_" in key:
        timing_keys.append(key)
# loop through all samples and retrieve
for key in timing_keys:
    times = dict_utils.extract_statistic(statistics, key)
    block_name = key.split('_')[1]
    block_timings[block_name] = times

# plot result
splot.plot_boxplot(block_timings, "block_timing", path=dataset.data_path, y_label="seconds")

