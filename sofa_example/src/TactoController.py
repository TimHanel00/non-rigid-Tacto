from meshlib import mrmeshpy
import os
import math 
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from splib3.numerics import RigidDof
from splib3.numerics.quat import Quat
import splib3.numerics.quat
import numpy as np
from stl import mesh
import trimesh
import heapq
def readMesh():
    your_mesh = mesh.Mesh.from_file('mesh/.stl')

def get_rotation_matrix(angles):
    roll=angles[0]
    pitch=angles[1]
    yaw=angles[2]
    # Roll (rotation around X-axis)
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)]])
    
    # Pitch (rotation around Y-axis)
    R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])
    
    # Yaw (rotation around Z-axis)
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0],
                    [0, 0, 1]])
    
    # Combined rotation matrix (ZYX order)
    R = np.dot(R_z, np.dot(R_y, R_x))
    
    return R

def transform_to_global(local_point, orientation, position):
    rotation_matrix=get_rotation_matrix(orientation)
    # Convert the point to a numpy array for easier matrix operations
    local_point = np.array(local_point)
    translation_vector = np.array(position)
    
    # Apply the transformation: rotate then translate
    global_point = np.dot(rotation_matrix, local_point) + translation_vector
    return global_point
class ForcesController(Sofa.Core.Controller):
    def __init__(self, *args, **kwargs):
        # These are needed (and the normal way to override from a python class)
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.rootNode = kwargs.get("rootNode")
    def onAnimateEndEvent(self, event):
        """
        # 处理 Sphere 的力
        try:
            sphere_constraint = self.rootNode.Tacto.collision.MechanicalObject.constraint.value
            # print("sphere_constraint", sphere_constraint)
        except AttributeError:
            print("Unable to find attribute: MechanicalObject for Sphere")
            return
        sphere_dt = self.rootNode.dt.value
        sphere_constraintMatrixInline = np.fromstring(sphere_constraint, sep='  ')
        # print("sphere_constraintMatrixInline:", sphere_constraintMatrixInline)
        sphere_pointId = []
        sphere_constraintId = []
        sphere_constraintDirections = []
        sphere_index = 0
        i=0
        # 获取约束力
        forcesNorm = self.rootNode.GCS.constraintForces.value
        acc=0.0
        for i in forcesNorm:
            if i>0:
                print("heureka")
                print(i)
                acc+=i
        print(f'Sum of Forces: {acc}')
        """
def calcNormalVec(node):
    sphere_constraint =node.rigidobject.constraint.value
    sphere_dt = node.parent.dt.value
    sphere_constraintMatrixInline = np.fromstring(sphere_constraint, sep='  ')
    # print("sphere_constraintMatrixInline:", sphere_constraintMatrixInline)

    sphere_pointId = []
    sphere_constraintId = []
    sphere_constraintDirections = []
    sphere_index = 0
    i=0

    # 获取约束力
    forcesNorm = node.parent.GCS.constraintForces.value
    print(forcesNorm)
    
    # 在 onAnimateEndEvent 中的现有代码基础上，添加总力累加变量
    contactforce_x = 0
    contactforce_y = 0
    contactforce_z = 0


    # 解析约束矩阵
    while sphere_index < len(sphere_constraintMatrixInline):
        currConstraintID=int(sphere_constraintMatrixInline[sphere_index])
        nbConstraint = int(sphere_constraintMatrixInline[sphere_index + 1])
        for pts in range(nbConstraint):
            currIDX=sphere_index+2+pts*4
            sphere_pointId=np.append(sphere_pointId,sphere_constraintMatrixInline[currIDX])
            sphere_constraintId.append(currConstraintID)
            sphere_constraintDirections.append([sphere_constraintMatrixInline[currIDX+1],sphere_constraintMatrixInline[currIDX+2],sphere_constraintMatrixInline[currIDX+3]])
        sphere_index=sphere_index+2+nbConstraint*4

    sphere_nbDofs = len(sphere_constraint)
    sphere_forces = np.zeros((sphere_nbDofs, 3))

    print(f"Parsed Point IDs: {sphere_pointId}")
    print(f"Parsed Constraint Directions: {sphere_constraintDirections}")
    print(f"forcesNorm: {forcesNorm}")

    # 计算并累加力
    for i in range(len(sphere_pointId)):
        indice = int(sphere_pointId[i])
        #print(f"Calculating force for point {indice}")

        sphere_forces[indice][0] += sphere_constraintDirections[i][0] * forcesNorm[sphere_constraintId[i]] / sphere_dt
        sphere_forces[indice][1] += sphere_constraintDirections[i][1] * forcesNorm[sphere_constraintId[i]] / sphere_dt
        sphere_forces[indice][2] += sphere_constraintDirections[i][2] * forcesNorm[sphere_constraintId[i]] / sphere_dt
        #print(f"Force on point {indice}: {sphere_forces[indice]}")

        # print('indice',i,indice)
    # 累加总力
    for i in range(sphere_nbDofs):
        contactforce_x += sphere_forces[i][0]
        contactforce_y += sphere_forces[i][1]
        contactforce_z += sphere_forces[i][2]
        #print(f"Accumulated force on DOF {i}: ({contactforce_x}, {contactforce_y}, {contactforce_z})")

    # 输出总力
    # print('nbDof', sphere_nbDofs)
    # print('force', sphere_forces)
    print('contactforce', contactforce_x, contactforce_y, contactforce_z)
    return contactforce_x, contactforce_y, contactforce_z
def findClosestVerts(verts, pos, num_closest=3):
    # Calculate distances from the position to each vertex
    distances = [(i, (v[0] - pos[0])**2 + (v[1] - pos[1])**2 + (v[2] - pos[2])**2) for i, v in enumerate(verts)]
    
    # Find the `num_closest` vertices with the smallest distances
    closest_indices = [i for i, _ in heapq.nsmallest(num_closest, distances, key=lambda x: x[1])]
    
    # Retrieve the vertices corresponding to the closest indices
    closest_verts = [verts[i] for i in closest_indices]
    
    return closest_verts
mesh=None
def exportMesh(oglModel):
    global mesh
    triangles=oglModel.triangles.value
    positions=oglModel.position.value
    mesh=trimesh.Trimesh(vertices=positions, faces=triangles)
    return mesh,triangles,positions
def spherical_uv_mapping(vertices):
    # Get the x, y, z coordinates
    x = vertices[:, 0]
    y = vertices[:, 1]
    z = vertices[:, 2]

    # Calculate spherical coordinates (r, theta, phi)
    r = np.sqrt(x**2 + y**2 + z**2)
    theta = np.arctan2(y, x)  # Longitude (-π to π)
    phi = np.arccos(z / r)     # Latitude (0 to π)

    # Normalize theta and phi to be in [0, 1] for UV mapping
    u = (theta + np.pi) / (2 * np.pi)  # Map theta from [-π, π] to [0, 1]
    v = phi / np.pi                    # Map phi from [0, π] to [0, 1]

    # Stack u and v coordinates into a UV array
    uv_coords = np.stack((u, v), axis=-1)
    
    return uv_coords
def faceNormal(points):
    p1, p2, p3 = points
    
    # Compute the face normal
    v1 = p2 - p1
    v2 = p3 - p1
    normal = np.cross(v1, v2)
    normal = normal / np.linalg.norm(normal)
    return normal
def planeSign(plane_normal,plane_point,point):
    # Unpack the plane normal vector and point coordinates
    a, b, c = plane_normal
    x0, y0, z0 = plane_point
    x_p, y_p, z_p = point
    
    # Compute the plane equation value for the point
    d = -(a * x0 + b * y0 + c * z0)
    value = a * x_p + b * y_p + c * z_p + d
    return value
def baseNormalVec(node,XYZ=None):
    global mesh
    posOffset=[0.025,0.0,0.0]
    old_y=[0.0,0.0,0.0]
    nodePos=transform_to_global(posOffset,node.getAngles(),node.transformWrapper.getPosition())
    verticesTissue=node.tissue.visual.VisualModel.position.value
    trianglesTissue=node.tissue.visual.VisualModel.triangles.value
    tissueVerts=findClosestVerts(verticesTissue,[nodePos[0],nodePos[1],nodePos[2]])
    
    if mesh.contains([nodePos]):
        node.forceApply*=0.5
        k=node.transformWrapper.getPosition()
        node.transformWrapper.setPosition([k[0]-0.001*old_y[0],k[1]-0.001*old_y[1],k[2]-0.001*old_y[2]])
        return old_y[0],old_y[1],old_y[2]
    normalized_y=faceNormal(tissueVerts)
    if XYZ is None:
        return normalized_y[0],normalized_y[1],normalized_y[2]
    #finde y and z that are orthogonal to x
    x =np.cross(normalized_y, np.array([0.0,0.0,1.0]))
    normalized_x= x / np.sqrt(np.sum(x**2))
    z =np.cross(normalized_x, normalized_y)
    normalized_z= z / np.sqrt(np.sum(z**2))
    l=[normalized_x,normalized_y,normalized_z]
    ret=[0.0,0.0,0.0]
    print(f'Y {normalized_y}')
    print(f'X {normalized_x}')
    print(f'Z {normalized_z}')
    for i in range(len(XYZ)):
        for j in range(len(l[i])):
            ret[j]+=XYZ[i]*l[i][j]
    old_y=normalized_y
    return ret
class TactoController(Sofa.Core.Controller):
    """ This controller monitors new sphere objects.
    Press ctrl and the L key to make spheres falling!
    """
    def addBasics(self,node):
        plugins=['SofaRigid']
        plugins.append('SofaConstraint')
        plugins.append('SofaImplicitOdeSolver')
        node.addObject('EulerImplicitSolver', name="cg_odesolver")
        node.addObject("CGLinearSolver",iterations=20, tolerance=1e-2, threshold=1e-2)
        node.addObject('RequiredPlugin', pluginName=plugins)
    def addVisuals(self,node):
        visual=node.addChild("Visual")
        visual.addObject("OglModel",name="VisualModel",src="@../../TactoMeshLoader")
        visual.addObject('RigidMapping')
    def addCollision(self,node):
        collision = node.addChild('collision')

        collision.addObject('MeshTopology', src="@../../TactoMeshLoader")
        collision.addObject('MechanicalObject')
        #node.addObject('FixedConstraint', name="FixedConstraint", indices="0")
        collision.addObject('TriangleCollisionModel',contactStiffness=1.0)
        #collision.addObject('LineCollisionModel')
        #collision.addObject('PointCollisionModel')
        collision.addObject('RigidMapping')
        return collision
    def onAnimateEndEvent(self, __):
        nr_contacts=self.listener.getNumberOfContacts()
        base_mesh=self.parent.meshLoaderFine.position.value
        
        mesh=exportMesh(self.tissue.visual.VisualModel)
        self.contacts=nr_contacts
        #print(self.rigidobject.velocity.value)
        #print(nr_contacts)
        x,y,z=baseNormalVec(self)
        self.node.CFF.totalForce.value=[x*self.forceApply, y*self.forceApply, z*self.forceApply, 0, 0, 0]
        self.rigidobject.velocity.value=[[0, 0, 0, 0, 0, 0]]
        if nr_contacts==0:
            #print("HOW AM I HERE")
            #self.rigidobject.velocity.value = [0,0,0]
            
            k=self.node.CFF.totalForce.value
            self.forceApply=0.0
            #print(f' Force before: {k}')
            self.rigidobject.velocity.value=[[0, 0, 0, 0, 0, 0]]
            self.node.CFF.totalForce.value=[0, 0, 0, 0, 0, 0]
            #print(f' Force after: {self.node.CFF.totalForce.value}')
        forcesNorm = self.parent.GCS.constraintForces.value
        acc=0.0
        for i in forcesNorm:
            if i>0:
                acc+=i
        nr_contacts/=50
        if nr_contacts>100:
            nr_contacts=100
        self.dataSender.update(self.transformWrapper.getPosition(),self.getAngles(),acc*100,mesh)
    def reset(self):
        self.transformWrapper.setPosition([0.0, 0.13, 0, 0, 0, -0.7071068, 0.7071068])
        self.rigidobject.velocity.value=[[0, 0, 0, 0, 0, 0]]
        self.node.CFF.totalForce.value=[0, 0, 0, 0, 0, 0]
        self.forceApply=0.0
    def __init__(self, name:str,meshfile : str,parent:Sofa.Core.Node,tissue,stiffness=5.0,senderD=None):
        Sofa.Core.Controller.__init__(self)
        self.iteration = 0
        self.parent=parent
        self.dataSender=senderD
        self.stiffness=stiffness
        self.parent.addObject("MeshSTLLoader",name="TactoMeshLoader",triangulate="true",filename=meshfile)
        self.parent.addObject("MeshSTLLoader",name="GelMeshLoader",triangulate="true",filename="mesh/gel.stl")
        self.node=self.parent.addChild(name)
        self.contacts=0
        self.addBasics(self.node)
        self.rigidobject=self.node.addObject("MechanicalObject",template="Rigid3d",name="TactoMechanics",position=[0.0, 0.13, 0, 0, 0, -0.7071068, 0.7071068])
        self.node.addObject("UniformMass",vertexMass=[1., 1., [1., 0., 0., 0., 1., 0., 0., 0., 1.][:]])
        self.addVisuals(self.node)
        self.collision=self.addCollision(self.node)
        tissue.node.getChild("Collision").getObject("CollisionModel")
        self.tissue=tissue
        self.listener = self.node.addObject(
            "ContactListener",
            collisionModel1=tissue.node.getChild("Collision").getObject("CollisionModel").getLinkPath(),
            collisionModel2=self.collision.getObject('TriangleCollisionModel').getLinkPath(),
        )
        self.forceApply=10000.0
        self.key=""
        self.XYZ=[1.0,0.0,0.0]
        self.scaleIncr=0.1
        self.scale=0.01
        self.transformWrapper=RigidDof(self.rigidobject)
        self.dataSender.update(self.transformWrapper.getPosition(),self.getAngles())
        self.node.addObject('UncoupledConstraintCorrection')
        self.node.addObject('ConstantForceField', name="CFF", totalForce=[0.0, 0.0, 0.0, 0, 0, 0, 0])
        self.mode=0
        self.modeSelect=['Translate','Rotate','Scale']
        self.ModeDict = {'Translate' : self.trans,
           'Rotate' : self.rot,
           'Scale' :self.scaleF
        }
        print("To use Controller always use STRG + (key)")
        print("Change Mode with STRG+M available Modes are: Translate, Rotate and Scale")
        print("Scale refers to the size of the operation (Translate,Rotate) executed not the scale of the Sensor")
        print("If in Translate or Rotate Mode use x, y and z to select the direction of the operation")
        print("Use + / - to translate,rotate and change the Scale of the Operation in the respective Mode")
    def radTodeg(self,angle):
         return (angle*180)/math.pi
    def degtoRad(self,angle):
        return angle*math.pi/180
    def trans(self):
        t=self.transformWrapper.getPosition()
        """
        print(f' Position before: {t}')
        if self.key=='+':
            self.transformWrapper.setPosition([t[0]+self.XYZ[0]*self.scale, t[1]+self.XYZ[1]*self.scale, t[2]+self.XYZ[2]*self.scale])
        if self.key=='-':
            x=t[0]-self.XYZ[0]*self.scale
            self.transformWrapper.setPosition([t[0]-self.XYZ[0]*self.scale, t[1]-self.XYZ[1]*self.scale, t[2]-self.XYZ[2]*self.scale])
        t1=self.transformWrapper.getPosition()
    
        print(f' Position after: {t1}')
        """
        if self.contacts==0:
            print(f'Position before: {t}')
            if self.key=='+':
                self.transformWrapper.setPosition([t[0]+self.XYZ[0]*self.scale, t[1]+self.XYZ[1]*self.scale, t[2]+self.XYZ[2]*self.scale])
            if self.key=='-':
                x=t[0]-self.XYZ[0]*self.scale
                self.transformWrapper.setPosition([t[0]-self.XYZ[0]*self.scale, t[1]-self.XYZ[1]*self.scale, t[2]-self.XYZ[2]*self.scale])
            t1=self.transformWrapper.getPosition()
            print(f'Position after: {t1}')
        else:
            k=self.node.CFF.totalForce.value
            #x,y,z=calcNormalVec(self)
            if self.XYZ[1]==1.0:
                print(self.forceApply)
                if self.key=='+':
                    self.forceApply+=self.scale*100
                if self.key=='-':
                    self.forceApply-=self.scale*100
            else:
                x,y,z=baseNormalVec(self,self.XYZ)
                if self.key=='+':
                    self.node.CFF.totalForce.value=[x*self.scale*10000,y*self.scale*10000,z*self.scale*10000,0,0,0]
                if self.key=='-':
                    self.node.CFF.totalForce.value=[-x*self.scale*10000,-y*self.scale*10000,-z*self.scale*10000,0,0,0]
                """
                if self.key=='+':
                    self.node.CFF.totalForce.value = [k[0]+self.XYZ[0]*self.scale*100,k[1]+self.XYZ[1]*self.scale*100,k[2]+self.XYZ[2]*self.scale*100,k[3],k[4],k[5]]
                if self.key=='-':
                    self.node.CFF.totalForce.value = [k[0]-self.XYZ[0]*self.scale*100,k[1]-self.XYZ[1]*self.scale*100,k[2]-self.XYZ[2]*self.scale*100,k[3],k[4],k[5]]
                """
                print(f'Force after: {self.node.CFF.totalForce.value}')
    def scaleF(self):
        scalebef=self.scale
        print(self.scaleIncr)
        if self.key=='+':
            switch=math.floor(math.log10(self.scale))
            self.scaleIncr=(10**switch)
            self.scale+=self.scaleIncr
            self.scale=round(self.scale,-switch+1)
            #self.scale=round(self.scale,4)
        if self.key=='-':
            switch=math.floor(math.log10(self.scale-(1e-9)))
            self.scaleIncr=(10**switch)
            if self.scale<=0.0001:
                print("ScaleValueToShort")
                return
            self.scale-=self.scaleIncr
            self.scale=round(self.scale,-switch+1)
            #self.scale=round(self.scale,4)
        print(f'Change Scale of Operations (T/R) from {scalebef} to {self.scale} ')
    def getAngles(self):
        eulerAngles= Quat(self.transformWrapper.getOrientation().tolist()).getEulerAngles()
        return [round(self.radTodeg(el),4) for el in eulerAngles]
    def rot(self):
        print(f'Angles before Rotate: {self.getAngles()}')
        #axis=[int(self.XYZ[0]),int(self.XYZ[1]),int(self.XYZ[2])]
        val=100*self.scale
        if val>180.0:
            val=val%180
            val=-180+val
        print(f'Rotate by {val} degree (10*scale)')
        if self.key=='+':
            self.transformWrapper.rotateAround(self.XYZ,self.degtoRad(val))
        if self.key=='-':
            self.transformWrapper.rotateAround(self.XYZ,self.degtoRad(-val))
        print(f'Angles after Rotate: {self.getAngles()}')
        #Todo
        return
        #splib3.numerics.quat.createFromEuler()
    def onKeypressedEvent(self, event):
        # Press L key triggers the creation of new objects in the scene
        keypressed=event['key']
        print(f' Key pressed = {keypressed}')
        if event['key'] == 'M':
            self.mode =(self.mode+1)%3
            modestr=self.modeSelect[self.mode]
            print(f'Change Mode to {modestr}')
        if event['key']=='X' and not self.XYZ==[1.0,0.0,0.0]:
            self.XYZ=[1.0,0.0,0.0]
            print(f'"Mode: {self.modeSelect[self.mode]} in Direction {keypressed}')
        if event['key']=='Y' and not self.XYZ==[0.0,1.0,0.0]:
            self.XYZ=[0.0,1.0,0.0]
            print(f'"Mode: {self.modeSelect[self.mode]} in Direction {keypressed}')
        if event['key']=='Z' and not self.XYZ==[0.0,0.0,1.0]:
            self.XYZ=[0.0,0.0,1.0]
            print(f'"Mode: {self.modeSelect[self.mode]} in Direction {keypressed}')
        if event['key']=='-' or event['key']=='+':
            self.key=event['key'] 
            self.ModeDict[self.modeSelect[self.mode]]()
        self.iteration+=1
        if event['key']=='K':
            self.reset()
        #self.setPosition([0, 1.0, 0, 0, 0, 0, 1])
        if event['key']=='L':
            self.createNewSphere()
        
    def createNewSphere(self):
        root = self.getContext()
        newSphere = root.addChild('FallingSphere-'+str(self.iteration))
        newSphere.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
        newSphere.addObject('CGLinearSolver', threshold='1e-09', tolerance='1e-09', iterations='200')
        MO = newSphere.addObject('MechanicalObject', position=[0, 1.5+0.5*self.iteration, 0, 0, 0, 0, 1], name=f'Particle-{self.iteration}', template='Rigid3d')
        Mass = newSphere.addObject('UniformMass', totalMass=0.001)
        Force = newSphere.addObject('ConstantForceField', name="CFF", totalForce=[0, -1, 0, 0, 0, 0] )
        Sphere = newSphere.addObject('SphereCollisionModel', name="SCM", simulated=1,moving=1,radius=0.02,contactStiffness=10.0 )
        self.iteration = self.iteration+1
        newSphere.init()
        
        self.iteration = self.iteration+1