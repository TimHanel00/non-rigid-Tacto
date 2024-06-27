from meshlib import mrmeshpy
import Sofa
from Sofa.Core import TaskScheduler
import time

def createScene(root):
    root.dt = 0.01

    root.addObject("RequiredPlugin", pluginName=[
        "MultiThreading",
        "Sofa.Component.Constraint.Projective",
        "Sofa.Component.Engine.Select",
        "Sofa.Component.LinearSolver.Iterative",
        "Sofa.Component.Mass",
        "Sofa.Component.ODESolver.Backward",
        "Sofa.Component.StateContainer",
        "Sofa.Component.Topology.Container.Grid",
        "Sofa.Component.Visual",
        "Sofa.Component.Topology.Container.Dynamic",
    ])
    root.addObject('VisualStyle', displayFlags="showForceFields")
    root.addObject('DefaultAnimationLoop')
    root.addObject('EulerImplicitSolver', rayleighStiffness=0.1, rayleighMass=0.1)
    root.addObject('CGLinearSolver', iterations=25, tolerance=1.0e-9, threshold=1.0e-9)
    root.addObject('MechanicalObject', template="Vec3")
    root.addObject('UniformMass', vertexMass=1)
    root.addObject('RegularGridTopology', nx=8, ny=8, nz=40, xmin=-1.5, xmax=1.5, ymin=-1.5, ymax=1.5, zmin=0, zmax=19)
    root.addObject('BoxROI', box=[-1.5, -1.5, 0, 1.5, 1.5, 0.0001], name="box")
    root.addObject('FixedConstraint', indices="@box.indices")
    root.addObject('ParallelHexahedronFEMForceField', youngModulus=400000, poissonRatio=0.4, method="large", updateStiffnessMatrix=False)


# When not using runSofa, this main function will be called python
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
