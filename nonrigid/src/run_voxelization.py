###############################################################
# Pipeline construction sample
# -------------------------------------------------------------
# This sample demonstrates how to construct and run a pipeline
# with voxelization.
# Run "python3 src/run_voxelization.py --help" for an overview
# of parameters.
# -------------------------------------------------------------
# Copyright: 2022, Micha Pfeiffer, Eleonora Tagliabue
###############################################################

import argparse
import math

from core.pipeline import Pipeline
from core.dataset import Dataset
from core.log import Log
from blocks.scene_objects.scene_object_generator_block import SceneObjectGeneratorBlock
from blocks.scene_generation.random_scene_block import RandomSceneBlock
from blocks.displacement.rigid_displacement_block import RigidDisplacementBlock, RotationMode, RigidDisplacementMode
from blocks.displacement.calc_displacement_block import CalcDisplacementBlock
from blocks.meshing.gmsh_meshing_block import GmshMeshingBlock
from blocks.surface_extraction.surface_extraction_block import SurfaceExtractionBlock
from blocks.add_surface_noise.add_surface_noise_block import AddSurfaceNoiseBlock
from blocks.voxelization.voxelization_block import VoxelizationBlock
from core.objects.sceneobjects import Ligament, RigidOrgan, DeformableOrgan, AbdominalWall

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
pipeline = Pipeline(**vars(args))

# Define which objects you want in your scene
scene_object_block = SceneObjectGeneratorBlock()
scene_object_block.add_object_template( DeformableOrgan )
scene_object_block.add_object_template( RigidOrgan )
scene_object_block.add_object_template( AbdominalWall )
scene_object_block.add_object_template( Ligament,
        {"stiffness":(100,200), "rest_length_factor":(0.5, 1.2)} )
scene_object_block.add_object_template( Ligament,
        {"ex_likelyhood":0.7, "stiffness":(100,200), "rest_length_factor":(0.5, 1.2)} )
scene_object_block.add_object_template( Ligament,
        {"ex_likelyhood":0.1, "stiffness":(100,200), "rest_length_factor":(0.5, 1.2)} )
pipeline.append_block( scene_object_block )

# Build the pipeline by adding blocks to it.
# The order used here is important - blocks will later be run in this order as well.
scene_gen_block = RandomSceneBlock( pipeline.pipeline_blocks )
pipeline.append_block(scene_gen_block)

centeringBlock = RigidDisplacementBlock(
        input_filename = "surface_A.stl", 
        output_filename = "preop_surface_centered.stl",
        mode = RigidDisplacementMode.center,
        transform_name = "center" 
        )
pipeline.append_block(centeringBlock)

meshingBlock = GmshMeshingBlock(
        input_filename = centeringBlock.output_filename,
        output_filename = "preop_volume.vtk" 
        )
pipeline.append_block(meshingBlock)

rigidDisplacementBlock = RigidDisplacementBlock(
        input_filename = meshingBlock.output_filename, 
        output_filename = "intraop_volume.vtu",
        max_rotate = math.pi*0.1, 
        max_translate = 0.01, 
        rotation_center = RotationMode.origin
        )
        #max_rotate=math.pi*0.25, max_translate=0.01)
pipeline.append_block(rigidDisplacementBlock)

surfaceExtractionBlock = SurfaceExtractionBlock(
        input_filename = rigidDisplacementBlock.output_filename, 
        output_filename = "partial_intraop_surface.stl" 
        )
pipeline.append_block(surfaceExtractionBlock)

addSurfaceNoiseBlock = AddSurfaceNoiseBlock(
        input_filename = surfaceExtractionBlock.output_filename, 
        output_filename = "partial_intraop_surface_with_noise.stl" 
        )
pipeline.append_block(addSurfaceNoiseBlock)

calc_displ_block = CalcDisplacementBlock(
        initial_mesh_filename = "preop_volume.vtk",
        displaced_mesh_filename = "intraop_volume.vtu",
        output_filename = "preop_volume_with_displacement.vtu"
        )
pipeline.append_block(calc_displ_block)

voxelizationBlock = VoxelizationBlock(
        inputs = [
            {"filename": calc_displ_block.output_filename, "signed": True, "with_arrays": True},
            {"filename": addSurfaceNoiseBlock.output_filename, "signed": False}
            ],
        output_filename = "voxelized.vts"
        )
pipeline.append_block(voxelizationBlock)

# Execute the pipeline, run each block for each sample in dataset:
pipeline.run( dataset )


