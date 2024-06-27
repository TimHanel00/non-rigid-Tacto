from meshlib import mrmeshpy
import Sofa
import Sofa.Core
import numpy as np


def createScene(root):
    root.gravity = [0, -9.81, 0]

    root.addObject("DefaultAnimationLoop")
    root.addObject("DefaultVisualManagerLoop")
    root.addObject("RequiredPlugin", name="Sofa.Component.Topology.Container.Dynamic")
    root.addObject('RequiredPlugin', name='Sofa.Component.StateContainer')

    container = root.addObject("PointSetTopologyContainer", points=[[0, 0, 0], [1, 0, 0]])
    modifier = root.addObject("PointSetTopologyModifier")
    state = root.addObject("MechanicalObject", template="Vec3d", showObject=True, showObjectScale=10)

    root.addObject(PointController(modifier=modifier, state=state, container=container))


class PointController(Sofa.Core.Controller):
    def __init__(self, modifier, state, container):
        super().__init__()
        self.container = container
        self.modifier = modifier
        self.state = state

    def onKeypressedEvent(self, event):
        if event["key"] == "A":
            print("Add 10 points")
            self.modifier.addPoints(10, True)
            # print("Before setting positions", self.state.position.array())

        elif event["key"] == "D":
            print("Remove point 0")
            self.modifier.removePoints(np.array([0]), True)

        elif event["key"] == "B":
            print(f"{len(self.state.position.array())=}")
            with self.state.position.writeable() as state:
                print(f"{len(state)=}")
                # for i in range(len(state)):
                #     state[i] = np.array([i, 0, 0])

            # print("After setting positions", self.state.position.array())
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