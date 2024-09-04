from meshlib import mrmeshpy
import os
import math 
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from splib3.numerics import RigidDof
from splib3.numerics.quat import Quat
import splib3.numerics.quat
import numpy as np
class ForcesController(Sofa.Core.Controller):

    def __init__(self, *args, **kwargs):
        # These are needed (and the normal way to override from a python class)
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.rootNode = kwargs.get("rootNode")

    def onAnimateEndEvent(self, event):
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
        print(forcesNorm)
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
        collision.addObject('PointCollisionModel')
        collision.addObject('RigidMapping')
        return collision
    def onAnimateEndEvent(self, __):
        nr_contacts=self.listener.getNumberOfContacts()
        self.contacts=nr_contacts
        if nr_contacts==0:
            print(nr_contacts)
            
            k=self.node.CFF.totalForce.value
            print(f' Force before: {k}')
            #self.node.CFF.totalForce.value=[0, 0, 0, 0, 0, 0]
            print(f' Force after: {self.node.CFF.totalForce.value}')
        nr_contacts/=50
        if nr_contacts>100:
            nr_contacts=100
        self.dataSender.update(self.transformWrapper.getPosition(),self.getAngles(),nr_contacts)

    def __init__(self, name:str,meshfile : str,parent:Sofa.Core.Node,tissue:Sofa.Core.Node,stiffness=5.0,senderD=None):
        Sofa.Core.Controller.__init__(self)
        self.iteration = 0
        self.parent=parent
        self.dataSender=senderD
        self.stiffness=stiffness
        self.parent.addObject("MeshSTLLoader",name="TactoMeshLoader",triangulate="true",filename=meshfile)
        self.node=self.parent.addChild(name)
        self.contacts=0
        self.addBasics(self.node)
        self.rigidobject=self.node.addObject("MechanicalObject",template="Rigid3d",name="TactoMechanics",position=[0.0, 0.13, 0, 0, 0, -0.7071068, 0.7071068])
        self.node.addObject("UniformMass",vertexMass=[1., 1., [1., 0., 0., 0., 1., 0., 0., 0., 1.][:]])
        self.addVisuals(self.node)
        self.collision=self.addCollision(self.node)
        tissue.getChild("Collision").getObject("CollisionModel")
        self.listener = self.node.addObject(
            "ContactListener",
            collisionModel1=tissue.getChild("Collision").getObject("CollisionModel").getLinkPath(),
            collisionModel2=self.collision.getObject('TriangleCollisionModel').getLinkPath(),
        )
        self.key=""
        self.XYZ=[1.0,0.0,0.0]
        self.scaleIncr=0.1
        self.scale=0.01
        self.transformWrapper=RigidDof(self.rigidobject)
        self.dataSender.update(self.transformWrapper.getPosition(),self.getAngles())
        self.node.addObject('UncoupledConstraintCorrection')
        self.node.addObject('ConstantForceField', name="CFF", totalForce=[0.0, -200.0, 0.0, 0, 0, 0, 0])
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
        self.node.CFF.totalForce.value=[0, 0, 0, 0, 0, 0]
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
            self.node.CFF.totalForce.value=[0, 0, 0, 0, 0, 0]
            print(f' Position before: {t}')
            if self.key=='+':
                self.transformWrapper.setPosition([t[0]+self.XYZ[0]*self.scale, t[1]+self.XYZ[1]*self.scale, t[2]+self.XYZ[2]*self.scale])
            if self.key=='-':
                x=t[0]-self.XYZ[0]*self.scale
                self.transformWrapper.setPosition([t[0]-self.XYZ[0]*self.scale, t[1]-self.XYZ[1]*self.scale, t[2]-self.XYZ[2]*self.scale])
            t1=self.transformWrapper.getPosition()
        
            print(f' Position after: {t1}')
        else:
            k=self.node.CFF.totalForce.value
            print(f' Force before: {k}')
            if self.key=='+':
                self.node.CFF.totalForce.value = [k[0]+self.XYZ[0]*self.scale*100,k[1]+self.XYZ[1]*self.scale*100,k[2]+self.XYZ[2]*self.scale*100,k[3],k[4],k[5]]
            if self.key=='-':
                self.node.CFF.totalForce.value = [k[0]-self.XYZ[0]*self.scale*100,k[1]-self.XYZ[1]*self.scale*100,k[2]-self.XYZ[2]*self.scale*100,k[3],k[4],k[5]]
            print(f' Force after: {self.node.CFF.totalForce.value}')
        """
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