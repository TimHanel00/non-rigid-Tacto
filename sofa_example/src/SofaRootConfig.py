from meshlib import mrmeshpy
import os
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
def retrieveContacts(event,root):
            if isinstance(event, Sofa.SimulationEvent):
                contacts = root.pipeline.contactInteractions
                for contact in contacts:
                    print("Contact between Mesh1 and Mesh2")
                    print("Contact point:", contact.contactPoints())
                    print("Contact normal:", contact.contactNormals())
                    print("Contact distance:", contact.contactDistances())
class Environment():
     
    def __init__(self,root:Sofa.Core.Node):
        self.root=root
        self.setupEnvironment()
    def setupEnvironment(self):
        #self.root.addObject('DefaultVisualManagerLoop')
        self.root.addObject('DefaultAnimationLoop')
        self.root.addObject("RequiredPlugin", pluginName=[
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
        'Sofa.Component.ODESolver.Forward'
        ])
        self.root.addObject('VisualStyle', displayFlags="showVisual showCollisionModels showForceFields")
        self.root.addObject('CollisionPipeline', verbose=0,draw=0)
        self.root.addObject('BruteForceDetection', name="BruteForceBroadPhase")
        self.root.addObject('NewProximityIntersection', name="Proximity",alarmDistance=0.01,contactDistance=0.001)
        self.root.addObject('CollisionResponse', name="CollisionResponse", response="FrictionContactConstraint")
        self.root.addObject('FreeMotionAnimationLoop')
        self.root.addObject('GenericConstraintSolver', name="GCS", maxIt=20, tolerance=1e-2, computeConstraintForces=True)
        self.root.addObject('DefaultContactManager', name='Response', response='FrictionContactConstraint')
        #self.root.addObject('CollisionResponse', name="CollisionResponse", response="PenalityContactForceField")
        #root.addObject('DiscreteIntersection')
        #root.addObject("RequiredPlugin",pluginName="Sofa.Component.ODESolver.Forward Sofa.Component.LinearSolver.Iterative Sofa.Component.Mass Sofa.Component.MechanicalLoad" 
                    #+" Sofa.Component.IO.Mesh Sofa.Component.SolidMechanics.FEM.Elastic Sofa.GL.Component.Rendering3D")
        self.root.dt=0.01
        self.root.gravity=[0.,0.0,0.]

def Floor(parentNode, color=[0.5, 0.5, 0.5, 1.], rotation=[0., 0., 0.], translation=[0., 0., 0.]):
    floor = parentNode.addChild('Floor')
    floor.addObject('MeshOBJLoader', name='loader', filename='mesh/square1.obj', scale=250, rotation=rotation,
                    translation=translation)
    floor.addObject('OglModel', src='@loader', color=color)
    floor.addObject('MeshTopology', src='@loader', name='topo')
    floor.addObject('MechanicalObject')
    floor.addObject('TriangleCollisionModel')
    floor.addObject('LineCollisionModel')
    floor.addObject('PointCollisionModel')
    return floor