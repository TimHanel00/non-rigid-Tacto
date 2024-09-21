
#based on https://github.com/sofa-framework/sofa/discussions/3812
from meshlib import mrmeshpy
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
from stlib3.physics.rigid import Floor, Cube
import numpy as np


class drawForces(Sofa.Core.Controller):

    def __init__(self, *args, **kwargs):
        # These are needed (and the normal way to override from a python class)
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.rootNode = kwargs.get("rootNode")

    def onAnimateEndEvent(self, event): # called at each end of animation step
        constraint = self.rootNode.Cube.collision.MechanicalObject.constraint.value
        dt = self.rootNode.dt.value
        constraintMatrixInline = np.fromstring(constraint, sep='  ')

        pointId = []
        constraintDirections = []
        index = 0
        i = 0

        forcesNorm = self.rootNode.GCS.constraintForces.value

        constraintDirections = np.zeros((1,1))

        if len(constraintMatrixInline) > 0:
          constraintDirections = np.zeros((int(len(constraintMatrixInline)/6),3))

        while index < len(constraintMatrixInline):
          nbConstraint   = constraintMatrixInline[index+1]
          pointId = np.append(pointId, constraintMatrixInline[index+2])
          constraintDirections[i][0] = constraintMatrixInline[index+3]
          constraintDirections[i][1] = constraintMatrixInline[index+4]
          constraintDirections[i][2] = constraintMatrixInline[index+5]
          index = index + 6
          i = i + 1
        
        nbDofs = len(self.rootNode.Cube.collision.MechanicalObject.position.value)
        forces = np.zeros((nbDofs,3))

        for i in range(int(len(constraintMatrixInline)/6)):
          indice = int(pointId[i])
          forces[indice][0] = forces[indice][0] + constraintDirections[i][0] * forcesNorm[i] / dt
          forces[indice][1] = forces[indice][1] + constraintDirections[i][1] * forcesNorm[i] / dt
          forces[indice][2] = forces[indice][2] + constraintDirections[i][2] * forcesNorm[i] / dt
        

        if len(constraintMatrixInline) > 0:
          self.rootNode.drawNode.drawForceFF.indices.value = list(range(0,nbDofs,1)) 
          self.rootNode.drawNode.drawForceFF.forces.value = forces
          self.rootNode.drawNode.drawPositions.position.value = self.rootNode.Cube.collision.MechanicalObject.position.value




def createScene(rootNode):
    rootNode.addObject("RequiredPlugin", pluginName=[    'Sofa.Component.Constraint.Lagrangian.Solver','Sofa.Component.AnimationLoop','Sofa.Component.Collision.Detection.Algorithm',
                                                     'Sofa.Component.Collision.Detection.Intersection','Sofa.Component.ODESolver.Backward','Sofa.Component.Mass','Sofa.Component.LinearSolver.Iterative','Sofa.Component.IO.Mesh',
                                                     'Sofa.Component.MechanicalLoad'])
    rootNode.addObject('VisualStyle', displayFlags='showVisual showCollisionModels showWireFrame showInteractionForceFields showForceFields')
    rootNode.addObject('GenericConstraintSolver', name="GCS", maxIt=1000, tolerance=1e-6, computeConstraintForces=True)
    rootNode.addObject('FreeMotionAnimationLoop')
    rootNode.addObject('DefaultPipeline', depth=15, verbose=0, draw=0)
    rootNode.addObject('BruteForceBroadPhase')
    rootNode.addObject('BVHNarrowPhase')
    rootNode.addObject('LocalMinDistance', name='Proximity', alarmDistance=10, contactDistance=5, useLMDFilters=0)
    rootNode.addObject('DefaultContactManager', name='Response', response='FrictionContactConstraint')
    rootNode.addObject('EulerImplicitSolver', name='odesolver', firstOrder=False, rayleighMass=0.1, rayleighStiffness=0.1)
    rootNode.gravity = [0, -981.0, 0]

    cube = Cube(rootNode, 
                  name="Cube",
                  translation=[0.0,0.0,0.0],
                  uniformScale=20.0,
                  totalMass=1.0,
                  volume=1.0)
    cube.addObject('UncoupledConstraintCorrection')

    floor = Floor(rootNode,
                  name="Floor",
                  translation=[0.0, -300.0, 0.0],
                  uniformScale=5.0,
                  isAStaticObject=True)

    rootNode.addObject( drawForces(name="PythonController", rootNode=rootNode) )

    drawNode = rootNode.addChild('drawNode')
    MOdraw = drawNode.addObject('MechanicalObject', name="drawPositions", position="@/rootNode/Cube/collision/MechanicalObject.position", size=8)
    drawNode.addObject('ConstantForceField', name="drawForceFF", force=[0,0,0], showArrowSize=1)


    return rootNode
def main():
    rootNode = Sofa.Core.Node("root")

    # Create the scene
    createScene(rootNode)

    # Run the simulation
    Sofa.Simulation.init(rootNode)
    Sofa.Gui.GUIManager.Init("simple_scene", "qt")
    Sofa.Gui.GUIManager.createGUI(rootNode,__file__)
    Sofa.Gui.GUIManager.MainLoop(rootNode)
    Sofa.Gui.GUIManager.closeGUI()

    #Sofa.Simulation.start(rootNode)

if __name__ == "__main__":
    main()