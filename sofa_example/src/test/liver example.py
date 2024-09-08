# Required import for python
import Sofa
import SofaRuntime
import Sofa.Gui
# Choose in your script to activate or not the GUI
USE_GUI = True
def main():


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


def createScene(root):
    root.gravity=[0, -9.81, 0]
    root.dt=0.02

    root.addObject("RequiredPlugin", pluginName=[
    'Sofa.Component.Collision.Detection.Algorithm',
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
    'Sofa.Component.AnimationLoop',
    'Sofa.Component.LinearSolver.Direct',
    'Sofa.Component.Constraint.Lagrangian.Correction',
    'Sofa.Component.MechanicalLoad'

    ])

    root.addObject('VisualStyle', displayFlags="showCollisionModels hideVisualModels showForceFields")
    root.addObject('FreeMotionAnimationLoop')
    root.addObject('GenericConstraintSolver', maxIterations=1000, tolerance=1e-6)

    root.addObject('CollisionPipeline', name="CollisionPipeline")
    root.addObject('BruteForceBroadPhase', name="BroadPhase")
    root.addObject('BVHNarrowPhase', name="NarrowPhase")
    root.addObject('DefaultContactManager', name="CollisionResponse", response="PenaltyContactConstraint")
    root.addObject('MinProximityIntersection', useLineLine=True, usePointPoint=True, alarmDistance=0.3, contactDistance=0.15, useLinePoint=True)

    root.addObject('MeshOBJLoader', name="LiverSurface", filename="mesh/liver-smooth.obj")

    liver = root.addChild('Liver')
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject('SparseLDLSolver', name="linear_solver", template="CompressedRowSparseMatrixMat3x3d")
    liver.addObject('MeshGmshLoader', name="meshLoader", filename="mesh/liver.msh")
    liver.addObject('TetrahedronSetTopologyContainer', name="topo", src="@meshLoader")
    liver.addObject('MechanicalObject', name="dofs", src="@meshLoader")
    liver.addObject('TetrahedronSetGeometryAlgorithms', template="Vec3d", name="GeomAlgo")
    liver.addObject('DiagonalMass', name="Mass", massDensity=1.0)
    liver.addObject('TetrahedralCorotationalFEMForceField', template="Vec3d", name="FEM", method="large", poissonRatio=0.3, youngModulus=2000, computeGlobalMatrix=False)
    liver.addObject('FixedConstraint', name="FixedConstraint", indices="3 39 64")
    liver.addObject('LinearSolverConstraintCorrection')

    LiverSurf = liver.addChild('ExtractSurface')
    LiverSurf.addObject('TriangleSetTopologyContainer', name="Container", position="@../topo.position")
    LiverSurf.addObject('TriangleSetTopologyModifier', name="Modifier")
    LiverSurf.addObject('Tetra2TriangleTopologicalMapping', name="SurfaceExtractMapping", input="@../topo", output="@Container")

    LiverCollision = LiverSurf.addChild('Surf')
    LiverCollision.addObject('TriangleSetTopologyContainer', name="Container", src="@../Container")
    LiverCollision.addObject('MechanicalObject', name="surfaceDOFs")
    LiverCollision.addObject('PointCollisionModel', name="CollisionModel")
    LiverCollision.addObject('IdentityMapping', name="CollisionMapping", input="@../../dofs", output="@surfaceDOFs")

    newSphere = root.addChild('FallingSphere-0')
    newSphere.addObject('EulerImplicitSolver')
    newSphere.addObject('CGLinearSolver', threshold='1e-09', tolerance='1e-09', iterations='200')
    MO = newSphere.addObject('MechanicalObject', showObject=True, position=[-2, 10, 0, 0, 0, 0, 1], name=f'Particle-0', template='Rigid3d')
    Mass = newSphere.addObject('UniformMass', totalMass=1)
    Force = newSphere.addObject('ConstantForceField', name="CFF", totalForce=[0, -1, 0, 0, 0, 0] )
    Sphere = newSphere.addObject('SphereCollisionModel', name="SCM", radius=1.0 )
    newSphere.addObject('UncoupledConstraintCorrection' )

    return root



# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()