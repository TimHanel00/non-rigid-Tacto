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
from blocks.copy_files.copy_files_block import CopyFilesBlock
from blocks.scene_objects.scene_object_generator_block import SceneObjectGeneratorBlock
from blocks.scene_generation.random_scene_block import RandomSceneBlock
from blocks.meshing.gmsh_meshing_block import GmshMeshingBlock
from blocks.simulation.simulation_block import SimulationBlock
from blocks.simulation.sofa.simulation_scene import SofaSimulation
from blocks.displacement.rigid_displacement_block import RigidDisplacementBlock, RotationMode, RigidDisplacementMode
from blocks.displacement.calc_displacement_block import CalcDisplacementBlock
from blocks.surface_extraction.surface_extraction_block import SurfaceExtractionBlock
from blocks.add_surface_noise.add_surface_noise_block import AddSurfaceNoiseBlock
from core.objects.sceneobjects import Ligament, RigidOrgan, DeformableOrgan, AbdominalWall, FixedAttachments, Force
from blocks.voxelization.voxelization_block import VoxelizationBlock
import Sofa.Gui

######################################
## Argument parsing:
parser = argparse.ArgumentParser("Sample run script")

Pipeline.add_arguments(parser)
Dataset.add_arguments(parser)
Log.add_arguments(parser)

parser.add_argument("--patient_input_file", type=str,
                    help="Custom organ mesh to be deformed")

args = parser.parse_args()

######################################
## Initialize logging:
Log.initialize( **vars(args) )

######################################
## Data loading:
dataset = Dataset(**vars(args))
dataset.print_state()

deformable_options = {
        "young_modulus":(3000,30000),
        "poisson_ratio":(0.45,0.48)
    }
if args.patient_input_file:
    deformable_options["source_file"] = "patient_input_mesh_rot.obj"

def_surface = f"{DeformableOrgan.file_basename}_A.{DeformableOrgan.file_extension}"

# Initialize the pipeline:
pipeline = Pipeline(**vars(args))


# Build the pipeline by adding blocks to it.
# The order used here is important - blocks will later be run in this order as well.

# If we were given patient data, use this as a basis for the scene.
if args.patient_input_file:
    # Copy the patient data to every sample:
    copy_block = CopyFilesBlock(
            path = args.patient_input_file,
            output_file_pattern="patient_input_mesh.obj"
            )
    pipeline.append_block(copy_block)

    rigid_init_block = RigidDisplacementBlock(
        input_filename = copy_block.output_file_pattern,
        output_filename = "patient_input_mesh_rot.obj",
        max_rotate = math.pi*2, 
        max_translate = 0,
        rotation_center = RotationMode.mean
        )
    pipeline.append_block( rigid_init_block )

##-------------------------------------------
## Add blocks which create the scene objects:
scene_object_block = SceneObjectGeneratorBlock()
scene_object_block.add_object_template( DeformableOrgan, deformable_options )
scene_object_block.add_object_template( AbdominalWall, {
            "fill_with_fat":True,
            "fat_amount":(0.4,0.8),
            "outset_amplitude":(0.03, 0.07),
            "outset_frequency":(3,10)
            })
scene_object_block.add_object_template( RigidOrgan )
scene_object_block.add_object_template( RigidOrgan )
scene_object_block.add_object_template( RigidOrgan, {
            "ex_likelyhood":0.2
            })
scene_object_block.add_object_template( Ligament, {
            "stiffness":(100,250),
            "rest_length_factor":(0.5, 1.2)
            })
scene_object_block.add_object_template( Ligament, {
            "ex_likelyhood":0.7,
            "stiffness":(100,250),
            "rest_length_factor":(0.5, 1.2)
            })
scene_object_block.add_object_template( Ligament, {
            "ex_likelyhood":0.5,
            "stiffness":(100,250),
            "rest_length_factor":(0.5, 1.2)
            })
scene_object_block.add_object_template( FixedAttachments, {
            "surface_amount":(0.02, 0.07)
            })
scene_object_block.add_object_template( FixedAttachments, {
            "ex_likelyhood":0.2, "surface_amount":(0.02, 0.05)
            })
pipeline.append_block( scene_object_block )


scene_gen_block = RandomSceneBlock( pipeline.pipeline_blocks )
pipeline.append_block(scene_gen_block)

meshing_block = GmshMeshingBlock(
        input_filename = def_surface,
        output_filename = "preop_volume.vtk",
        )
pipeline.append_block(meshing_block)

simulation_block = SimulationBlock(
        simulation_filename = meshing_block.output_filename,
        surface_filename = def_surface,
        output_filename = "deformed.vtu",
        simulation_class=SofaSimulation,
        launch_gui=pipeline.launch_sofa_gui,
        max_simulation_time = 2,
    )
pipeline.append_block(simulation_block)

rigid_displ_block = RigidDisplacementBlock(
        input_filename = simulation_block.output_filename,
        output_filename = "intraop_volume.vtu",
        max_rotate = math.pi*0.1, 
        max_translate = 0.01, 
        rotation_center = RotationMode.mean
        )
pipeline.append_block(rigid_displ_block)

surface_extraction_block = SurfaceExtractionBlock(
        input_filename = rigid_displ_block.output_filename,
        output_filename = "partial_intraop_surface.stl",
        surface_amount = (0.2,1.0)
        )
pipeline.append_block(surface_extraction_block)

add_surface_noise_block = AddSurfaceNoiseBlock(
        input_filename = surface_extraction_block.output_filename,
        output_filename = "partial_intraop_surface_with_noise.stl" 
        )
pipeline.append_block(add_surface_noise_block)

calc_displ_block = CalcDisplacementBlock(
        initial_mesh_filename="preop_volume.vtk",
        displaced_mesh_filename="intraop_volume.vtu",
        output_filename="preop_volume_with_displacement.vtu"
        )
pipeline.append_block(calc_displ_block)

voxelizationBlock = VoxelizationBlock(
        inputs = [
            {"filename": calc_displ_block.output_filename, "signed": True, "with_arrays": True},
            {"filename": add_surface_noise_block.output_filename, "signed": False}
            ],
        output_filename = "voxelized.vts"
        )
pipeline.append_block(voxelizationBlock)


######################################
## List of plots we want the pipeline to create:
pipeline.add_plot( {
        "type":"HISTOGRAM",
        "key":"stats|CalcDisplacementBlock_0|mean_displacement",
        "display_name":"Mean Displacement (m)"
    } )
pipeline.add_plot( {
        "type":"HISTOGRAM",
        "key":"stats|CalcDisplacementBlock_0|max_displacement",
        "display_name":"Max Displacement (m)"
    } )
pipeline.add_plot( {
        "type":"HISTOGRAM",
        "key":"stats|SurfaceExtractionBlock_0|partial_surface_area",
        "display_name":"Surface area (m^2)"
    } )
pipeline.add_plot( {
        "type":"HISTOGRAM",
        "key":"stats|SurfaceExtractionBlock_0|intraop_surface_num_points",
        "display_name":"Number of points"
    } )
pipeline.add_plot( {
        "type":"SCATTER",
        "y_key":"stats|CalcDisplacementBlock_0|mean_displacement",
        "x_key":"stats|CalcDisplacementBlock_0|mean_displacement",
        "display_name":"Mean Displacement (m)"
    } )


######################################
# Execute the pipeline, run each block for each sample in dataset:
pipeline.run( dataset )


