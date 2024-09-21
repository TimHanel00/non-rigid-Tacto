import sys
import Sofa
import Sofa.Gui
import SofaRuntime


class MoveControlPoint(Sofa.Core.Controller):

    def __init__(self, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.MO = kwargs.get("MO_control")

    def onAnimateBeginEvent(self, event):
        with self.MO.position.writeableArray() as writeablePosition:
            for i in range(len(writeablePosition)):
                writeablePosition[i][0] += 0.0001  # 控制点沿 +z 方向移动


def createScene(rootNode):
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
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.AnimationLoop')
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Correction')
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Model')
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Solver')

    rootNode.addObject('VisualStyle', displayFlags='showVisual showBehaviorModels showInteractionForceFields')
    rootNode.addObject('FreeMotionAnimationLoop')
    rootNode.addObject('GenericConstraintSolver', tolerance="0.001", maxIterations="1000")
    rootNode.addObject('CollisionPipeline', verbose='0')
    rootNode.addObject('BruteForceBroadPhase')
    rootNode.addObject('BVHNarrowPhase')
    rootNode.addObject('CollisionResponse', response='PenalityContactForceField')
    rootNode.addObject('MinProximityIntersection', name='Proximity', alarmDistance='0.8', contactDistance='0.5')

    # 使用 mesh/gel.vtk 文件替换之前的网格文件
    GelObject = rootNode.addChild('GelObject')
    GelObject.addObject('EulerImplicitSolver', name='cg_odesolver', printLog='false', rayleighStiffness='0.1',
                        rayleighMass='0.1')
    GelObject.addObject('CGLinearSolver', iterations='200', name='linear solver', tolerance='1.0e-9',
                        threshold='1.0e-12')
    GelObject.addObject('MeshVTKLoader', name='meshLoader', filename='mesh/gel_tet_4.2.vtk')
    GelObject.addObject('TetrahedronSetTopologyContainer', name='Container', src='@meshLoader')
    GelObject.addObject('TetrahedronSetTopologyModifier', name='Modifier')
    GelObject.addObject('TetrahedronSetGeometryAlgorithms', name='GeomAlgo', template='Vec3')
    GelObject.addObject('MechanicalObject', name='MO')
    GelObject.addObject('DiagonalMass', massDensity='0.08')
    GelObject.addObject('TetrahedronFEMForceField', name='FEM', youngModulus='1e30', poissonRatio='0.3', method='large')
    GelObject.addObject('UncoupledConstraintCorrection', defaultCompliance="0.001")

    # GelObject 可视化
    VisualNode = GelObject.addChild('Visual')

    # 确保 MechanicalObject 在 OglModel 之前定义和初始化
    VisualNode.addObject('OglModel', name='Visual', src='@../MO')  # 修改为 @../MO，表示引用同一个节点下的 MechanicalObject
    VisualNode.addObject('IdentityMapping', input='@..', output='@Visual')

    # 创建 ControlPoints 节点并添加控制点
    ControlPoints = rootNode.addChild('ControlPoints')

    # 定义多个控制点
    control_point_positions = [
        [0.01606825, -0.0073004, -0.01040069],
        [0.01606826, 0.00904162, -0.00634731],
        [0.01606825, -0.00914089, -0.00630023],
        [0.01606825, -0.00020875, -0.01380922],
        [0.01606825, 0.00446336, -0.01268844],
        [0.01606825, -0.0038385, -0.01296444],
        [0.01606825, 0.00758922, -0.00972445],
        [0.01606826, -0.00920764, 0.01042104],
        [0.01606826, -0.00845061, 0.01120982],
        [0.01606826, 0.00822222, 0.01122653],
        [0.01606826, 0.0090457, 0.01058317],
        [0.01606826, -0.00595934, -0.01160379],
        [0.0160683, -0.00822657, -0.00879856],
        [0.01606824, 0.0091181, -0.006134],
        [0.01606832, 0.00737474, -0.01022446],
        [0.01606826, -0.00916443, -0.00561236],
        [0.01606833, 0.00435365, -0.01267685],
        [0.01606828, 0.00182797, -0.0135791],
        [0.01606814, -0.00213384, -0.0135948],
        [0.01606826, -0.0091581, 0.010464],
        [0.01606826, -0.0082946, 0.01123847],
        [0.01606827, 0.00840058, 0.01122075],
        [0.01606825, 0.00916695, 0.0103632]
    ]
    MO_control = ControlPoints.addObject('MechanicalObject', name='MO', position=control_point_positions)

    # 使用 BilateralInteractionConstraint 将所有控制点绑定到 gel.vtk 顶点
    rootNode.addObject("BilateralInteractionConstraint", template="Vec3",
                       object1="@ControlPoints/MO",
                       object2="@GelObject/MO",
                       first_point=" ".join(map(str, range(len(control_point_positions)))),
                       second_point=" ".join(map(str, range(len(control_point_positions)))))

    # 控制控制点的运动
    rootNode.addObject(MoveControlPoint(name="DOFController", MO_control=MO_control))

    return


def main():
    rootNode = Sofa.Core.Node("rootNode")
    createScene(rootNode)
    Sofa.Simulation.init(rootNode)

    Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
    Sofa.Gui.GUIManager.createGUI(rootNode, __file__)
    Sofa.Gui.GUIManager.SetDimension(1080, 1080)
    Sofa.Gui.GUIManager.MainLoop(rootNode)
    Sofa.Gui.GUIManager.closeGUI()


if __name__ == '__main__':
    main()
