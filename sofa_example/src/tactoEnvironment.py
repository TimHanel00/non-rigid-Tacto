
import cv2
import hydra
import pybullet as p
import pybulletX as px
import trimesh
import pyrender
from stl import mesh
import numpy as np
import tacto
import threading
import logging
log = logging.getLogger(__name__)
def stlToPyrenderMesh(meshfile):
    stl_mesh = mesh.Mesh.from_file(meshfile)

    trimesh_mesh = trimesh.Trimesh(vertices=stl_mesh.vectors.reshape(-1, 3),
                                faces=np.arange(len(stl_mesh.vectors) * 3).reshape(-1, 3))
    pyrender_mesh = pyrender.Mesh.from_trimesh(trimesh_mesh)
def tactoLoop(digits):
    while True:
        color, depth = digits.render()
        digits.updateGUI(color, depth)
def tactoLaunch(cfg):
   
    # Load the config YAML file from examples/conf/digit.yaml

        # Initialize digits
    bg = cv2.imread("conf/bg_digit_240_320.jpg")
    digits = tacto.Sensor(**cfg.tacto, background=bg)
    
    # Initialize World
    log.info("Initializing world")
    px.init()

    p.resetDebugVisualizerCamera(**cfg.pybullet_camera)

    # Create and initialize DIGIT
    digit_body = px.Body(**cfg.digit)
    digits.add_camera(digit_body.id, [-1])

    # Add object to pybullet and tacto simulator
    obj = px.Body(**cfg.object)
    digits.add_body(obj)

    # Create control panel to control the 6DoF pose of the object
    panel = px.gui.PoseControlPanel(obj, **cfg.object_control_panel)
    panel.start()
    log.info("Use the slides to move the object until in contact with the DIGIT")

    # run p.stepSimulation in another thread
    t = px.utils.SimulationThread(real_time_factor=1.0)
    t.start()
    thread = threading.Thread(target=tactoLoop, args=(digits,))
    thread.start()
    thread.join()

