from meshlib import mrmeshpy
import os
from core.sofa.objects.tissue import Tissue
from core.sofa.components.forcefield import Material, ConstitutiveModel
from core.sofa.components.solver import SolverType, TimeIntegrationType
#from core.sofa.components.solver import TimeIntegrationType, ConstraintCorrectionType, SolverType, add_solver
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from stlib3.scene import MainHeader, ContactHeader
from stlib3.solver import DefaultSolver
from stlib3.physics.rigid import Cube, Sphere, Floor
from stlib3.physics.deformable import ElasticMaterialObject
from splib3.numerics import RigidDof
# Choose in your script to activate or not the GUI
USE_GUI = True
import vtk



def main():
    import SofaRuntime
    import Sofa.Gui

    root = Sofa.Core.Node("root")
    createScene(root)
    Sofa.Simulation.init(root)

    if not USE_GUI:
        for iteration in range(10):
            Sofa.Simulation.animate(root, root.dt.value)
    else:
        Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
        Sofa.Gui.GUIManager.createGUI(root, __file__)
        Sofa.Gui.GUIManager.SetDimension(1080, 1080)
        Sofa.Gui.GUIManager.MainLoop(root)
        Sofa.Gui.GUIManager.closeGUI()

vtkMesh=None
material=None
def Floor(parentNode, color=[0.5, 0.5, 0.5, 1.], rotation=[0., 0., 0.], translation=[0., 0., 0.]):
    floor = parentNode.addChild('Floor')
    floor.addObject('MeshOBJLoader', name='loader', filename='mesh/square1.obj', scale=250, rotation=rotation,
                    translation=translation)
    floor.addObject('OglModel', src='@loader', color=color)
    floor.addObject('MeshTopology', src='@loader', name='topo')
    floor.addObject('MechanicalObject')
    floor.addObject('TriangleCollisionModel')
    floor.addObject('LineCollisionModel')
    floor.addObject('PointCollisionModel')
    return floor
def setupEnvironment(root):
    root.addObject('DefaultVisualManagerLoop')
    root.addObject('DefaultAnimationLoop')
    root.addObject("RequiredPlugin", pluginName=[    'Sofa.Component.Collision.Detection.Algorithm',
    'Sofa.Component.Collision.Detection.Intersection',
    'Sofa.Component.Collision.Geometry',
    'Sofa.Component.Collision.Response.Contact',
    'Sofa.Component.Constraint.Projective',
    'Sofa.Component.IO.Mesh',
    'Sofa.Component.LinearSolver.Iterative',
    'Sofa.Component.Mapping.Linear',
    'Sofa.Component.Mass',
    'Sofa.Component.ODESolver.Backward',
    'Sofa.Component.SolidMechanics.FEM.Elastic',
    'Sofa.Component.StateContainer',
    'Sofa.Component.Topology.Container.Dynamic',
    'Sofa.Component.Visual',
    'Sofa.GL.Component.Rendering3D',
    'Sofa.Component.MechanicalLoad',
    'Sofa.Component.ODESolver.Forward'
    ])
    root.addObject('VisualStyle', displayFlags="showCollisionModels showForceFields")
    root.addObject('CollisionPipeline', verbose=0,draw=0)
    root.addObject('BruteForceDetection', name="BruteForceBroadPhase")
    root.addObject('NewProximityIntersection', name="Proximity",alarmDistance=0.2,contactDistance=0.0001)
    root.addObject('CollisionResponse', name="CollisionResponse", response="PenalityContactForceField")
    #root.addObject('DiscreteIntersection')
    #root.addObject("RequiredPlugin",pluginName="Sofa.Component.ODESolver.Forward Sofa.Component.LinearSolver.Iterative Sofa.Component.Mass Sofa.Component.MechanicalLoad" 
                   #+" Sofa.Component.IO.Mesh Sofa.Component.SolidMechanics.FEM.Elastic Sofa.GL.Component.Rendering3D")
    root.dt=0.01
    root.gravity=[0.,0.,0.]
def createScene(root):
    setupEnvironment(root)
    material=Material(
                                young_modulus = 25799.3899911763,
                                poisson_ratio = 0.47273863208820904,
                                constitutive_model = ConstitutiveModel.COROTATED,
                                mass_density = 1.0
                            )
    

    #root.addObject('MeshObjLoader', name="LiverSurface", filename="mesh/liver-smooth.obj")
    
    tissue = root.addObject(Tissue(
                        root,
                        simulation_mesh_filename="mesh/preop_volume.vtk",
                        material= material,
                        node_name='Tissue',
                        #grid_resolution=[8,2,6], # for simulation with hexa
                        solver=SolverType.CG,
                        analysis=TimeIntegrationType.EULER,
                        surface_mesh="mesh/surface_A.stl", # e.g. surface for visualization or collision
                        view=True,
                        collision=True,
                        )
                    )
    print(type(tissue))
    print(type(root))
    root.addObject(TactoController(name = "Tacto",meshfile="mesh/digit.STL",parent=root))

    return root


class TactoController(Sofa.Core.Controller):
    """ This controller monitors new sphere objects.
    Press ctrl and the L key to make spheres falling!
    """
    def addBasics(self,node):
        node.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
        node.addObject("CGLinearSolver", iterations=200, tolerance=1e-9,threshold=1e-9)
        
        
        
    def addVisuals(self,node):
        visual=node.addChild("Visual")
        visual.addObject("OglModel",name="VisualModel",src="@../../TactoMeshLoader")
        visual.addObject('RigidMapping')
    def addCollision(self,node):
        collision = node.addChild('collision')

        collision.addObject('MeshTopology', src="@../../TactoMeshLoader")
        collision.addObject('MechanicalObject')

        collision.addObject('TriangleCollisionModel')
        collision.addObject('LineCollisionModel')
        collision.addObject('PointCollisionModel')
        collision.addObject('RigidMapping')
    def __init__(self, name:str,meshfile : str,parent:Sofa.Core.Node):
        Sofa.Core.Controller.__init__(self)
        self.iteration = 0
        self.parent=parent
        self.parent.addObject("MeshSTLLoader",name="TactoMeshLoader",triangulate="true",filename=meshfile)
        self.node=self.parent.addChild(name)
        
        self.addBasics(self.node)
        self.rigidobject=self.node.addObject("MechanicalObject",template="Rigid3d",name="TactoMechanics",position=[0, 2.0, 0, 0, 0, 0, 1])
        self.node.addObject("UniformMass",totalMass=1)
        self.addVisuals(self.node)
        self.addCollision(self.node)
        self.XYZ='X'
        self.transformWrapper=RigidDof(self.rigidobject)
        self.mode='Translate'
        print("Use STRG+R or STRG+T to select translate or rotate Mode ")
    def setPosition(self, v,index=0, field="position"):
        print(" APDWDPOKAWPDOK")
        p = self.rigidobject.getData(field)
        print("=====")
        print(p.value)
        if(not isinstance(v,list)):
            v = list(v)
        value = [list(float(y) for y in i) for i in p.value]
        v = [float(i) for i in v]
        print("----  "+str(v)+"  ----")
        value[index] = v + value[index][3:]
        print(value)
        self.rigidobject.position = value
        print(self.rigidobject.getData(field).value)
        print("=====")
    def onKeypressedEvent(self, event):
        # Press L key triggers the creation of new objects in the scene
        if event['key'] == 'T' and not self.mode=="Translate":
            self.mode="Translate"
            print(f'{self.mode} has been activated: use STRG+(x|y|z) to select direction and STRG + (+|-) to increase or decrease the specified value')
        if event['key'] == 'R' and not self.mode=="Rotate":
            self.mode="Rotate"
            print(f'{self.mode} has been activated: use STRG+(x|y|z) to select direction and STRG + (+|-) to increase or decrease the specified value')
        printstr=self.mode
        if event['key']=='X' and not self.XYZ=='X':
            self.XYZ='X'
            print(f'"Mode: {printstr} in Direction {self.mode}')
        if event['key']=='Y' and not self.XYZ=='Y':
            self.XYZ='Y'
            print(f'"Mode: {printstr} in Direction {self.mode}')
        if event['key']=='Z' and not self.XYZ=='Z':
            self.XYZ='Z'
            print(f'"Mode: {printstr} in Direction {self.mode}')
        if event['key']=='x' or event['key']=='-':
            self.tactocontrol()
        print("ENTERED")
        #print(self.state.getData("position"))
        t=self.transformWrapper.getPosition()
        self.transformWrapper.setPosition([0, 2.0-self.iteration, 0.])
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
        Mass = newSphere.addObject('UniformMass', totalMass=0.01)
        Force = newSphere.addObject('ConstantForceField', name="CFF", totalForce=[0, -1, 0, 0, 0, 0] )
        Sphere = newSphere.addObject('SphereCollisionModel', name="SCM", simulated=1,moving=1,radius=0.03,contactStiffness=10.0 )
        self.iteration = self.iteration+1
        newSphere.init()
        
        self.iteration = self.iteration+1


# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()
