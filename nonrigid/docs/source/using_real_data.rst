.. _using_real_data:

Using real patient data in your pipeline
*****************************************

One of the pipeline's core features is that it can generate organ-like structures and scenes automatically. However, to test whether your applications could also work with real meshes, the simulations can also be run on meshes extracted from patient data.
Testing on such a simulated scenario doesn't replace testing on phantom or real data, but it may give insights into the strengths and weaknesses the developped downstream methods.

Note: The "src/run_rigid_displacement.py" and "src/run_nonrigid_displacement.py" samples show how examples of how to set up a full pipeline to optionally use real data, however we recommend reading through the following first.

Step 1: Add your input meshes
------------------------------

Adding patient meshes is in theory very simple: All if takes is a :class:`~blocks.copy_files.copy_files_block.CopyFilesBlock` which must be added to the beginning of your pipeline::

    copy_block = CopyFilesBlock(
            path = "path/to/file.obj",
            output_filename = "patient_input_mesh.obj"
            )
    pipeline.append_block(copy_block)

This block will take the (single) file "file.obj" and copy it into every DataSample's folder under the new name "patient_input_mesh.obj". Following blocks can then use this file in their calculations, such as meshing and simulating.

(Note that if you have data from multiple patients, you can use the CopyFilesBlock's 'distribute' argument to distribute the files to the different samples automatically.)

However, in practice, meshes derived from patient files are often quite messy. You can try to clean up the meshes manually, or use the :class:`~blocks.scene_generation.clean_mesh_block.CleanMeshBlock`. (Note that if you just add this block to the pipeline after the copy block it will run on every data sample - which is fine but wastes a bit of time. An alternative would be to set up a pipeline which just cleans the mesh, and then use that cleaned file as input to your actual pipeline).

You should also take care of scales in this step. We recommend to use SI units. Since most patient meshes tend to be represented in millimeters, you could scale to meters as a first step. You can do this manually, or by using the :class:`~blocks.displacement.rigid_displacement_block.RigidDisplacementBlock` with a fixed, constant transform which scales the mesh.

Step 2: Adjust your scene generation
-------------------------------------

If you have a :class:`~blocks.scene_generation.random_scene_block.RandomSceneBlock` in your pipeline, you will need to tell it to not generate a new patient organ, but instead load and use the given patient file. The easiest way to do this is to let the scene object know that you have a source file for it.
This is done by passing a "source_file" parameter to the scene object (or rather, the :class:`~blocks.scene_objects.scene_object_generator_block.SceneObjectGeneratorBlock`, which creates the scene object later on)::

    scene_object_block = SceneObjectGeneratorBlock()
    scene_object_block.add_object_template( DeformableOrgan,
            params = { "source_file":"patient_input_mesh.obj" }
            )
    pipeline.append_block( scene_object_block )

This will pass the "source_file" parameter to the DeformableOrgan when it is generated, to let the system know that there is a source file to use for this object.

When the RandomSceneBlock gets to generating this organ, it will notice that there is a source_file parameter present and will load this instead of generating a new mesh.


This whole process may seem rather complicated, but the nice thing about it is that it allows the generated scenes to be partially random, i.e. you can use a real liver mesh and let the pipeline generate random surrounding organs and boundary conditions.

