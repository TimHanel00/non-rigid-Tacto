###############################################################
# Pipeline construction sample
# -------------------------------------------------------------
# This sample demonstrates how to construct and run a pipeline
# with scene generation, and rigid displacement
# Run "python3 src/run_rigid_displacement.py --help" for an
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
from blocks.scene_generation.random_scene_block import RandomSceneBlock
from blocks.scene_objects.scene_object_generator_block import SceneObjectGeneratorBlock
from blocks.displacement.rigid_displacement_block import RigidDisplacementBlock, RotationMode
from blocks.displacement.calc_displacement_block import CalcDisplacementBlock
from blocks.meshing.gmsh_meshing_block import GmshMeshingBlock
from blocks.surface_extraction.surface_extraction_block import SurfaceExtractionBlock
from blocks.add_surface_noise.add_surface_noise_block import AddSurfaceNoiseBlock
from core.objects.sceneobjects import DeformableOrgan, PortalVein, HepaticVein

######################################
## Argument parsing:
parser = argparse.ArgumentParser("Sample run script")

Pipeline.add_arguments(parser)
Dataset.add_arguments(parser)
Log.add_arguments(parser)

parser.add_argument("--patient_input_file", type=str,
                    help="Custom organ mesh to be displaced")
parser.add_argument("--max_ang_in_degrees", type=float, default=20)
parser.add_argument("--max_movement_in_meters", type=float, default=0.01)

args = parser.parse_args()

######################################
## Initialize logging:
Log.initialize( **vars(args) )

######################################
## Data loading:
dataset = Dataset(**vars(args))
dataset.print_state()

organ_options = {"young_modulus":(3000,30000),
        "poisson_ratio":(0.45,0.48)}

######################################
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

    # Let scene generation know to use this file:
    organ_options["source_file"] = "patient_input_mesh.obj"

##-------------------------------------------
## Add blocks which create the scene objects:
scene_object_block = SceneObjectGeneratorBlock()
organ_options["tag"] = "liver"
scene_object_block.add_object_template( DeformableOrgan, organ_options )
pipeline.append_block( scene_object_block )

scene_object_block.add_object_template(PortalVein, {"structure_tag": "liver",
                                        "curved": True,
                                        "tag": 'blood'
                                        })
scene_object_block.add_object_template(HepaticVein, {"structure_tag": "liver",
                                        "curved": True
                                        })

scene_gen_block = RandomSceneBlock( pipeline.pipeline_blocks )
pipeline.append_block(scene_gen_block)

meshingBlock = GmshMeshingBlock(
        input_filename="surface_A.stl",
        output_filename="preop_volume.vtk" )
pipeline.append_block(meshingBlock)

rigidDisplacementBlock = RigidDisplacementBlock(
        meshingBlock.output_filename, "intraop_volume.vtu",
        max_rotate=args.max_ang_in_degrees*math.pi/180,
        max_translate=args.max_movement_in_meters, rotation_center=RotationMode.mean)
        #max_rotate=math.pi*0.25, max_translate=0.01)
pipeline.append_block(rigidDisplacementBlock)

surfaceExtractionBlock = SurfaceExtractionBlock(
        rigidDisplacementBlock.output_filename, "partial_intraop_surface.stl" )
pipeline.append_block(surfaceExtractionBlock)

addSurfaceNoiseBlock = AddSurfaceNoiseBlock(
        surfaceExtractionBlock.output_filename, "partial_intraop_surface_with_noise.stl" )
pipeline.append_block(addSurfaceNoiseBlock)

calc_displ_block = CalcDisplacementBlock(
        initial_mesh_filename="preop_volume.vtk",
        displaced_mesh_filename="intraop_volume.vtu",
        output_filename="preop_volume_with_displacement.vtu")
pipeline.append_block(calc_displ_block)


######################################
## List of plots we want the pipeline to create:
pipeline.add_plot( {
        "type":"HISTOGRAM",
        "key":"stats|CalcDisplacementBlock_0|mean_displacement",
        "display_name":"Mean Displacement (m)"
    } )
pipeline.add_plot( {
        "type":"SCATTER",
        "y_key":"stats|CalcDisplacementBlock_0|mean_displacement",
        "x_key":"stats|CalcDisplacementBlock_0|mean_displacement",
        "display_name":"Mean Displacement (m)"
    } )
pipeline.add_plot( {
        "type":"BOX",
        "name":"unknown_name",
        "keys":[
            "configs|SurfaceExtractionBlock_0|target_surface_amount",
            "stats|SurfaceExtractionBlock_0|partial_surface_area"
            ],
        "labels":[
            "target_surface_amount",
            "actual_surface_amount"
            ],
    } )

######################################
# Execute the pipeline, run each block for each sample in dataset:
pipeline.run( dataset )


