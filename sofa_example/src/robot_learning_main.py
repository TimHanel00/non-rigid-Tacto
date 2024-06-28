from meshlib import mrmeshpy
import os
from core.sofa.objects.tissue import Tissue
from core.sofa.components.forcefield import Material, ConstitutiveModel
from core.sofa.components.solver import SolverType, TimeIntegrationType
from TactoController import TactoController
import SofaRootConfig
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

vtkMesh=None
material=None

def createScene(root):
    SofaRootConfig.setupEnvironment(root)
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
                        )
                    )
    print(type(tissue))
    print(type(root))
    root.addObject(TactoController(name = "Tacto",meshfile="mesh/digit.STL",parent=root))

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
