from meshlib import mrmeshpy
import os
import math 
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from splib3.numerics import RigidDof
from splib3.numerics.quat import Quat
import splib3.numerics.quat 
class TactoController(Sofa.Core.Controller):
    """ This controller monitors new sphere objects.
    Press ctrl and the L key to make spheres falling!
    """
    def addBasics(self,node):
        node.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
        node.addObject("CGLinearSolver", iterations=50, tolerance=1e-6,threshold=1e-6)
        
        
        
    def addVisuals(self,node):
        visual=node.addChild("Visual")
        visual.addObject("OglModel",name="VisualModel",src="@../../TactoMeshLoader")
        visual.addObject('RigidMapping')
    def addCollision(self,node):
        collision = node.addChild('collision')

        collision.addObject('MeshTopology', src="@../../TactoMeshLoader")
        collision.addObject('MechanicalObject')
        node.addObject('FixedConstraint', name="FixedConstraint", indices="0")
        collision.addObject('TriangleCollisionModel',contactStiffness=1.0)
        #collision.addObject('LineCollisionModel')
        #collision.addObject('PointCollisionModel')
        collision.addObject('RigidMapping')
        return collision
    def onAnimateEndEvent(self, __):
        self.dataSender.update(self.transformWrapper.getPosition(),self.getAngles())
        if(self.listener.getNumberOfContacts()!=0):
            return
            #print(self.listener.getNumberOfContacts())
            #print(self.listener.getDistances())
            #for key in self.listener.getContactData():

                #print(key)

            
            """
            contacts = self.collision.getObject('TriangleCollisionModel').getLastComputedResults()
            for contact in contacts:
                    print("Contact between Mesh1 and Mesh2")
                    print("Contact point:", contact.point)
                    print("Contact normal:", contact.normal)
                    print("Contact penetration depth:", contact.depth)
            """
    def __init__(self, name:str,meshfile : str,parent:Sofa.Core.Node,tissue:Sofa.Core.Node,stiffness=5.0,senderD=None):
        Sofa.Core.Controller.__init__(self)
        self.iteration = 0
        self.parent=parent
        self.dataSender=senderD
        self.stiffness=stiffness
        self.parent.addObject("MeshSTLLoader",name="TactoMeshLoader",triangulate="true",filename=meshfile)
        self.node=self.parent.addChild(name)
        
        self.addBasics(self.node)
        self.rigidobject=self.node.addObject("MechanicalObject",template="Rigid3d",name="TactoMechanics",position=[0.0, 0.11, 0, 0, 0, 0, 1])
        self.node.addObject("UniformMass",totalMass=1.0)
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
        self.scale=0.1
        self.transformWrapper=RigidDof(self.rigidobject)
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
        print(f' Position before: {t}')
        if self.key=='+':
            self.transformWrapper.setPosition([t[0]+self.XYZ[0]*self.scale, t[1]+self.XYZ[1]*self.scale, t[2]+self.XYZ[2]*self.scale])
        if self.key=='-':
            x=t[0]-self.XYZ[0]*self.scale
            self.transformWrapper.setPosition([t[0]-self.XYZ[0]*self.scale, t[1]-self.XYZ[1]*self.scale, t[2]-self.XYZ[2]*self.scale])
        t1=self.transformWrapper.getPosition()
        print(f' Position after: {t1}')
    def scaleF(self):
        scalebef=self.scale

        if self.key=='+':

            self.scale+=self.scaleIncr
            self.scale=round(self.scale,4)
            if self.scale==2.0:
                self.scaleIncr=1.0
            if self.scale==0.1:
                self.scaleIncr=0.1
            if self.scale==0.01:
                self.scaleIncr=0.01
        if self.key=='-':
            if self.scale<=0.001:
                print("ScaleValueToShort")
                return
            self.scale-=self.scaleIncr
            self.scale=round(self.scale,4)
            if self.scale==2.0:
                self.scaleIncr=0.1
            if self.scale==0.1:
                self.scaleIncr=0.01
            if self.scale==0.01:
                self.scaleIncr=0.001
        
        print(f'Change Scale of Operations (T/R) from {scalebef} to {self.scale} ')
    def getAngles(self):
        eulerAngles= Quat(self.transformWrapper.getOrientation().tolist()).getEulerAngles()
        return [round(self.radTodeg(el),4) for el in eulerAngles]
    def rot(self):
        
        print(f'Angles before Rotate: {self.getAngles()}')
        #axis=[int(self.XYZ[0]),int(self.XYZ[1]),int(self.XYZ[2])]
        
        val=10*self.scale
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