import Sofa
import SofaRuntime
import Sofa.Simulation
import Sofa.Gui

# 加载所需的插件
SofaRuntime.importPlugin("Sofa.Component.Constraint.Projective")
SofaRuntime.importPlugin("Sofa.Component.LinearSolver.Iterative")
SofaRuntime.importPlugin("Sofa.Component.Mass")
SofaRuntime.importPlugin("Sofa.Component.ODESolver.Backward")
SofaRuntime.importPlugin("Sofa.Component.SolidMechanics.FEM.Elastic")
SofaRuntime.importPlugin("Sofa.Component.StateContainer")
SofaRuntime.importPlugin("Sofa.Component.IO.Mesh")
SofaRuntime.importPlugin("Sofa.Component.Visual")
SofaRuntime.importPlugin("Sofa.GL.Component.Rendering3D")
SofaRuntime.importPlugin("Sofa.Component.MechanicalLoad")

# 初始化变量来跟踪是否已初始化 GUI
is_gui_initialized = False

def createScene(root):
    root.dt = 0.02
    root.addObject('VisualStyle', displayFlags="showBehaviorModels showForceFields")
    root.addObject('DefaultAnimationLoop')

    # 加载欧拉隐式求解器和线性求解器
    root.addObject('EulerImplicitSolver', name="cg_odesolver", rayleighStiffness=0.1, rayleighMass=0.1)
    root.addObject('CGLinearSolver', iterations=25, name="linear_solver", tolerance=1e-9, threshold=1e-9)

    # 创建并加载 VTK 网格
    deformable = root.addChild("DeformableObject")
    deformable.addObject('MeshVTKLoader', name="loader", filename="mesh/gel_tet_4.2.vtk")
    deformable.addObject('TetrahedronSetTopologyContainer', src="@loader")
    deformable.addObject('TetrahedronSetGeometryAlgorithms')

    # 创建 MechanicalObject 并添加质量
    deformable.addObject('MechanicalObject', name="dofs", template="Vec3d", position="@loader.position")
    deformable.addObject('UniformMass', totalMass=1.0)

    # 添加形变力场 (增加刚性)
    deformable.addObject('TetrahedronFEMForceField', template='Vec3d', name="FEM", youngModulus=100000, poissonRatio=0.4)

    # 固定特定顶点
    fixed_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 17, 23, 26, 28, 30, 34, 37, 41, 45]
    deformable.addObject('FixedConstraint', indices=fixed_indices)

    # 取消重力场 (移除 ConstantForceField)
    # 添加常量力场，仅作用于索引为 103 的顶点，方向为 x 轴正方向的力 (减小施加的力)
    deformable.addObject('ConstantForceField', indices=[103], force=[0.01, 0, 0])  # 减小力，作用在 x 轴正方向

    # 添加可视化模型 (可选)
    deformable.addObject('OglModel', name="visual", src="@loader")
    deformable.addObject('BarycentricMapping', input="@dofs", output="@visual")


# 创建根节点
root = Sofa.Core.Node("root")

# 创建场景
createScene(root)

# 初始化并运行仿真
Sofa.Simulation.init(root)

# 启动 SOFA GUI 主循环
if not is_gui_initialized:
    Sofa.Gui.GUIManager.Init('MyScene', 'qglviewer')
    Sofa.Gui.GUIManager.createGUI(root, __file__)
    Sofa.Gui.GUIManager.SetDimension(1024, 768)
    is_gui_initialized = True  # 确保只初始化一次

# 运行主循环 (只调用一次)
try:
    Sofa.Gui.GUIManager.MainLoop(root)
except Exception as e:
    print(f"Error during the simulation loop: {e}")

# 关闭 GUI
Sofa.Gui.GUIManager.closeGUI()
