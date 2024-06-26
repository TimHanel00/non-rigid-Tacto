from meshlib import mrmeshpy

import Sofa
import SofaRuntime
import Sofa.Gui
def createCollisionMesh(root):#Part2
    #root.addObject('VisualStyle', displayFlags="showForceFields")

    root.addObject("MeshGmshLoader",name="meshLoaderCoarse",filename="mesh/liver.msh")
    root.addObject("MeshObjLoader",name="meshLoaderFine",filename="mesh/liver-smooth.obj")

    liver=root.addChild("Liver")
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject("CGLinearSolver", iterations=200, tolerance=1e-9,threshold=1e-9)
    liver.addObject("TetrahedronSetTopologyContainer",name="topo",src="@../meshLoaderCoarse")
    liver.addObject("TetrahedronSetGeometryAlgorithms",template="Vec3d",name="GeomAlgo")

    liver.addObject("MechanicalObject",template="Vec3d",name="MechanicalModel")#container for degrees of freedom (position,rotation)
    liver.addObject('TetrahedralCorotationalFEMForceField',name="FEM",method="large",youngModulus=4000,poissonRatio=0.4,computeGlobalMatrix=False)#compute elasticity of the object
    liver.addObject("MeshMatrixMass",name="Mass",massDensity=1.0)
    #liver.addObject("ConstantForceField",totalForce=[1.0,0.,0.])

    visual=liver.addChild("Visual")
    visual.addObject("OglModel",name="VisualModel",src="@../../meshLoaderFine")
    visual.addObject("BarycentricMapping", name="VMapping", input="@../MechanicalModel", output="@VisualModel")

    collision=liver.addChild("Collision")
    collision.addObject("Mesh",src="@../../meshLoaderFine")
    collision.addObject("MechanicalObject",name="StoringForces",scale=1.0)
    collision.addObject("TriangleCollisionModel",name="CollisionModel",contactStiffness=1.0)
    collision.addObject("BarycentricMapping",name="CollisionMapping",input="@../", output="@StoringForces")
def createDeformableMesh(root):#Part2
    root.addObject('VisualStyle', displayFlags="showForceFields")
    root.addObject("MeshGmshLoader",name="meshLoaderCoarse",filename="mesh/liver.msh")
    root.addObject("MeshGmshLoader",name="meshLoaderFine",filename="mesh/liver-smooth.obj")
    liver=root.addChild("Liver")
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject("CGLinearSolver", iterations=200, tolerance=1e-9,threshold=1e-9)
    liver.addObject("TetrahedronSetTopologyContainer",name="topo",src="@../meshLoaderCoarse")
    liver.addObject("TetrahedronSetGeometryAlgorithms",template="Vec3d",name="GeomAlgo")

    liver.addObject("MechanicalObject",template="Vec3d",name="MechanicalModel")#container for degrees of freedom (position,rotation)
    liver.addObject('TetrahedralCorotationalFEMForceField',name="FEM",method="large",youngModulus=1000,poissonRatio=0.4,computeGlobalMatrix=False)#compute elasticity of the object
    liver.addObject("MeshMatrixMass",name="Mass",massDensity=1.0)
    liver.addObject("ConstantForceField",totalForce=[1.0,0.,0.])
    visual=liver.addChild("Visual")
    visual.addObject("OglModel",name="VisualModel",src="@../../meshLoaderFine")
    visual.addObject("BarycentricMapping", name="VMapping", input="@../MechanicalModel", output="@VisualModel")
    #particle.addObject("OglModel",name="VisualModel",src="@../meshLoaderCoarse")
def createMesh(root):#Part1.5
    
    root.addObject("MeshGmshLoader",name="meshLoaderCoarse",filename="mesh/liver.msh")
    particle=root.addChild("Particle")
    particle.addObject("EulerExplicitSolver")
    particle.addObject("CGLinearSolver", iterations=200, tolerance=1e9,threshold=1e9)
    particle.addObject("PointSetTopologyContainer",name="topo",src="@../meshLoaderCoarse")
    particle.addObject("MechanicalObject", showObject=True,template="Rigid3d",name="myParticle",position=[0.,0.,0.,0.,0.,0.,1.0])
    particle.addObject("UniformMass",totalMass=1)
    particle.addObject("ConstantForceField",totalForce=[1.0,0.,0.,0.,0.,0.])
def createParticle(root):#Part1
    particle=root.addChild("Particle")
    particle.addObject("EulerExplicitSolver")
    particle.addObject("CGLinearSolver", iterations=200, tolerance=1e9,threshold=1e9)
    particle.addObject("MechanicalObject", showObject=True,template="Rigid3d",name="myParticle",position=[0.,0.,0.,0.,0.,0.,1.0])
    particle.addObject("UniformMass",totalMass=1)
    particle.addObject("ConstantForceField",totalForce=[1.0,0.,0.,0.,0.,0.])
def createSphere(root):
    newSphere = root.addChild('FallingSphere-')
    newSphere.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    newSphere.addObject('CGLinearSolver', threshold='1e-09', tolerance='1e-09', iterations='200')
    MO = newSphere.addObject('MechanicalObject', showObject=True, position=[0, 10, 0, 0, 0, 0, 1], name=f'Particle-', template='Rigid3d')
    Mass = newSphere.addObject('UniformMass', totalMass=1)
    Force = newSphere.addObject('ConstantForceField', name="CFF", totalForce=[0, -1, 0, 0, 0, 0] )
    Sphere = newSphere.addObject('SphereCollisionModel', name="SCM", simulated=1,moving=1,radius=1.0,contactStiffness=50.0 )
def createScene(root):
    createCollisionMesh(root)
    createSphere(root)

def main():


    root = Sofa.Core.Node("root")
    
    root.addObject('DefaultVisualManagerLoop')
    root.addObject('DefaultAnimationLoop')
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
    'Sofa.Component.MechanicalLoad',
    'Sofa.Component.ODESolver.Forward'
    ])
    root.addObject('VisualStyle', displayFlags="showCollisionModels showForceFields")
    root.addObject('CollisionPipeline', verbose=0,draw=0)
    root.addObject('BruteForceDetection', name="BruteForceBroadPhase")
    root.addObject('NewProximityIntersection', name="Proximity",alarmDistance=0.2,contactDistance=0.001)
    root.addObject('CollisionResponse', name="CollisionResponse", response="PenalityContactForceField")
    #root.addObject('DiscreteIntersection')
    #root.addObject("RequiredPlugin",pluginName="Sofa.Component.ODESolver.Forward Sofa.Component.LinearSolver.Iterative Sofa.Component.Mass Sofa.Component.MechanicalLoad" 
                   #+" Sofa.Component.IO.Mesh Sofa.Component.SolidMechanics.FEM.Elastic Sofa.GL.Component.Rendering3D")
    root.dt=0.01
    root.gravity=[0.,0.,0.]
    createScene(root)
    Sofa.Simulation.init(root)

    Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
    Sofa.Gui.GUIManager.createGUI(root, __file__)
    Sofa.Gui.GUIManager.SetDimension(1080, 1080)
    Sofa.Gui.GUIManager.MainLoop(root)
    Sofa.Gui.GUIManager.closeGUI()
if __name__ == '__main__':
    main()
