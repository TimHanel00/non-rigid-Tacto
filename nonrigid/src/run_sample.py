###############################################################
# Pipeline construction sample
# -------------------------------------------------------------
# This sample demonstrates how to construct and run a pipeline.
# Run "python3 src/run_sample.py --help" for an
# overview of parameters.
# Note that this sample does not produce any meaningful results,
# it only shows how to handle pipeline-setup. To construct your
# own pipeline, you can copy this sample and replace the
# pipeline blocks.
# -------------------------------------------------------------
# Copyright: 2022, Micha Pfeiffer, Eleonora Tagliabue
###############################################################



import argparse
import math

from core.pipeline import Pipeline
from core.dataset import Dataset
from core.log import Log
from blocks.sample.sample_blocks import SampleBlock1
from blocks.sample.sample_blocks import SampleBlock2

######################################
## Argument parsing:
parser = argparse.ArgumentParser("Sample run script")

Pipeline.add_arguments(parser)
Dataset.add_arguments(parser)
Log.add_arguments(parser)

args = parser.parse_args()

######################################
## Initialize logging:
Log.initialize( **vars(args) )

######################################
## Data loading:
dataset = Dataset(**vars(args))
dataset.print_state()

######################################
# Initialize the pipeline:
pipeline = Pipeline(**vars(args), verbose=True)

# Build the pipeline by adding blocks to it.
# The order used here is important - blocks will later be run in this order as well.
block1 = SampleBlock1()
pipeline.append_block( block1 )

block2 = SampleBlock2()
pipeline.append_block( block2 )

######################################
## List of plots we want the pipeline to create:
pipeline.add_plot( {
        "type":"HISTOGRAM",
        "key":"configs|SampleBlock1_0|eps-minus-id",
        "display_name":"eps minus ID"
    } )

######################################
# Execute the pipeline, run each block for each sample in dataset:
pipeline.run( dataset )


