from meshlib import mrmeshpy
import Sofa

class MyController(Sofa.Core.Controller):
    def __init__(self, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, *kwargs)
                
    def onEvent(self, params):
        print("Un-handled handled event received "+str(params))     

    def onSimulationInitDoneEvent(self, params):
        print("Handled event received: " + str(params))    

def createScene(node):
        node.bbox = [[-1, -1, -1],[1,1,1]]
        node.addObject('DefaultAnimationLoop')
        node.addObject( MyController() )
        return node
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
