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

# Choose in your script to activate or not the GUI
USE_GUI = True
import vtk

def read_mesh_file(location):
    location=os.path.join(os.getcwd(),location)
    """
    Reads a mesh file and returns a vtkUnstructuredGrid object.
    
    :param location: String representing the file path of the mesh file.
    :return: vtkUnstructuredGrid object containing the mesh data.
    """
    # Create a reader based on the file extension
    if location.endswith('.vtk'):
        reader = vtk.vtkUnstructuredGridReader()
    elif location.endswith('.vtu'):
        reader = vtk.vtkXMLUnstructuredGridReader()
    else:
        raise ValueError(f"Unsupported file format for '{location}'. Only .vtk and .vtu files are supported.")

    # Set the file name
    reader.SetFileName(location)

    # Read the file
    reader.Update()

    # Get the output data object
    output = reader.GetOutput()

    return output


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
def createScene(root):
    root.gravity=[0, -9.81, 0]
    root.dt=0.02
    material=Material(
                                young_modulus = 25799.3899911763,
                                poisson_ratio = 0.47273863208820904,
                                constitutive_model = ConstitutiveModel.COROTATED,
                                mass_density = 1.0
                            )
    root.addObject('DefaultAnimationLoop')

    #root.addObject('VisualStyle', displayFlags="showCollisionModels hideVisualModels showForceFields")
    root.addObject('VisualStyle', displayFlags="showCollisionModels showForceFields")
    #root.addObject('VisualStyle', displayFlags="showForceFields")
    root.addObject('RequiredPlugin',pluginName="Sofa.Component.Constraint.Lagrangian.Correction Sofa.Component.Collision.Detection.Algorithm Sofa.Component.Collision.Detection.Intersection Sofa.Component.Mass Sofa.Component.LinearSolver.Iterative")
    root.addObject('RequiredPlugin', pluginName="SofaImplicitOdeSolver SofaLoader SofaOpenglVisual SofaBoundaryCondition SofaGeneralLoader SofaGeneralSimpleFem") 
    root.addObject('DefaultPipeline', name="CollisionPipeline")
    root.addObject('BruteForceDetection', name="N2")
    root.addObject('CollisionResponse', response='FrictionContactConstraint', responseParams='mu=0.8')
    #root.addObject('DefaultContactManager', name="CollisionResponse", response="PenalityContactForceField")
    root.addObject('DiscreteIntersection')

    root.addObject('MeshObjLoader', name="LiverSurface", filename="mesh/liver-smooth.obj")
    vtkMesh=read_mesh_file("mesh/preop_volume.vtk")
    tissue = root.addObject(Tissue(
                        root,
                        simulation_mesh=vtkMesh,
                        simulation_mesh_filename="mesh/preop_volume.vtk",
                        material= material,
                        node_name='Tissue',
                        #grid_resolution=[8,2,6], # for simulation with hexa
                        solver=SolverType.CG,
                        analysis=TimeIntegrationType.EULER,
                        surface_mesh="mesh/surface_A.stl", # e.g. surface for visualization or collision
                        view=True,
                        collision=False,
                        )
                    )
    #collision=liver.addChild("Collision")
    #collision.addObject("Mesh",src="@../../meshLoaderFine")
    #collision.addObject("MechanicalObject",name="StoringForces",scale=1.0)
    #collision.addObject("TriangleCollisionModel",name="CollisionModel",contactStiffness=1.0)
    #collision.addObject("BarycentricMapping",name="CollisionMapping",input="@../", output="@StoringForces")
    print(type(tissue))
    print(type(root))
    #tissue.node.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    #tissue.node.addObject('CGLinearSolver', name="linear_solver", iterations=25, tolerance=1e-09, threshold=1e-09)
    #tissue.node.addObject('TetrahedronSetGeometryAlgorithms', template="Vec3d", name="GeomAlgo")
    #tissue.node.addObject('DiagonalMass', name="Mass", massDensity=1.0)
    #tissue.node.addObject('FixedConstraint', name="FixedConstraint", indices="3 39 64")
    Floor(root)


    """
    liver = root.addChild('Liver')
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject('CGLinearSolver', name="linear_solver", iterations=25, tolerance=1e-09, threshold=1e-09)
    liver.addObject('MeshGmshLoader', name="meshLoader", filename="mesh/liver.msh")
    liver.addObject('TetrahedronSetTopologyContainer', name="topo", src="@meshLoader")
    liver.addObject('MechanicalObject', name="dofs", src="@meshLoader")
    liver.addObject('TetrahedronSetGeometryAlgorithms', template="Vec3d", name="GeomAlgo")
    liver.addObject('DiagonalMass', name="Mass", massDensity=1.0)
    liver.addObject('TetrahedralCorotationalFEMForceField', template="Vec3d", name="FEM", method="large", poissonRatio=0.3, youngModulus=3000, computeGlobalMatrix=False)
    liver.addObject('FixedConstraint', name="FixedConstraint", indices="3 39 64")

    visu = liver.addChild('Visu')
    visu.addObject('OglModel', name="VisualModel", src="@../../LiverSurface")
    visu.addObject('BarycentricMapping', name="VisualMapping", input="@../dofs", output="@VisualModel")

    #surf = liver.addChild('Surf')
    #surf.addObject('SphereLoader', name="sphereLoader", filename="mesh/liver.msh")
    #surf.addObject('MechanicalObject', name="spheres", position="@sphereLoader.position")
    #surf.addObject('SphereCollisionModel', name="CollisionModel", listRadius="@sphereLoader.listRadius")
    #surf.addObject('BarycentricMapping', name="CollisionMapping", input="@../dofs", output="@spheres")
    """
    #root.addObject(KeyPressedController(name = "SphereCreator"))

    return root


class KeyPressedController(Sofa.Core.Controller):
    """ This controller monitors new sphere objects.
    Press ctrl and the L key to make spheres falling!
    """
    def __init__(self, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.iteration = 0

    def onKeypressedEvent(self, event):
        # Press L key triggers the creation of new objects in the scene
        print("awoidjoaiwjdoiajwodija")
        if event['key']=='L':
            self.createNewSphere()
            
    def createNewSphere(self):
        root = self.getContext()
        newSphere = root.addChild('FallingSphere-'+str(self.iteration))
        newSphere.addObject('EulerImplicitSolver')
        newSphere.addObject('CGLinearSolver', threshold='1e-09', tolerance='1e-09', iterations='200')
        MO = newSphere.addObject('MechanicalObject', showObject=True,showObjectScale=0.1, position=[0, 10+self.iteration, 0, 0, 0, 0, 1], name=f'Particle-{self.iteration}', template='Rigid3d')
        Mass = newSphere.addObject('UniformMass', totalMass=1)
        Force = newSphere.addObject('ConstantForceField', name="CFF", totalForce=[0, -1, 0, 0, 0, 0] )
        Sphere = newSphere.addObject('SphereCollisionModel', name="SCM", radius=1.0 )
        
        newSphere.init()
        self.iteration = self.iteration+1


# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()
