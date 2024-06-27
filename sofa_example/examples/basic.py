# Required import for python
from meshlib import mrmeshpy
import Sofa
import SofaRuntime


def main():
    # Make sure to load all necessary libraries
    SofaRuntime.importPlugin("Sofa.Component.StateContainer")

    # Call the above function to create the scene graph
    root = Sofa.Core.Node("root")
    createScene(root)

    # Once defined, initialization of the scene graph
    Sofa.Simulation.init(root)

    # Run the simulation for 10 steps
    for iteration in range(10):
        print(f'Iteration #{iteration}')
        Sofa.Simulation.animate(root, root.dt.value)

    print("Simulation made 10 time steps. Done")


# Function called when the scene graph is being created
def createScene(root):

    root.addObject('RequiredPlugin', name='Sofa.Component.StateContainer')

    # Scene must now include a AnimationLoop
    root.addObject('DefaultAnimationLoop')

    # Add new nodes and objects in the scene
    node1 = root.addChild("Node1")
    node2 = root.addChild("Node2")
    
    node1.addObject("MechanicalObject", template="Rigid3d", position="0 0 0   0 0 0 1", showObject="1")

    node2.addObject("MechanicalObject", template="Rigid3d", position="1 1 1   0 0 0 1", showObject="1")
        
    return root


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