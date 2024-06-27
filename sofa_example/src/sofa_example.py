from meshlib import mrmeshpy
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from stlib3.scene import MainHeader
from stlib3.solver import DefaultSolver
from stlib3.physics.rigid import Cube, Sphere, Floor
from stlib3.physics.deformable import ElasticMaterialObject
SofaRuntime.importPlugin('SofaPython3')
SofaRuntime.importPlugin('Sofa.GL.Component.Rendering3D')
SofaRuntime.importPlugin('Sofa.Component.Mass')
SofaRuntime.importPlugin('Sofa.Component.IO.Mesh')
SofaRuntime.importPlugin('Sofa.Component.LinearSolver.Direct')
SofaRuntime.importPlugin('Sofa.Component.SolidMechanics.FEM.Elastic')
stdPlugins=['SofaPython3']
def createScene(rootNode):
    MainHeader(rootNode,plugins=stdPlugins+['Sofa.GL.Component.Rendering3D','Sofa.Component.Mass','Sofa.Component.IO.Mesh','Sofa.Component.LinearSolver.Direct','Sofa.Component.SolidMechanics.FEM.Elastic'])
    DefaultSolver(rootNode)
    
    Sphere(rootNode, name="sphere", translation=[-5.0, 0.0, 0.0])
    Cube(rootNode, name="cube", translation=[5.0,0.0,0.0])

    ElasticMaterialObject(rootNode, name="dragon",
                          volumeMeshFileName="mesh/liver.msh",
                          surfaceMeshFileName="mesh/dragon.stl",
                          translation=[0.0,0.0,0.0])
    Floor(rootNode, name="plane", translation=[0.0, -1.0, 0.0])
def main():
    rootNode = Sofa.Core.Node("root")

    # Create the scene
    createScene(rootNode)

    # Run the simulation
    Sofa.Simulation.init(rootNode)
    Sofa.Gui.GUIManager.Init("simple_scene", "qt")
    Sofa.Gui.GUIManager.createGUI(rootNode,__file__)
    Sofa.Gui.GUIManager.MainLoop(rootNode)
    Sofa.Gui.GUIManager.closeGUI()

    #Sofa.Simulation.start(rootNode)

if __name__ == "__main__":
    main()
