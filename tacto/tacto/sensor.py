# Copyright (c) Facebook, Inc. and its affiliates.

# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import collections
import logging
import os
import warnings
from dataclasses import dataclass

import cv2
import numpy as np
import pybullet as p
import trimesh
from urdfpy import URDF
import pyrender
from .renderer import Renderer

logger = logging.getLogger(__name__)


def _get_default_config(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)


def get_digit_config_path():
    return _get_default_config("config_digit.yml")


def get_digit_shadow_config_path():
    return _get_default_config("config_digit_shadow.yml")


def get_omnitact_config_path():
    return _get_default_config("config_omnitact.yml")

def swap(l1,i,l2,j):
    tmp=l1[i]
    l1[i]=l2[j]
    l2[j]=tmp
def degtoRad(angle):
    import math
    return angle*math.pi/180
def register(linkobj,dataReceive):
    if linkobj.sofaName=="":
            for obj in dataReceive.get().tolist():
                if obj.name=="Tissue" and linkobj.obj_id==2:
                    linkobj.sofaName=obj.name
                if obj.name=="Sensor" and linkobj.link_id==-1 and linkobj.obj_id==1:
                    linkobj.sofaName=obj.name
def getSofaName(linkobj):
    if linkobj.link_id==-1 and linkobj.obj_id==1:
        return "Sensor"
    if linkobj.obj_id==2:
        return "Tissue"
    return ""
def tissueHandle(link,sofaObject,pos,orient):
    link.mesh=sofaObject.mesh
    if link.mesh is not None:
        #print("updatingMesh")
        
        
        #print(self.mesh)
        vertices = link.mesh.vertices.tolist()  # Convert to list
        indices = link.mesh.faces.flatten().tolist()     # Convert to list
        #print(vertices)
        #print(indices)
        new_visual_shape = p.createVisualShape(
            shapeType=p.GEOM_MESH, 
            vertices=vertices, 
            indices=indices
        )
        new_collision_shape = p.createCollisionShape(shapeType=p.GEOM_MESH, vertices=vertices, 
            indices=indices)
        old_id=link.pybullet_id

        link.pybullet_id = p.createMultiBody(basePosition=pos,baseOrientation=orient,baseVisualShapeIndex=new_visual_shape, baseCollisionShapeIndex=new_collision_shape)
        from time import sleep
        sleep(0.01)
        p.removeBody(old_id)
                
    return pos,orient 
def sensorHandle(link,sofaObject,pos,orient):
    link.force=sofaObject.forces
    if link.force>10.0:
        print(link.force)
    p.resetBasePositionAndOrientation(link.obj_id, pos, p.getQuaternionFromEuler(orient))
    return pos,orient
def default(link,sofaObject,pos,orient):
    return pos,orient
costumFctDict={"Sensor":sensorHandle,"Tissue":tissueHandle,"":default}
@dataclass
class Link:
    obj_id: int  # ID used for Tacto (pyrender and initially pybullet)
    link_id: int  # pybullet link ID (-1 means base)
    cid: int  # physicsClientId
    internalPos=None
    internalRot=None
    initSofaPos=None
    force=None
    mesh=None
    sofaName=""
    pybullet_id: int #ID used explicitly for pybullet
    def get_pose(self,dataReceive=None):
        global costumFctDict
        
        #for k,v in dic:
            #print(v)
        p.setRealTimeSimulation(0)
        if self.link_id < 0:
            # get the base pose if link ID < 0
            position, orientation = p.getBasePositionAndOrientation(
                self.pybullet_id, physicsClientId=self.cid
            )
        else:
            # get the link pose if link ID >= 0
            position, orientation = p.getLinkState(
                self.pybullet_id, self.link_id, physicsClientId=self.cid
            )[:2]

        orientation = p.getEulerFromQuaternion(orientation, physicsClientId=self.cid)
        if self.internalPos==None and self.internalRot==None:
            self.internalPos=position
            self.internalRot=orientation
        #print(f'{self.link_id}+ obj Id: {self.obj_id}')
        """
        if( is digit sensor):
        
        
        print(dataReceive.latest_data)
        for i in range(3):
            dataReceive.latest_data.position[i]*=10
        """    
        #print(dataReceive.get())
        #print(position,orientation)
        #return dataReceive.get().position,dataReceive.get().orientation
        #print(str(position)+ " 1")
        pos=None
        orient=None
        self.sofaName=getSofaName(self)
        if dataReceive==None:
            #print("receiveNone")
            return position, orientation
        if dataReceive.latest_data is None:
            #print("receiveDataNone")
            return position, orientation
        dic=dataReceive.latest_data.getDict()
        if self.sofaName not in dic:
            #print("name not in dict")
            return position, orientation
        sofaObject=dataReceive.get(self.sofaName)
            
        pos=sofaObject.position
        
        orient=[degtoRad(i) for i in sofaObject.orientation]


        pos,orient =costumFctDict[self.sofaName](self,sofaObject,pos,orient)
                
        return pos,orient
        pos=(pos[0],pos[1],pos[2]+2)


class Sensor:
    def __init__(
        self,
        width=120,
        height=160,
        background=None,
        config_path=get_digit_config_path(),
        visualize_gui=True,
        show_depth=True,
        zrange=0.002,
        cid=0,
        dataReceive=None
    ):
        """

        :param width: scalar
        :param height: scalar
        :param background: image
        :param visualize_gui: Bool
        :param show_depth: Bool
        :param config_path:
        :param cid: Int
        """
        self.cid = cid
        self.renderer = Renderer(width, height, background, config_path)

        self.visualize_gui = visualize_gui
        self.show_depth = show_depth
        self.zrange = zrange
        self.dataReceiver=dataReceive
        self.cameras = {}
        self.nb_cam = 0
        self.objects = {}
        self.object_poses = {}
        self.normal_forces = {}
        self._static = None

    @property
    def height(self):
        return self.renderer.height

    @property
    def width(self):
        return self.renderer.width

    @property
    def background(self):
        return self.renderer.background
    def setDataReceiver(self,receiver):
        self.dataReceiver=receiver
    def add_camera(self, obj_id, link_ids):
        """
        Add camera into tacto

        self.cameras format: {
            "cam0": Link,
            "cam1": Link,
            ...
        }
        """
        if not isinstance(link_ids, collections.abc.Sequence):
            link_ids = [link_ids]

        for link_id in link_ids:
            cam_name = "cam" + str(self.nb_cam)
            self.cameras[cam_name] = Link(obj_id, link_id, self.cid,obj_id)
            self.nb_cam += 1

    def add_object(self, urdf_fn, obj_id, globalScaling=1.0):
        # Load urdf file by urdfpy
        robot = URDF.load(urdf_fn)

        for link_id, link in enumerate(robot.links):
            if len(link.visuals) == 0:
                continue
            link_id = link_id - 1
            # Get each links
            visual = link.visuals[0]
            obj_trimesh = visual.geometry.meshes[0]

            # Set mesh color to default (remove texture)
            obj_trimesh.visual = trimesh.visual.ColorVisuals()

            # Set initial origin (pybullet pose already considered initial origin position, not orientation)
            pose = visual.origin

            # Scale if it is mesh object (e.g. STL, OBJ file)
            mesh = visual.geometry.mesh
            if mesh is not None and mesh.scale is not None:
                S = np.eye(4, dtype=np.float64)
                S[:3, :3] = np.diag(mesh.scale)
                pose = pose.dot(S)

            # Apply interial origin if applicable
            inertial = link.inertial
            if inertial is not None and inertial.origin is not None:
                pose = np.linalg.inv(inertial.origin).dot(pose)

            # Set global scaling
            pose = np.diag([globalScaling] * 3 + [1]).dot(pose)

            obj_trimesh = obj_trimesh.apply_transform(pose)
            obj_name = "{}_{}".format(obj_id, link_id)

            self.objects[obj_name] = Link(obj_id, link_id, self.cid,obj_id)
            position, orientation = self.objects[obj_name].get_pose(self.dataReceiver)

            # Add object in pyrender
            self.renderer.add_object(
                obj_trimesh,
                obj_name,
                position=position,  # [-0.015, 0, 0.0235],
                orientation=orientation,  # [0, 0, 0],
            )

    def add_body(self, body):
        self.add_object(
            body.urdf_path, body.id, globalScaling=body.global_scaling or 1.0
        )

    def loadURDF(self, *args, **kwargs):
        warnings.warn(
            "\33[33mSensor.loadURDF is deprecated. Please use body = "
            "pybulletX.Body(...) and Sensor.add_body(body) instead\33[0m."
        )
        """
        Load the object urdf to pybullet and tacto simulator.
        The tacto simulator will create the same scene in OpenGL for faster rendering
        """
        urdf_fn = args[0]
        globalScaling = kwargs.get("globalScaling", 1.0)

        # Add to pybullet
        obj_id = p.loadURDF(physicsClientId=self.cid, *args, **kwargs)

        # Add to tacto simulator scene
        self.add_object(urdf_fn, obj_id, globalScaling=globalScaling)

        return obj_id

    def update(self):
        warnings.warn(
            "\33[33mSensor.update is deprecated and renamed to ._update_object_poses()"
            ", which will be called automatically in .render()\33[0m"
        )

    def _update_object_poses(self):
        """
        Update the pose of each objects registered in tacto simulator
        """
        
        for obj_name in self.objects.keys():
            self.object_poses[obj_name] = self.objects[obj_name].get_pose(self.dataReceiver)
            if self.objects[obj_name].mesh is not None:
                #print(type(self.objects[obj_name].mesh))
                #print(self.objects[obj_name].mesh)
                #print(type(self.renderer.current_object_nodes[obj_name].mesh))
                self.renderer.current_object_nodes[obj_name].mesh=pyrender.Mesh.from_trimesh(self.objects[obj_name].mesh)
                self.renderer.object_nodes[obj_name].mesh==self.objects[obj_name].mesh

    def get_force(self, cam_name):
        # Load contact force

        obj_id = self.cameras[cam_name].obj_id
        link_id = self.cameras[cam_name].link_id
        self.normal_forces[cam_name] = collections.defaultdict(float)
        if self.cameras[cam_name].force!=None:
            obj_name = "{}_{}".format(2, -1)
            self.normal_forces[cam_name][obj_name]=float(self.cameras[cam_name].force)
            return self.normal_forces[cam_name]
        pts = p.getContactPoints(
            bodyA=obj_id, linkIndexA=link_id, physicsClientId=self.cid
        )

        # accumulate forces from 0. using defaultdict of float

        for pt in pts:
            body_id_b = pt[2]
            link_id_b = pt[4]

            obj_name = "{}_{}".format(body_id_b, link_id_b)

            # ignore contacts we don't care (those not in self.objects)
            if obj_name not in self.objects:
                continue

            # Accumulate normal forces
            self.normal_forces[cam_name][obj_name] += pt[9]

        return self.normal_forces[cam_name]

    @property
    def static(self):
        if self._static is None:
            colors, _ = self.renderer.render(noise=False)
            depths = [np.zeros_like(d0) for d0 in self.renderer.depth0]
            self._static = (colors, depths)

        return self._static

    def _render_static(self):
        colors, depths = self.static
        colors = [self.renderer._add_noise(color) for color in colors]
        return colors, depths

    def render(self):
        """
        Render tacto images from each camera's view.
        """

        self._update_object_poses()
        colors = []
        depths = []

        for i in range(self.nb_cam):
            cam_name = "cam" + str(i)

            # get the contact normal forces

            normal_forces = self.get_force(cam_name)
            position, orientation = self.cameras[cam_name].get_pose(self.dataReceiver)
            
            self.renderer.update_camera_pose(position, orientation)
            if normal_forces:
                color, depth = self.renderer.render(position,orientation,object_poses=self.object_poses, normal_forces=normal_forces)

                # Remove the depth from curved gel
                for j in range(len(depth)):
                    depth[j] = self.renderer.depth0[j] - depth[j]
            else:
                color, depth = self._render_static()

            colors += color
            depths += depth

        return colors, depths

    def _depth_to_color(self, depth):
        gray = (np.clip(depth / self.zrange, 0, 1) * 255).astype(np.uint8)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def updateGUI(self, colors, depths):
        """
        Update images for visualization
        """
        if not self.visualize_gui:
            return

        # concatenate colors horizontally (axis=1)
        color = np.concatenate(colors, axis=1)

        if self.show_depth:
            # concatenate depths horizontally (axis=1)
            depth = np.concatenate(list(map(self._depth_to_color, depths)), axis=1)

            # concatenate the resulting two images vertically (axis=0)
            color_n_depth = np.concatenate([color, depth], axis=0)

            cv2.imshow(
                "color and depth", cv2.cvtColor(color_n_depth, cv2.COLOR_RGB2BGR)
            )
        else:
            cv2.imshow("color", cv2.cvtColor(color, cv2.COLOR_RGB2BGR))

        cv2.waitKey(1)
