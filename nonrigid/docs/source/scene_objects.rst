.. _scene_objects:

Scene Objects
*************************************

For each sample, the pipeline constructs a "Scene". The objects within this scene are called "Scene Objects". They may be organs, tools or fat tissue as well as boundary conditions.
To keep track of these, each :class:`~core.datasample.DataSample` conatins a list of scene objects, accessible via :meth:`~core.datasample.DataSample.get_scene_objects()`. A scene object is always an instance of a (subclass of) :class:`~core.objects.baseobject.BaseObject`.

The default Scene Object classes are given in the :mod:`~core.objects.sceneobjects` module.

Important: When you create your pipeline, these objects should not be created directly! This is because every :class:`~core.datasample.DataSample` instance will need to construct its scene with its own paramerters. For example, DataSample 10 may construct 2 ligaments with high stiffness and DataSample 30 may instead create 4 with a low stiffness.
This is why instead of instancing the scene objects yourself, you need to let the pipeline do this for you whenever it creates a new :class:`~core.datasample.DataSample`.
We solve this by using the :class:`~blocks.scene_objects.scene_object_generator_block.SceneObjectGeneratorBlock` to which you can add the scene objects to be created via :meth:`~blocks.scene_objects.scene_object_generator_block.SceneObjectGeneratorBlock.add_object_template()`. This serves two purposes:

#. Create scene objects upon demand, i.e. when a DataSample is created
#. Sample random parameter ranges in order to fill the parameters of the created scene objects with their specific values for this specific sample.

If you start programming your own types of scene objects, you should:

#. Subclass :class:`~core.objects.baseobject.BaseObject` for your own scene object.
#. Add a :class:`~blocks.scene_objects.scene_object_generator_block.SceneObjectGeneratorBlock` to your pipeline if you haven't already, call the :meth:`~blocks.scene_objects.scene_object_generator_block.SceneObjectGeneratorBlock.add_object_template()` method and pass a dictionary with all the key/value pairs which will be passed to the specific scene object's constructor. Note: You can pass a tuple here, which acts as the min and max values of the value, which will be sampled upon construction of the scene object. This allows creating objects with varying parameters when creating the object. See the example run_* scripts in the src directory. The additional "ex_likelihood" parameter should be a likelihood in the range of (0..1] of including this object in a specific sample. For example, if ex_likelihood is 0.5, roughly half of the scenes (i.e. half of the DataSamples) will have this object created for them.
#. The above will make sure that the pipeline will create the scene object. Now when the :class:`~core.pipeline_block.PipelineBlock`'s are run on this sample, they must handle your new scene object type correctly. For example, you might want to adapt the :class:`~blocks.scene_generation.random_scene_block.RandomSceneBlock` and the :class:`~blocks.simulation.simulation_block.SimulationBlock` to correctly handle your scene objects as well.
