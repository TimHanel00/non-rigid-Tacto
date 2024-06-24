Troubleshooting
================

The pipeline has grown into a large project with multiple dependencies and parallelism, and debugging it is not always easy.
Here are a few pointers to get you started:

Note: If the pipeline ends with a message like::

    [OK|Pipeline] Pipeline finished. 4 of 10 (40.0%) samples processed successfully

this is usually not considered an error. This simply means that some of the samples could not be processed, for whatever reason. This may be due to instable simulations (which often occur due to the random nature of the simulation space), invalid meshing (which often occurs due to the random mesh setup) or similar. Still, you may be able to track down where the issue lies and figure how to make more samples process correctly.

Analyze
------------

The first thing to do after encountering issues is to analyze the resulting folder::

    python3 src/analyze.py --data_path [YOUR_DATA_PATH]

This will list the encountered issues for all samples. Each issue also mentions the block in which the issue occurred.

Log files
------------

There is a lot of log output for each sample. Usually, the logs from multiple data samples are mixed together due to the parallel processing of the samples, and some logs are hidden to not convolute the console too much. To dive deeper into issues for a sample, you can access the `log.log` and `issues.log` files, which are created in each of the data sample folders. Usually, it probably makes sense to look at the end of these files first, to see where the processing of the sample was aborted (and why).

Running sequentially
----------------------

It can help to run the pipeline sequentially in order to get clearer error messages, using the "--run_sequential" argument. This will parse the samples one by one instead of parsing multiple samples at the same time, making the output clearer::

   python3 src/run_[...].py --data_path [YOUR_DATA_PATH] --num_samples 10 --run_sequential


