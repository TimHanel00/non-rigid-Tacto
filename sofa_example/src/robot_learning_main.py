from meshlib import mrmeshpy
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
import os
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from core.sofa.objects.tissue import Tissue
from core.sofa.components.forcefield import Material, ConstitutiveModel
from core.sofa.components.solver import SolverType, TimeIntegrationType
from TactoController import TactoController
import SofaRootConfig
#from core.sofa.components.solver import TimeIntegrationType, ConstraintCorrectionType, SolverType, add_solver
from SofaRootConfig import Environment
from stlib3.scene import MainHeader, ContactHeader
from stlib3.solver import DefaultSolver
from stlib3.physics.rigid import Cube, Sphere, Floor
from stlib3.physics.deformable import ElasticMaterialObject
from splib3.numerics import RigidDof
# Choose in your script to activate or not the GUI
USE_GUI = True
import vtk

vtkMesh=None
material=None
def createCollisionMesh(root):#Part2
    #root.addObject('VisualStyle', displayFlags="showForceFields")

    root.addObject("MeshGmshLoader",name="meshLoaderCoarse",scale=0.1,filename="mesh/liver.msh")
    root.addObject("MeshObjLoader",name="meshLoaderFine",scale=0.1,filename="mesh/liver-smooth.obj")

    liver=root.addChild("Liver")
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject("CGLinearSolver", iterations=200, tolerance=1e-9,threshold=1e-9)
    liver.addObject("TetrahedronSetTopologyContainer",name="topo",src="@../meshLoaderCoarse")
    liver.addObject("TetrahedronSetGeometryAlgorithms",template="Vec3d",name="GeomAlgo")

    liver.addObject("MechanicalObject",template="Vec3d",name="MechanicalModel")#container for degrees of freedom (position,rotation)
    liver.addObject('TetrahedralCorotationalFEMForceField',name="FEM",method="large",youngModulus=4000,poissonRatio=0.4,computeGlobalMatrix=False)#compute elasticity of the object
    liver.addObject("MeshMatrixMass",name="Mass",massDensity=1.0)
    #liver.addObject("ConstantForceField",totalForce=[1.0,0.,0.])
    #liver.addObject('FixedConstraint', name="FixedConstraint", indices="3 39 64")
    visual=liver.addChild("Visual")
    visual.addObject("OglModel",name="VisualModel",src="@../../meshLoaderFine")
    visual.addObject("BarycentricMapping", name="VMapping", input="@../MechanicalModel", output="@VisualModel")

    collision=liver.addChild("Collision")
    collision.addObject("Mesh",src="@../../meshLoaderFine")
    collision.addObject("MechanicalObject",name="StoringForces",scale=1.0)
    collision.addObject("TriangleCollisionModel",name="CollisionModel",contactStiffness=1.0)
    collision.addObject("BarycentricMapping",name="CollisionMapping",input="@../", output="@StoringForces")


class CollisionResponseHandler(Sofa.Core.Controller):
    def __init__(self):
        super().__init__()
        self.collisions = []

    def onBeginAnimationStep(self, dt):
        self.collisions.clear()

    def onEndAnimationStep(self, dt):
        for coll in self.collisions:
            print(f"Collision detected between {coll['object1']} and {coll['object2']}")
            print(f"Normal force: {coll['normalForce']}")

    def onCollision(self, collision):
        print("awdpokawdpokapowkdpoawkdposkdpokpwok")
        obj1 = collision.getContactElements()[0]
        obj2 = collision.getContactElements()[1]
        normal_force = collision.getNormalForce()
        self.collisions.append({
            'object1': obj1.getName(),
            'object2': obj2.getName(),
            'normalForce': normal_force
        })
def createScene(root):
    env=Environment(root)
    root.addObject(CollisionResponseHandler())
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
                        check_displacement=False,
                        #grid_resolution=[8,2,6], # for simulation with hexa
                        solver=SolverType.CG,
                        analysis=TimeIntegrationType.EULER,
                        surface_mesh="mesh/surface_A.stl", # e.g. surface for visualization or collision
                        view=True,
                        collision=True,
                        stiffness=0.01
                        )
                    )
    #print(type(tissue))
    #createCollisionMesh(root)
    print(type(root))
    root.addObject(TactoController(name = "Tacto",meshfile="mesh/digit_transformed.stl",parent=root,tissue=tissue.node))

    return root


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






# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()
