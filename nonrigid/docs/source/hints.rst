Hints and Remarks
*************************

Units
========

Although, strictly speaking, the pipeline is mostly agnostic to scale and units, we use SI units throughout the project and strongly recommend that you do, too. The medical field often uses millimeters instead of meters, but we have decided that using Meters makes it easier to keep everything consistent and to parameterize other values such as pressure, gravity or elasticity. Furthermore, it has the nice side-effect that - since organs are usually several centimeters in size - resulting outputs are often in the range of ~0.01 to ~0.1, which is well suited for our deep learning settings.

Random values and determinism
===============================
.. _determinism:

We recommend to keep the pipeline you build deterministic, as it makes debugging and reproducing results much easier. Since PipelineBlocks may be called in any random order, using python's random.random() function (and similar) should be avoided.

Instead, each DataSample provides its own random number generator (seeded once at startup with the DataSample's ID), which can be accessed through :py:attr:`core.datasample.DataSample.random`. This is an instance of the :code:`random.Random()` class, so it can be used to sample random values using :code:`random.random()`, :code:`random.uniform()` etc.


Print Dataset Results
===========================

To analyze a dataset after creating it, try using the `src/analyze.py` script, like so:

.. code-block:: bash

    python3 src/analyze.py --data_path path/to/my/dataset

See :code:`python3 src/analyze.py --help` for more options.

