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
from time import sleep
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
import sys
import multiprocessing
from threading import Thread
from sofa_controller import CostumController
from hydra import compose, initialize
import cv2
import hydra
import pybullet as p
import pybulletX as px
import copy
import tacto  # Import TACTO
import vtk
######################################
## Argument parsing:
digitsGlob = None
obj = None
def filter_args(args):
    filtered_args = [args[0]]
    for arg in args:
        if args=="--show_full_errors":
            filtered_args.append(arg)
        print(arg)
    # Filter out arguments you want to ignore
    filtered_args = [args[0]]
    return filtered_args

def runTacto():
    sys.argv = filter_args(sys.argv)
    setupTacto()

    t = px.utils.SimulationThread(real_time_factor=1.0)
    t.start()

    while True:
    #update position and orientation of obj in sofa simulation
    #update the mesh incase of a deformation
        color, depth = digitsGlob.render()
        digitsGlob.updateGUI(color, depth)

    t.stop()
@hydra.main(config_path="../conf", config_name="digit")
def setupTacto(cfg):
    bg = cv2.imread("../conf/bg_digit_240_320.jpg")
    global digitsGlob
    digitsGlob = tacto.Sensor(**cfg.tacto, background=bg)
    px.init()
    p.resetDebugVisualizerCamera(**cfg.pybullet_camera)
    digit_body = px.Body(**cfg.digit)
    digitsGlob.add_camera(digit_body.id, [-1])
    global obj
        # Add object to pybullet and tacto simulator
    obj = px.Body(**cfg.object)
    digitsGlob.add_body(obj)

        # Create control panel to control the 6DoF pose of the object
    panel = px.gui.PoseControlPanel(obj, **cfg.object_control_panel)
    panel.start()
    #log.info("Use the slides to move the object until in contact with the DIGIT")
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
        gravity=(0.0,0.0,0.0),
        simulation_class=CostumController,
        launch_gui=True,
        max_simulation_time = 2,
    )
pipeline.append_block(simulation_block)

######################################
## List of plots we want the pipeline to create:

######################################
# Execute the pipeline, run each block for each sample in dataset:


sofaThread = multiprocessing.Process(target = pipeline.run( dataset ))
tactoThread = multiprocessing.Process(target = runTacto())
tactoThread.start()
print(" awdopijawodawdwadawdawdawdawdawdawdij")
#sleep(10)

sofaThread.start()
#


