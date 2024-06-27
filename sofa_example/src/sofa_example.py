from meshlib import mrmeshpy
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from stlib3.scene import MainHeader, ContactHeader
from stlib3.solver import DefaultSolver
from stlib3.physics.rigid import Cube, Sphere, Floor
from stlib3.physics.deformable import ElasticMaterialObject
def plugins():
    sofaPlugins=['SofaPython3']
    rendering=['Sofa.GL.Component.Rendering3D']
    collision=[]
    #collision=['Sofa.Component.AnimationLoop','Sofa.Component.Collision.Detection.Algorithm']
    timeIntegration=['Sofa.Component.Constraint.Lagrangian.Correction']
    #defaultSolve=['Sofa.Component.LinearSolver.Direct']
    components=['Sofa.Component.IO.Mesh','Sofa.Component.ODESolver.Backward','Sofa.Component.LinearSolver.Iterative','Sofa.Component.Mass',
                'Sofa.Component.Constraint.Lagrangian.Correction']
    return sofaPlugins+rendering+components

def addPlugins(root):
    for plugin in plugins():
         root.addObject('RequiredPlugin', name=plugin)
    return root

def createScene(rootNode):
    rootNode=addPlugins(rootNode)
    
    #MainHeader(rootNode,plugins=plugins())
    #DefaultSolver(rootNode)

    rootNode.addObject("VisualGrid", nbSubdiv=10, size=1000)
    confignode = rootNode.addChild("Config")
    confignode.addObject('OglSceneFrame', style="Arrows", alignment="TopRight")
    #Sphere(rootNode, name="sphere", translation=[-5.0, 0.0, 0.0])
    sphere = rootNode.addChild("sphere")
    sphere.addObject('MechanicalObject', name="mstate", template="Rigid3", translation2=[0., 0., 0.], rotation2=[0., 0., 0.], showObjectScale=50)

    #### Visualization subnode for the sphere
    sphereVisu = sphere.addChild("VisualModel")
    sphereVisu.loader = sphereVisu.addObject('MeshOBJLoader', name="loader", filename="mesh/ball.obj")
    sphereVisu.addObject('OglModel', name="model", src="@loader", scale3d=[50]*3, color=[0., 1., 0.], updateNormals=False)
    sphereVisu.addObject('RigidMapping')
    rootNode.gravity=[0.0,-9.81,0.0]
    rootNode.dt=0.01

    totalMass = 1.0
    volume = 1.0
    inertiaMatrix=[1., 0., 0., 0., 1., 0., 0., 0., 1.]
    sphere.addObject('EulerImplicitSolver', name='odesolver')
    sphere.addObject('CGLinearSolver', name='Solver', iterations=25, tolerance=1e-05, threshold=1e-05)
    sphere.addObject('MechanicalObject', name="mstate", template="Rigid3", translation2=[0., 0., 0.], rotation2=[0., 0., 0.], showObjectScale=50)
    sphere.addObject('UniformMass', name="mass", vertexMass=[totalMass, volume, inertiaMatrix[:]])
    sphere.addObject('UncoupledConstraintCorrection')

    """
    ElasticMaterialObject(rootNode, name="dragon",
                          volumeMeshFileName="mesh/liver.msh",
                          surfaceMeshFileName="mesh/dragon.stl",
                          translation=[0.0,0.0,0.0])
    """
    
    #floor=Floor(rootNode, translation=[0.0, -500.0, 0.0],isAStaticObject=True)
    #ContactHeader(floor, alarmDistance=0.05, contactDistance=0.05)
    #ContactHeader(rootNode, alarmDistance=0.05, contactDistance=0.05)
    return rootNode
def main():
    SofaRuntime.importPlugin("Sofa.Component.StateContainer")
    SofaRuntime.importPlugin("SofaOpenglVisual")
    rootNode = Sofa.Core.Node("root")
    rootNode.addObject('DefaultVisualManagerLoop')
    rootNode.addObject('DefaultAnimationLoop')
    # Create the scene
    rootNode=createScene(rootNode)

    # Run the simulation
    Sofa.Simulation.init(rootNode)
    Sofa.Gui.GUIManager.Init("simple_scene", "qt")
    Sofa.Gui.GUIManager.createGUI(rootNode,__file__)
    Sofa.Gui.GUIManager.SetDimension(1080, 800)
    Sofa.Gui.GUIManager.MainLoop(rootNode)
    Sofa.Gui.GUIManager.closeGUI()

    #Sofa.Simulation.start(rootNode)

if __name__ == "__main__":
    main()
