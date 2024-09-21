# Required import for python
from meshlib import mrmeshpy
import Sofa


# Choose in your script to activate or not the GUI
USE_GUI = True


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
def Floor(parentNode, color=[0.5, 0.5, 0.5, 1.], rotation=[90., 0., 0.], translation=[-10., -2., -5.0]):
    floor = parentNode.addChild('Floor')
    floor.addObject('MeshOBJLoader', name='loader', filename='mesh/square1.obj', scale=10.0, rotation=rotation,
                    translation=translation)
    floor.addObject('OglModel', src='@loader', color=color)
    floor.addObject('MeshTopology', src='@loader', name='topo')
    floor.addObject('MechanicalObject', rotation=[0., 0., 0.])
    floor.addObject('TriangleCollisionModel')
    floor.addObject('LineCollisionModel')
    floor.addObject('PointCollisionModel')
    return floor

def createScene(root):
    root.gravity=[0, -9.81, 0]
    root.dt=0.02

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
    'Sofa.Component.MechanicalLoad'
    ])

    root.addObject('DefaultAnimationLoop')

    #root.addObject('VisualStyle', displayFlags="showCollisionModels hideVisualModels showForceFields")
    root.addObject('VisualStyle', displayFlags="showCollisionModels showForceFields")
    root.addObject('CollisionPipeline', name="CollisionPipeline")
    root.addObject('BruteForceBroadPhase', name="BroadPhase")
    root.addObject('BVHNarrowPhase', name="NarrowPhase")
    root.addObject('DefaultContactManager', name="CollisionResponse", response="PenalityContactForceField")
    root.addObject('DiscreteIntersection')

    root.addObject('MeshOBJLoader', name="LiverSurface", filename="mesh/liver-smooth.obj")

    liver = root.addChild('Liver')
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject('CGLinearSolver', name="linear_solver", iterations=25, tolerance=1e-09, threshold=1e-09)
    liver.addObject('MeshGmshLoader', name="meshLoader", filename="mesh/liver.msh")
    liver.addObject('TetrahedronSetTopologyContainer', name="topo", src="@meshLoader")
    liver.addObject('MechanicalObject', name="dofs", src="@meshLoader")
    liver.addObject('TetrahedronSetGeometryAlgorithms', template="Vec3d", name="GeomAlgo")
    liver.addObject('DiagonalMass', name="Mass", massDensity=1.0)
    liver.addObject('TetrahedralCorotationalFEMForceField', template="Vec3d", name="FEM", method="large", poissonRatio=0.3, youngModulus=3000, computeGlobalMatrix=False)
    #liver.addObject('FixedConstraint', name="FixedConstraint", indices="3 39 64")

    visu = liver.addChild('Visu')
    visu.addObject('OglModel', name="VisualModel", src="@../../LiverSurface")
    visu.addObject('BarycentricMapping', name="VisualMapping", input="@../dofs", output="@VisualModel")
    liver.addObject('TriangleCollisionModel', moving=1, simulated=1, contactStiffness=10, color=[0.56,0.56,0.56,0])
    liver.addObject('LineCollisionModel', moving=1, simulated=1, contactStiffness=10, color=[0.56,0.56,0.56,0])
    liver.addObject('PointCollisionModel', moving=1, simulated=1, contactStiffness=10, color=[0.56,0.56,0.56,0])
    #surf = liver.addChild('Surf')
    #surf.addObject('SphereLoader', name="sphereLoader", filename="mesh/liver.sph")
    #surf.addObject('MechanicalObject', name="spheres", position="@sphereLoader.position")
    #surf.addObject('SphereCollisionModel', name="CollisionModel", listRadius="@sphereLoader.listRadius")
    #surf.addObject('BarycentricMapping', name="CollisionMapping", input="@../dofs", output="@spheres")
    Floor(root)
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
        if event['key']=='L':
            self.createNewSphere()
            
    def createNewSphere(self):
        root = self.getContext()
        liver = root.addChild('Liver2')
        liver.addObject('EulerImplicitSolver', name="cg_odesolver"+str(self.iteration), rayleighStiffness=0.1, rayleighMass=0.1)
        liver.addObject('CGLinearSolver', name="linear_solver"+str(self.iteration), iterations=25, tolerance=1e-09, threshold=1e-09)
        liver.addObject('MeshGmshLoader', name="meshLoader"+str(self.iteration), filename="mesh/liver.msh")
        liver.addObject('TetrahedronSetTopologyContainer', name="topo"+str(self.iteration), src="@meshLoader"+str(self.iteration))
        liver.addObject('MechanicalObject', name="dofs"+str(self.iteration), src="@meshLoader"+str(self.iteration),position=[0, 20+self.iteration, 0, 0, 0, 0, 1])
        liver.addObject('TetrahedronSetGeometryAlgorithms', template="Vec3d", name="GeomAlgo"+str(self.iteration))
        liver.addObject('DiagonalMass', name="Mass"+str(self.iteration), massDensity=1.0)
        liver.addObject('TetrahedralCorotationalFEMForceField', template="Vec3d", name="FEM"+str(self.iteration), method="large", poissonRatio=0.3, youngModulus=3000, computeGlobalMatrix=False)
        #liver.addObject('FixedConstraint', name="FixedConstraint", indices="3 39 64")

        visu = liver.addChild('Visu2')
        visu.addObject('OglModel', name="VisualModel"+str(self.iteration), src="@../../LiverSurface")
        visu.addObject('BarycentricMapping', name="VisualMapping"+str(self.iteration), input="@../dofs"+str(self.iteration), output="@VisualModel"+str(self.iteration))
        visu.addObject('TriangleCollisionModel', moving=1, simulated=1, contactStiffness=10, color=[0.56,0.56,0.56,0])
        visu.addObject('LineCollisionModel', moving=1, simulated=1, contactStiffness=10, color=[0.56,0.56,0.56,0])
        visu.addObject('PointCollisionModel', moving=1, simulated=1, contactStiffness=10, color=[0.56,0.56,0.56,0])
        liver.init()
        self.iteration = self.iteration+1


# Function used only if this script is called from a python environment
if __name__ == '__main__':
    import SofaRuntime
    import Sofa.Gui
    # Make sure to load all SOFA libraries

    #Create the root node
    root = Sofa.Core.Node("root")
    # Call the below 'createScene' function to create the scene graph
    createScene(root)
    Sofa.Simulation.init(root)
    # Find out the supported GUIs
    print ("Supported GUIs are: " + Sofa.Gui.GUIManager.ListSupportedGUI(","))
    # Launch the GUI (qt or qglviewer)
    Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
    Sofa.Gui.GUIManager.createGUI(root, __file__)
    Sofa.Gui.GUIManager.SetDimension(1080, 1080)
    # Initialization of the scene will be done here
    Sofa.Gui.GUIManager.MainLoop(root)
    Sofa.Gui.GUIManager.closeGUI()
    print("GUI was closed")
