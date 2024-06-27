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
import sys
import meshlib 
#import mrmeshpy

#from blocks.simulation.simulation_block import SimulationBlock

"""
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
"""
#import Sofa.Simulation
#import SofaRuntime, Sofa.Core,Sofa.Gui
def main():
    print("hello World")
    print(sys.path)
    meshlib.__version__
if __name__ == "__main__":
    main()
######################################
## Argument parsing:
