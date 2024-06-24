.. _building_pipeline:

Building your Pipeline
=================================

Since most projects will differ in what they want to do, a user will likely need to configure their own pipeline. Once all PipelineBlocks have been written, setting up a pipeline and running it is straight forward. Here's an example of configuring a pipeline and running it on a dataset (SampleBlock1 and SampleBlock2 both inherit from :class:`~core.pipeline_block.PipelineBlock`)::

    from core.pipeline import Pipeline
    from core.dataset import Dataset
    from blocks.sample.sample_blocks import SampleBlock1
    from blocks.sample.sample_blocks import SampleBlock2

    ######################################
    ## Argument parsing:
    import argparse
    # ... (left out for brevity)
    # ...

    ######################################
    ## Data loading:
    dataset = Dataset(args.data_path, args.num_samples)
    dataset.print_state()

    # Initialize the pipeline:
    pipeline = Pipeline(verbose=True)

    # Build the pipeline by adding blocks to it.
    # The order used here is important - blocks will later be run in this order as well.
    block1 = SampleBlock1()
    pipeline.append_block( block1 )

    block2 = SampleBlock2()
    pipeline.append_block( block2 )

    # Execute the pipeline, run each block for each sample in dataset:
    pipeline.run( dataset )

For more detailed examples, check out the run scripts in the "src" directory, such as `run_rigid_displacement.py`.
