.. _partial_runs:

Partial runs and re-running on the same folder
***********************************************

Dealing with the generation of large datasets can be a frustrating undertaking. One reason is that generation takes a long time and often there will be issues which only arise after a certain event happens. In this case, you will often be left with a broken, half-finished dataset.

This project is intended to be able to work with such partial data sets - and if you're careful, it might be able to recover from such states.

Being able to deal with partial data sets also means that you can speed up generation by spreading out the process over multiple computers and then aggregating the results into one final larger dataset.

One reason this is possible is that the pipeline is deterministic and all random values for a sample depend on the unique random seed of the sample. When writing your own blocks, make sure to also write deterministic code (see also :ref:`Random values and determinism <determinism>`).

We have tried to make the pipeline verbose enough to understand the state of the pipeline as well as the dataset.
While developing, make sure to read the output at the beginning of each run where the currently configured pipeline will be printed to the console, along with information about inputs and outpus for each block.
When in doubt, we recommend using the `src/analyze.py` script to try to understand the content of a (partially) generated dataset folder. Furthermore, we recommend experimenting with small runs of only a few samples to get used to the pipeline. If there is anything that could be made clearer, feel free to raise an issue.

Recovering from partial runs:
------------------------------

If a run aborts, you can usually simply run the pipeline again with the same parameters and it will pick up where it left off. It does this by checking for each block and sample which output files have been successfully generated and which are missing.
However, it will try to re-run blocks that have not produced useful output in a previous run, which often means it will re-run those blocks which have timed out. This can be avoided using the `--do_not_retry_blocks` argument added by the :class:`~core.pipeline.Pipeline` class.
Furthermore, keep in mind that this procedure cannot handle cases in which blocks failed outputting optional outputs. Furthermore, it will not re-run blocks which tell the pipeline that they never intent to output any files, such as the :class:`~blocks.scene_objects.scene_object_generator_block.SceneObjectGeneratorBlock`.

In cases where the automatic detection of failed blocks is not enough, you can force the re-execution of blocks by using the `--force_run_blocks` argument, which will ensure the pipeline runs the blocks passed to the argument no matter whether their output is already present or not.
This is also useful if you have decided to change some parameters (such that a certain block needs to be re-run for all samples).

Note that whenever a block is re-run, this will force the re-running of downstream blocks as well, because they may depend on the block's output.

Intentional partial runs:
--------------------------

You can run the pipeline only on certain samples by using the `--start_sample` and `--num_samples` arguments. These allow you to precisely control which samples to (re-)generate. Note however that this will produce statistics and plots only from the currently processed samples. If there are more samples from previous runs in the folder, you should re-run the pipeline at the end with the whole range of samples and the `--statistics_only` argument, which will only aggregate statistics and generate plots, but not run any pipeline blocks.

This method is also useful when using multiple computers: Use `--start_sample` and `--num_samples` to calculate a different range of samples on each computer, then copy them into a single folder and run again with `--statistics_only` to generate the plots.
(Note that we may add a script to do this automatically at some point).

When to delete data:
---------------------

When you add new pipeline blocks to your pipeline, but all previous blocks in the pipeline stay unchanged, you should be able to keep your dataset folders. However, when you start making larger changes, re-naming output files and changing a lot of configuration, it can be easier to delete your output folders and start generating new ones, because keeping track of which files come from older runs will start to get difficult. This is why we recommend testing your pipeline regularly with only a few samples passed to `--num_samples` and upscale only when you are confident that the pipeline is near completion.

