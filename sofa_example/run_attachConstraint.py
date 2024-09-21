import Sofa
import SofaRuntime
import Sofa.Simulation
import Sofa.Gui

# 确保加载插件
SofaRuntime.importPlugin("Sofa.Component.Constraint.Projective")
SofaRuntime.importPlugin("Sofa.Component.Engine.Select")
SofaRuntime.importPlugin("Sofa.Component.LinearSolver.Iterative")
SofaRuntime.importPlugin("Sofa.Component.Mass")
SofaRuntime.importPlugin("Sofa.Component.ODESolver.Backward")
SofaRuntime.importPlugin("Sofa.Component.SolidMechanics.FEM.Elastic")
SofaRuntime.importPlugin("Sofa.Component.StateContainer")
SofaRuntime.importPlugin("Sofa.Component.Topology.Container.Grid")
SofaRuntime.importPlugin("Sofa.Component.Visual")
SofaRuntime.importPlugin("Sofa.GL.Component.Rendering3D")


def createScene(root):
    root.dt = 0.02
    root.addObject('VisualStyle', displayFlags="showBehaviorModels showForceFields")
    root.addObject('DefaultAnimationLoop')

    single = root.addChild('Single')
    single.addObject('EulerImplicitSolver', name="cg_odesolver", printLog=False, rayleighStiffness=0.1,
                     rayleighMass=0.1)
    single.addObject('CGLinearSolver', iterations=25, name="linear solver", tolerance=1.0e-9, threshold=1.0e-9)

    m1 = single.addChild('M1')
    m1.addObject('MechanicalObject', showObject=True)
    m1.addObject('UniformMass', vertexMass=1)
    m1.addObject('RegularGridTopology', nx=4, ny=4, nz=28, xmin=-9, xmax=-6, ymin=0, ymax=3, zmin=0, zmax=27)

    # 使用 BoxROI 和 FixedConstraint 替代 BoxConstraint
    m1.addObject('BoxROI', box=[-9.1, -0.1, -0.1, -5.9, 3.1, 0.1], drawBoxes=True, name="boxROI")
    m1.addObject('FixedConstraint', indices="@boxROI.indices")

    m1.addObject('TetrahedronFEMForceField', name="FEM", youngModulus=4000, poissonRatio=0.3)

    # AttachOneWay 节点
    attach_oneway = root.addChild('AttachOneWay')
    attach_oneway.addObject('EulerImplicitSolver', name="cg_odesolver", printLog=False)
    attach_oneway.addObject('CGLinearSolver', iterations=25, name="linear solver", tolerance=1.0e-9, threshold=1.0e-9)

    m1_attach = attach_oneway.addChild('M1')
    m1_attach.addObject('MechanicalObject')
    m1_attach.addObject('UniformMass', vertexMass=1)
    m1_attach.addObject('RegularGridTopology', nx=4, ny=4, nz=10, xmin=-4, xmax=-1, ymin=0, ymax=3, zmin=0, zmax=9)

    # 替换 BoxConstraint
    m1_attach.addObject('BoxROI', box=[-4.1, -0.1, -0.1, -0.9, 3.1, 0.1], drawBoxes=True, name="boxROI_m1_attach")
    m1_attach.addObject('FixedConstraint', indices="@boxROI_m1_attach.indices")

    m1_attach.addObject('TetrahedronFEMForceField', name="FEM", youngModulus=4000, poissonRatio=0.3)

    m2_attach = attach_oneway.addChild('M2')
    m2_attach.addObject('MechanicalObject')
    m2_attach.addObject('UniformMass', vertexMass=1)
    m2_attach.addObject('RegularGridTopology', nx=4, ny=4, nz=10, xmin=-4, xmax=-1, ymin=0, ymax=3, zmin=9, zmax=18)
    m2_attach.addObject('TetrahedronFEMForceField', name="FEM", youngModulus=4000, poissonRatio=0.3)

    m3_attach = attach_oneway.addChild('M3')
    m3_attach.addObject('MechanicalObject')
    m3_attach.addObject('UniformMass', vertexMass=1)
    m3_attach.addObject('RegularGridTopology', nx=4, ny=4, nz=10, xmin=-4, xmax=-1, ymin=0, ymax=3, zmin=18, zmax=27)
    m3_attach.addObject('TetrahedronFEMForceField', name="FEM", youngModulus=4000, poissonRatio=0.3)

    # AttachConstraint 单向连接
    attach_oneway.addObject('AttachConstraint', object1="@M1", object2="@M2", indices1=list(range(144, 160)),
                            indices2=list(range(16)), constraintFactor=[1] * 16)
    attach_oneway.addObject('AttachConstraint', object1="@M2", object2="@M3", indices1=list(range(144, 160)),
                            indices2=list(range(16)), constraintFactor=[1] * 16)

    # AttachTwoWay 节点
    attach_twoway = root.addChild('AttachTwoWay')
    attach_twoway.addObject('EulerImplicitSolver', name="cg_odesolver", printLog=False)
    attach_twoway.addObject('CGLinearSolver', iterations=25, name="linear solver", tolerance=1.0e-9, threshold=1.0e-9)

    m1_twoway = attach_twoway.addChild('M1')
    m1_twoway.addObject('MechanicalObject')
    m1_twoway.addObject('UniformMass', vertexMass=1)
    m1_twoway.addObject('RegularGridTopology', nx=4, ny=4, nz=10, xmin=1, xmax=4, ymin=0, ymax=3, zmin=0, zmax=9)

    # 替换 BoxConstraint
    m1_twoway.addObject('BoxROI', box=[0.9, -0.1, -0.1, 4.1, 3.1, 0.1], drawBoxes=True, name="boxROI_m1_twoway")
    m1_twoway.addObject('FixedConstraint', indices="@boxROI_m1_twoway.indices")

    m1_twoway.addObject('TetrahedronFEMForceField', name="FEM", youngModulus=4000, poissonRatio=0.3)

    m2_twoway = attach_twoway.addChild('M2')
    m2_twoway.addObject('MechanicalObject')
    m2_twoway.addObject('UniformMass', vertexMass=1)
    m2_twoway.addObject('RegularGridTopology', nx=4, ny=4, nz=10, xmin=1, xmax=4, ymin=0, ymax=3, zmin=9, zmax=18)
    m2_twoway.addObject('TetrahedronFEMForceField', name="FEM", youngModulus=4000, poissonRatio=0.3)

    m3_twoway = attach_twoway.addChild('M3')
    m3_twoway.addObject('MechanicalObject')
    m3_twoway.addObject('UniformMass', vertexMass=1)
    m3_twoway.addObject('RegularGridTopology', nx=4, ny=4, nz=10, xmin=1, xmax=4, ymin=0, ymax=3, zmin=18, zmax=27)

    # AttachConstraint 双向连接
    attach_twoway.addObject('AttachConstraint', object1="@M1", object2="@M2", twoWay=True,
                            indices1=list(range(144, 160)), indices2=list(range(16)), constraintFactor=[1] * 16)
    attach_twoway.addObject('AttachConstraint', object1="@M2", object2="@M3", twoWay=True,
                            indices1=list(range(144, 160)), indices2=list(range(16)))


# 创建根节点
root = Sofa.Core.Node("root")

# 创建场景
createScene(root)

# 初始化并运行仿真
Sofa.Simulation.init(root)
Sofa.Simulation.animate(root, 0.1)

# 创建根节点
root = Sofa.Core.Node("root")

# 创建场景
createScene(root)

# 初始化并运行仿真
Sofa.Simulation.init(root)

# 启动 SOFA GUI
Sofa.Gui.GUIManager.Init('MyScene', 'qglviewer')  # 使用 'qglviewer' 渲染器启动 GUI
Sofa.Gui.GUIManager.createGUI(root, __file__)  # 创建 GUI 窗口
Sofa.Gui.GUIManager.SetDimension(1024, 768)  # 设置窗口大小
Sofa.Gui.GUIManager.MainLoop(root)  # 启动主循环
Sofa.Gui.GUIManager.closeGUI()  # 关闭 GUI 界面