import Sofa.Core
import SofaRuntime, Sofa.Core, Sofa.Gui
from stlib3.physics.rigid import Floor, Cube
import numpy as np
from stlib3.physics.rigid import Sphere # Use the Sphere class from stlib3 to define a sphere

class drawForces(Sofa.Core.Controller):

    def __init__(self, *args, **kwargs):
        # These are needed (and the normal way to override from a python class)
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.rootNode = kwargs.get("rootNode")

    def onAnimateEndEvent(self, event):

        # Process forces on the Sphere
        try:
            sphere_constraint = self.rootNode.Sphere.collision.MechanicalObject.constraint.value
            # print("sphere_constraint", sphere_constraint)
        except AttributeError:
            print("Unable to find attribute: MechanicalObject for Sphere")
            return

        sphere_dt = self.rootNode.dt.value
        sphere_constraintMatrixInline = np.fromstring(sphere_constraint, sep='  ')
        # print("sphere_constraintMatrixInline:", sphere_constraintMatrixInline)

        sphere_pointId = []
        sphere_constraintId = []
        sphere_constraintDirections = []
        sphere_index = 0
        i=0

        # Get the constraint forces
        forcesNorm = self.rootNode.GCS.constraintForces.value

        # Add total force accumulation variable in the existing code in onAnimateEndEvent
        contactforce_x = 0
        contactforce_y = 0
        contactforce_z = 0


        # Parse the constraint matrix
        while sphere_index < len(sphere_constraintMatrixInline):
            currConstraintID=int(sphere_constraintMatrixInline[sphere_index])
            nbConstraint = int(sphere_constraintMatrixInline[sphere_index + 1])
            for pts in range(nbConstraint):
                currIDX=sphere_index+2+pts*4
                sphere_pointId=np.append(sphere_pointId,sphere_constraintMatrixInline[currIDX])
                sphere_constraintId.append(currConstraintID)
                sphere_constraintDirections.append([sphere_constraintMatrixInline[currIDX+1],sphere_constraintMatrixInline[currIDX+2],sphere_constraintMatrixInline[currIDX+3]])
            sphere_index=sphere_index+2+nbConstraint*4

        sphere_nbDofs = len(self.rootNode.Sphere.collision.MechanicalObject.position.value)
        sphere_forces = np.zeros((sphere_nbDofs, 3))

        print(f"Parsed Point IDs: {sphere_pointId}")
        print(f"Parsed Constraint Directions: {sphere_constraintDirections}")
        print(f"forcesNorm: {forcesNorm}")

        # Compute and accumulate forces
        for i in range(len(sphere_pointId)):
            indice = int(sphere_pointId[i])
            print(f"Calculating force for point {indice}")

            sphere_forces[indice][0] += sphere_constraintDirections[i][0] * forcesNorm[sphere_constraintId[i]] / sphere_dt
            sphere_forces[indice][1] += sphere_constraintDirections[i][1] * forcesNorm[sphere_constraintId[i]] / sphere_dt
            sphere_forces[indice][2] += sphere_constraintDirections[i][2] * forcesNorm[sphere_constraintId[i]] / sphere_dt
            print(f"Force on point {indice}: {sphere_forces[indice]}")

            # print('indice',i,indice)
        # Accumulate total force
        for i in range(sphere_nbDofs):
            contactforce_x += sphere_forces[i][0]
            contactforce_y += sphere_forces[i][1]
            contactforce_z += sphere_forces[i][2]
            print(f"Accumulated force on DOF {i}: ({contactforce_x}, {contactforce_y}, {contactforce_z})")

        # Print total force
        # print('nbDof', sphere_nbDofs)
        # print('force', sphere_forces)
        print('contactforce', contactforce_x, contactforce_y, contactforce_z)


        if len(sphere_constraintMatrixInline) > 0:
            self.rootNode.drawNode.drawForceFF.indices.value = list(range(0, sphere_nbDofs, 1))
            print(f"indices length: {len(self.rootNode.drawNode.drawForceFF.indices.value)}")
            print(f"forces length: {len(sphere_forces)}")
            print(f"force array: {sphere_forces}")
            self.rootNode.drawNode.drawForceFF.forces.value = sphere_forces
            self.rootNode.drawNode.drawPositions.position.value = self.rootNode.Sphere.collision.MechanicalObject.position.value


def createCollisionMesh(rootNode):
    rootNode.addObject("MeshGmshLoader", name="meshLoaderCoarse", filename="mesh/liver.msh")
    rootNode.addObject("MeshObjLoader", name="meshLoaderFine", filename="mesh/liver-smooth.obj")

    liver = rootNode.addChild("Liver")
    liver.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    liver.addObject("CGLinearSolver", iterations=200, tolerance=1e-9, threshold=1e-9)
    liver.addObject("TetrahedronSetTopologyContainer", name="topo", src="@../meshLoaderCoarse")
    liver.addObject("TetrahedronSetGeometryAlgorithms", template="Vec3d", name="GeomAlgo")

    liver.addObject("MechanicalObject", template="Vec3d", name="MechanicalModel")
    liver.addObject('TetrahedralCorotationalFEMForceField', name="FEM", method="large", youngModulus=1000, poissonRatio=0.4, computeGlobalMatrix=True)
    liver.addObject("MeshMatrixMass", name="Mass", massDensity=3.0)
    liver.addObject('FixedConstraint', name="FixedConstraint", indices="1 3 50")
    liver.addObject("ConstantForceField", totalForce=[100.0, 0.0, 0.0])

    visual = liver.addChild("Visual")
    visual.addObject("OglModel", name="VisualModel", src="@../../meshLoaderFine")
    visual.addObject("BarycentricMapping", name="VMapping", input="@../MechanicalModel", output="@VisualModel")

    collision = liver.addChild("Collision")
    collision.addObject("Mesh", src="@../../meshLoaderFine")
    collision.addObject("MechanicalObject", name="StoringForces", scale=1.0)
    collision.addObject("TriangleCollisionModel", name="CollisionModel", contactStiffness=3.0)
    collision.addObject("BarycentricMapping", name="CollisionMapping", input="@../", output="@StoringForces")

    # Add ConstraintCorrection to ensure forces are correctly applied
    liver.addObject('UncoupledConstraintCorrection')

def createSphere(rootNode):
    sphere = Sphere(
        node=rootNode,
        name="Sphere",
        translation=[0, 7.0, 0],
        uniformScale=1.0,  # Set uniform scaling of the sphere
        totalMass=1.0,     # Set total mass of the sphere
        color=[1.0, 0.0, 0.0]  # Set color of the sphere, optional
    )
    sphere.addObject('UncoupledConstraintCorrection')
    Force = sphere.addObject('ConstantForceField', name="CFF", totalForce=[0, -1.0, 0, 0, 0, 0, 0])



def createScene(rootNode):

    rootNode.addObject('DefaultAnimationLoop')
    rootNode.addObject("RequiredPlugin", pluginName=[
        'Sofa.Component.Constraint.Lagrangian.Solver',
        'Sofa.Component.Constraint.Projective',
        'Sofa.Component.AnimationLoop',
        'Sofa.Component.Collision.Detection.Algorithm',
        'Sofa.Component.Collision.Detection.Intersection',
        'Sofa.Component.Collision.Geometry',
        'Sofa.Component.Collision.Response.Contact',
        'Sofa.Component.Constraint.Lagrangian.Correction',
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
        'Sofa.Component.ODESolver.Forward',
        'SofaValidation'
    ])
    # root.addObject('VisualStyle', displayFlags='showVisual showCollisionModels showWireframe showInteractionForceFields showForceFields')
    rootNode.addObject('VisualStyle', displayFlags=' showCollisionModels   showForceFields')
    rootNode.addObject('CollisionPipeline', verbose=0, draw=0)
    rootNode.addObject('BruteForceDetection', name="BruteForceBroadPhase")
    rootNode.addObject('NewProximityIntersection', name="Proximity", alarmDistance=0.5, contactDistance=0.001)
    rootNode.addObject('CollisionResponse', name="CollisionResponse", response="PenalityContactForceField")
    rootNode.addObject('FreeMotionAnimationLoop')
    rootNode.addObject('GenericConstraintSolver', name="GCS", maxIt=1000, tolerance=1e-6, computeConstraintForces=True)
    rootNode.addObject('DefaultContactManager', name='Response', response='PenalityContactConstraint')
    rootNode.dt = 0.01
    rootNode.gravity = [0., 0., 0.]
    createCollisionMesh(rootNode)
    createSphere(rootNode)

    rootNode.addObject(drawForces(name="ForceController", rootNode=rootNode))
    drawNode = rootNode.addChild('drawNode')
    MOdraw = drawNode.addObject('MechanicalObject', name="drawPositions", position="@/rootNode/Sphere/collision/MechanicalObject.position", size=8)
    drawNode.addObject('ConstantForceField', name="drawForceFF", force=[0, 0, 0], showArrowSize=1)



def main():
    rootNode = Sofa.Core.Node("root")
    createScene(rootNode)
    Sofa.Simulation.init(rootNode)

    Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
    Sofa.Gui.GUIManager.createGUI(rootNode, __file__)
    Sofa.Gui.GUIManager.SetDimension(1080, 1080)
    Sofa.Gui.GUIManager.MainLoop(rootNode)
    Sofa.Gui.GUIManager.closeGUI()

if __name__ == '__main__':
    main()
