from meshlib import mrmeshpy
import os
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa.Gui
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
def setupEnvironment(root):
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
    root.addObject('NewProximityIntersection', name="Proximity",alarmDistance=0.01,contactDistance=0.0025)
    root.addObject('CollisionResponse', name="CollisionResponse", response="PenalityContactForceField")
    #root.addObject('DiscreteIntersection')
    #root.addObject("RequiredPlugin",pluginName="Sofa.Component.ODESolver.Forward Sofa.Component.LinearSolver.Iterative Sofa.Component.Mass Sofa.Component.MechanicalLoad" 
                   #+" Sofa.Component.IO.Mesh Sofa.Component.SolidMechanics.FEM.Elastic Sofa.GL.Component.Rendering3D")
    root.dt=0.01
    root.gravity=[0.,0.0,0.]