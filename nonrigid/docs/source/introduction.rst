Introduction
*******************

The core of this project is made up of three important components:

* The :class:`~core.datasample.DataSample` class holds all data relevant for exactly one simulation.
* A number of :class:`~core.pipeline_block.PipelineBlock` classes, each performing a single task for a simulation (like a necessary preprocessing step, or some metric calculation)
* The :class:`~core.pipeline.Pipeline` class which is responsible for handling all PipelineBlocks and running them all on each DataSample

The DataSample
====================

The :class:`~core.datasample.DataSample` class represents a single simulation. It stores all of its information in a single folder and gives read and write access to these files.
A DataSample is considered "valid" as long as none of the PipelineBlocks have reported an issue with it. As soon as an issue is encountered (such as a simulation that doesn't converge, intersecting triangles etc.) the PipelineBlocks may raise an error which gets stored with the DataSample. In this case, subsequent PipelineBlocks in the Pipeline will not be called on this DataSample.

The DataSample class also stores logs for the given sample, as well as meta-info such as statistics for easier access.

The PipelineBlock
====================

Each functionality of the Pipeline is implemented in a subclass of the :class:`~core.pipeline_block.PipelineBlock` class. Examples could be:

* generating a mesh
* extracting a surface
* adding noise

Each block also tells the Pipeline which inputs and outputs it needs. In this way, the Pipeline can determine whether a PipelineBlock needs to be run on a certain DataSample or whether the output files are already present.

When adding your own functionality, you should do this by subclassing the PipelineBlock. See :ref:`building_pipeline_blocks` for more details.

The Pipeline
====================

The :class:`~core.pipeline.Pipeline` class starts and controls the process of calling each PipelineBlock on each DataSample. Depending on how the Pipeline is configured, this workload may be spread out across multiple threads/processes or computers. For a single DataSample, we guarantee that the blocks are called in order, but there is no guarantee that sample i will be finished before sample i+1 is finished (Note: we added a flag to process samples in-order for debugging purposes).

The pipeline also aggregates the statistics from all samples into one single file for easier overview and generates plots of these statistics (TODO).


