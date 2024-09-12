from meshlib import mrmeshpy
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
import os
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from core.sofa.objects.tissue import Tissue
from core.sofa.components.forcefield import Material, ConstitutiveModel
from core.sofa.components.solver import SolverType, TimeIntegrationType
from TactoController import TactoController,ControllMode,ForceMode
import SofaRootConfig
from multiprocessing import Process, Pipe
from threading import Thread
#from core.sofa.components.solver import TimeIntegrationType, ConstraintCorrectionType, SolverType, add_solver
from SofaRootConfig import Environment,Solver
from stlib3.scene import MainHeader, ContactHeader
from stlib3.solver import DefaultSolver
from stlib3.physics.rigid import Cube, Sphere, Floor
from stlib3.physics.deformable import ElasticMaterialObject
from splib3.numerics import RigidDof
import tactoEnvironment
import numpy as np
#import tacto  # Import TACTO
import vtk
import hydra
from dataTransport import TransportData, Sender 
# Choose in your script to activate or not the GUI
USE_GUI = True

vtkMesh=None
material=None

solver=Solver(objectName="CGLinearSolver",iterations=30, tolerance=1e-3, threshold=1e-3)







def createCollisionMesh(root):#Part2
    
    #root.addObject('VisualStyle', displayFlags="showForceFields")

    root.addObject("MeshGmshLoader",name="meshLoaderCoarse",scale=0.1,filename="mesh/liver.msh")
    root.addObject("MeshObjLoader",name="meshLoaderFine",scale=0.1,filename="mesh/liver-smooth.obj")

    liver=root.addChild("Liver")
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject("CGLinearSolver", iterations=50, tolerance=1e-9,threshold=1e-9)
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
def createScene(root,dataSend):
    global solver
    env=Environment(root)
    material=Material(
                                young_modulus = 200000.0,
                                poisson_ratio = 0.47273863208820904,
                                constitutive_model = ConstitutiveModel.COROTATED,
                                mass_density = .2
                            )
    

    #root.addObject('MeshObjLoader', name="LiverSurface", filename="mesh/liver-smooth.obj")

    tissue = root.addObject(Tissue(
                        root,
                        simulation_mesh_filename="mesh/preop_volume.vtk",
                        material= material,
                        node_name='Tissue',
                        check_displacement=False,
                        #grid_resolution=[8,2,6], # for simulation with hexa
                        solver=solver,
                        analysis=TimeIntegrationType.EULER,
                        surface_mesh="mesh/surface_A.stl", # e.g. surface for visualization or collision
                        view=True,
                        collision=True,
                        contact_stiffness=1.0,
                        massDensity=10.0,
                        senderD=dataSend
                        )
                    )
    #print(type(tissue))
    #createCollisionMesh(root)
    print(type(root))
    root.addObject(TactoController(name = "Tacto",meshfile="mesh/digit_transformed2.stl",senderD=dataSend,parent=root,solver=solver,stiffness=10.0,forceMode=ForceMode.dof,controllMode=ControllMode.forceField))
    return root
def sofaSimLoop(root,sendConn):
    
    dataSend=Sender(sendConn)
    createScene(root,dataSend)
    dataSend.start()
    Sofa.Simulation.init(root)
    send=Thread()
    
    if not USE_GUI:
        for iteration in range(10):
            Sofa.Simulation.animate(root, root.dt.value)
    else:
        Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
        Sofa.Gui.GUIManager.createGUI(root, __file__)
        Sofa.Gui.GUIManager.SetDimension(1080, 1080)
        Sofa.Gui.GUIManager.MainLoop(root)
        Sofa.Gui.GUIManager.closeGUI()
    dataSend.join()
@hydra.main(config_path="../config", config_name="digit")
def main(cfg):
    import SofaRuntime
    import Sofa.Gui
    root = Sofa.Core.Node("root")
    parent_conn, child_conn = Pipe()

    
    
    sofaProc=Process(target=sofaSimLoop,args=(root,parent_conn,))
    tactoProc=Process(target=tactoEnvironment.tactoLaunch,args=(cfg,child_conn,))
    tactoProc.start()
    sofaProc.start()
    sofaProc.join()
    tactoProc.join()







# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()
