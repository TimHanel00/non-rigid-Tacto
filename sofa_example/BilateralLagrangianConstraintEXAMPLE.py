"""
TriangleSurfaceCuttingPython file is based on the scene:
b'/data/Softwares/sofa/src/master'/examples/Demos/TriangleSurfaceCutting.scn
. It has been converted into a python script compatible with the SofaPython3 plugin.
"""

import sys
import Sofa
import Sofa.Gui

import SofaRuntime

class MoveControlPoint(Sofa.Core.Controller):

    def __init__(self, *args, **kwargs):
        # These are needed (and the normal way to override from a python class)
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.MO = kwargs.get("MO_control")

    def onAnimateBeginEvent(self, event):
        with self.MO.position.writeableArray() as writeablePosition:
                writeablePosition[0][2] += 0.1 # move control point 1 in +z
                writeablePosition[1][2] += 0.1 # move control point 1 in +z


def createScene(rootNode):
        # rootNode
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Detection.Algorithm')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Detection.Intersection')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Geometry')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Response.Contact')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Projective')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.LinearSolver.Iterative')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Mapping.Linear')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Mass')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.ODESolver.Backward')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.FEM.Elastic')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.Spring')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.StateContainer')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Dynamic')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Visual')
        rootNode.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.AnimationLoop') # Needed to use components [FreeMotionAnimationLoop]
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Correction') # Needed to use components [UncoupledConstraintCorrection]
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Model') # Needed to use components [BilateralLagrangianConstraint]
        rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Solver')


        rootNode.addObject('VisualStyle', displayFlags='showVisual showBehaviorModels showInteractionForceFields')
        rootNode.addObject('FreeMotionAnimationLoop')
        rootNode.addObject('GenericConstraintSolver', tolerance="0.001", maxIterations="1000")

        rootNode.addObject('CollisionPipeline', verbose='0')
        rootNode.addObject('BruteForceBroadPhase')
        rootNode.addObject('BVHNarrowPhase')
        rootNode.addObject('CollisionResponse', response='PenalityContactForceField')
        rootNode.addObject('MinProximityIntersection', name='Proximity', alarmDistance='0.8', contactDistance='0.5')

        # rootNode/SquareGravity
        SquareGravity = rootNode.addChild('SquareGravity')
        SquareGravity.addObject('EulerImplicitSolver', name='cg_odesolver', printLog='false', rayleighStiffness='0.1', rayleighMass='0.1')
        SquareGravity.addObject('CGLinearSolver', iterations='200', name='linear solver', tolerance='1.0e-9', threshold='1.0e-9')
        SquareGravity.addObject('MeshOBJLoader', name='meshLoader', filename='mesh/square_2594_triangles.obj', scale='10', createSubelements='true')
        SquareGravity.addObject('TriangleSetTopologyContainer', name='Container', src='@meshLoader')
        SquareGravity.addObject('TriangleSetTopologyModifier', name='Modifier')
        SquareGravity.addObject('TriangleSetGeometryAlgorithms', name='GeomAlgo', template='Vec3')
        SquareGravity.addObject('MechanicalObject', name='MO')
        SquareGravity.addObject('DiagonalMass', massDensity='0.08')
        # SquareGravity.addObject('FixedProjectiveConstraint', indices='617 618 57 1301 1302 49')
        SquareGravity.addObject('TriangularFEMForceField', name='FEM', youngModulus='6e8', poissonRatio='0.3', method='large')
        SquareGravity.addObject('TriangularBendingSprings', name='FEM-Bend', stiffness='300', damping='1.0')
        SquareGravity.addObject('TriangleCollisionModel')
        SquareGravity.addObject('UncoupledConstraintCorrection', defaultCompliance="0.001")

        # rootNode/SquareGravity/unnamedNode_0
        unnamedNode_0 = SquareGravity.addChild('unnamedNode_0')
        unnamedNode_0.addObject('OglModel', name='Visual', texcoords='@../meshLoader.texcoords', texturename='textures/colorMap.png')
        unnamedNode_0.addObject('IdentityMapping', input='@..', output='@Visual')

        # ControlPoints
        ControlPoints = rootNode.addChild('ControlPoints')
        MO_control = ControlPoints.addObject('MechanicalObject', name='MO', position="0 100 0 100 100 0")

        rootNode.addObject("BilateralInteractionConstraint", template="Vec3", object1="@ControlPoints/MO", object2="@SquareGravity/MO", first_point="0 1", second_point="1302 618") #If BilateralLagrangianConstraint does not exist, use the old name: BilateralInteractionConstraint

        rootNode.addObject( MoveControlPoint(name="DOFController", MO_control=MO_control) )

        return
def main():
        rootNode=Sofa.Core.Node("rootNode")
        createScene(rootNode)
        Sofa.Simulation.init(rootNode)

        Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
        Sofa.Gui.GUIManager.createGUI(rootNode, __file__)
        Sofa.Gui.GUIManager.SetDimension(1080, 1080)
        Sofa.Gui.GUIManager.MainLoop(rootNode)
        Sofa.Gui.GUIManager.closeGUI()

if __name__ == '__main__':
        main()


