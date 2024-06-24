###############################################################
# Pipeline construction sample
# -------------------------------------------------------------
# This sample demonstrates how to construct and run a pipeline
# with scene generation, non-rigid deformation, partial
# intraoperative surface extraction and rigid misalignment.
# Run "python3 src/run_nonrigid_displacement.py --help" for an
# overview of parameters.
# -------------------------------------------------------------
# Copyright: 2022, Micha Pfeiffer, Eleonora Tagliabue
###############################################################

import argparse
import math

from core.pipeline import Pipeline
from core.dataset import Dataset
from core.log import Log
from blocks.scene_generation.random_scene_block import RandomSceneBlock
from blocks.scene_objects.scene_object_generator_block import SceneObjectGeneratorBlock
from blocks.meshing.gmsh_meshing_block import GmshMeshingBlock
from blocks.simulation.simulation_block import SimulationBlock
from blocks.simulation.sofa.simulation_scene import SofaSimulation
from blocks.displacement.calc_displacement_block import CalcDisplacementBlock
from blocks.surface_extraction.surface_extraction_block import SurfaceExtractionBlock
from core.objects.sceneobjects import DeformableOrgan, FixedAttachments, Force
from blocks.voxelization.voxelization_block import VoxelizationBlock

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



# Initialize the pipeline:
pipeline = Pipeline(**vars(args))


# Define which objects you want in your scene
scene_object_block = SceneObjectGeneratorBlock()
scene_object_block.add_object_template( DeformableOrgan, 
                {"size_x": 0.3,
                "size_y": 0.3,
                "size_z": (0.01,0.05),
                "young_modulus": (3000, 10000),
                "poisson_ratio": (0.45, 0.49),
                "add_concavity": False,
                "predeform_twist": True,
                "predeform_noise": True,
                "cut_to_fit": True,}
                )
scene_object_block.add_object_template( 
                FixedAttachments, 
                {"surface_amount": 0.05} 
                )
scene_object_block.add_object_template( 
                FixedAttachments, 
                {"ex_likelihood": 0.5,
                "surface_amount": 0.05} 
                )
scene_object_block.add_object_template( 
                Force, 
                {"magnitude": (0.05,0.55), 
                "roi_radius": (0.005, 0.01),
                "ang_from_normal": (0.0, 30)} 
                )
pipeline.append_block( scene_object_block )

# Build the pipeline by adding blocks to it.
# The order used here is important - blocks will later be run in this order as well.
scene_gen_block = RandomSceneBlock( pipeline.pipeline_blocks )
pipeline.append_block(scene_gen_block)

meshing_block = GmshMeshingBlock(
        input_filename="surface0.stl",
        output_filename="preop_volume.vtk",
        )
pipeline.append_block(meshing_block)

simulation_block = SimulationBlock(
        simulation_filename=meshing_block.output_filename,
        surface_filename="surface0.stl",
        output_filename="deformed.vtu",
        gravity=(0.0, 0.0, 0.0),
        simulation_class=SofaSimulation,
        export_time = 0.3,
        max_simulation_time=10,
        launch_gui=pipeline.launch_sofa_gui,
    )
pipeline.append_block(simulation_block)

surface_extraction_block = SurfaceExtractionBlock(
        input_filename=simulation_block.output_filename,
        output_filename="partial_intraop_surface.stl" 
        )
pipeline.append_block(surface_extraction_block)

calc_displ_block = CalcDisplacementBlock(
        initial_mesh_filename="preop_volume.vtk",
        displaced_mesh_filename=surface_extraction_block.output_filename,
        corresponding_indices=surface_extraction_block.extracted_indices,
        output_filename="preop_volume_with_displacement.vtu"
        )
pipeline.append_block(calc_displ_block)

voxelizationBlock = VoxelizationBlock(
        inputs = [
            {"filename": calc_displ_block.output_filename, 
            "signed": True, 
            "with_arrays": True,
            "center": True},
            ],
        output_filename = "voxelized.vts"
        )
pipeline.append_block(voxelizationBlock)

# Execute the pipeline, run each block for each sample in dataset:
pipeline.run( dataset )


