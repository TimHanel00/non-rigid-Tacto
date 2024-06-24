.. _building_pipeline_blocks:

Building your own PipelineBlocks
*********************************

To add your own functionality to the pipeline, you should build your own subclass of :class:`~core.pipeline_block.PipelineBlock`.
There are 2 things you must do:

1. Implement an __init__() function to your class which calls the PipelineBlock's init function and passes the (unique) file names it requires as input as well as the (unique) filenames of files this block will create.
2. Implement a run() function which takes a DataSample as input, computes the block operation and instructs the DataSample to write its outputs, if applicable.

Example::

    class SampleBlock1(PipelineBlock):

        def __init__(self):
            inputs = []
            outputs = ["test.yaml"]
            super().__init__(inputs, outputs)

        def run(self, sample):

            sample.write("test.yaml", {"DATA":sample.id})
            #msg = f"Running SampleBlock on sample {sample.id}"
            #log(module="SampleBlock", msg=msg)
            if sample.id == 2:
                raise SampleProcessingException(self, sample, "I won't process blocks with ID 2.")

Adding PipelineBlocks to a Pipeline
====================================

This block can then be added to your pipeline like this::

    from core.pipeline import Pipeline
    from blocks.sample.sample_blocks import SampleBlock1

    # Initialize the pipeline:
    pipeline = Pipeline(verbose=True)

    # Initialize your block and add it to the pipeline:
    block1 = SampleBlock1()
    pipeline.append_block( block1 )


Note:

* A PipelineBlock should access data/files only through the DataSample's read/write functions.
* Usually, a single instance of your PipelineBlock will be created and used on all the DataSamples passed to its run function. However, this may happen across multiple threads/processes/(or in the future: computers). The block should not store any information specific to a DataSample; instead, use the DataSample's functions for this purpose.

Raising issues
===============================
Whenever a PipelineBlock encounters a sample for which it cannot successfully complete its functionality, it should raise a :class:`~core.exceptions.SampleProcessingException`. This could happen, for example, when a simulation does not converge or some criteria are not met by the sample. Note that the occurrence of such an exception is not considered a fatal error: The pipeline will continue to run for all other samples, but the current sample's processing will be stopped.

The message will also be logged in the sample's folder so that users can analyze the sample further to determine what went wrong.

Once your pipeline blocks have been built, you can :ref:`configure your pipeline and run it <building_pipeline>`.
