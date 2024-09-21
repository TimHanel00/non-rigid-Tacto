import Sofa
import Sofa.Core
import SofaRuntime
import Sofa.Gui


class GelScene:
    def __init__(self, vtk_file, tacto_mechanics):
        """
        GelScene 管理柔性体的创建和物理场景，并使用 RigidMapping 将其附着到 TactoController 的刚体上。

        :param vtk_file: 柔性体的 VTK 文件路径。
        :param tacto_mechanics: TactoController 的刚体机械对象。
        """
        self.vtk_file = vtk_file
        self.tacto_mechanics = tacto_mechanics

    def create_scene(self, root):
        """
        创建柔性 Gel 的物理和可视化场景，添加到根节点中，并通过 RigidMapping 附着到刚体 TactoController。
        """
        # 加载必要的插件
        root.addObject('RequiredPlugin', name='Sofa.Component.ODESolver.Backward')
        root.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')
        root.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')
        root.addObject('RequiredPlugin', name='Sofa.Component.Mass')
        root.addObject('RequiredPlugin', name='Sofa.Component.MechanicalLoad')

        # 加载 VTK 文件
        root.addObject('MeshVTKLoader', name='gelLoader', filename=self.vtk_file)

        # 创建 Gel 节点
        self.gel_node = root.addChild('Gel')

        # 使用 MeshTopology 来保存拓扑结构
        self.gel_node.addObject('TetrahedronSetTopologyContainer', src='@../gelLoader')
        self.gel_node.addObject('TetrahedronSetTopologyModifier')

        # 添加机械对象用于存储位置信息
        self.gel_mechanical_object = self.gel_node.addObject('MechanicalObject', name='dofs', template='Vec3d',
                                                             position='@../gelLoader.position')

        # 添加质量
        self.gel_node.addObject('UniformMass', totalMass=1.0)

        # 添加力场
        self.gel_node.addObject('TetrahedronFEMForceField', template='Vec3d', youngModulus=500, poissonRatio=0.3)

        # 可视化模型
        visual = self.gel_node.addChild('VisualModel')
        visual.addObject('OglModel', name='visual', src='@../../gelLoader')

        # 使用 RigidMapping 将 Gel 与 TactoController 的刚体绑定
        if self.tacto_mechanics:
            self.gel_node.addObject('RigidMapping', input=self.tacto_mechanics.getLinkPath(), output='@dofs')
            visual.addObject('RigidMapping', input=self.tacto_mechanics.getLinkPath(), output='@visual')
        else:
            print("[ERROR] TactoMechanics not found or not initialized.")


class TactoController(Sofa.Core.Controller):
    def __init__(self, parent_node, vtk_file):
        """
        TactoController 创建一个刚体，并将 GelScene 附加到刚体上。

        :param parent_node: 父节点。
        :param vtk_file: GelScene 使用的柔性体 VTK 文件路径。
        """
        super().__init__()
        self.node = parent_node.addChild("TactoControllerNode")

        # 创建 TactoController 刚体
        self.rigid_object = self.node.addObject("MechanicalObject", name="TactoMechanics", template="Rigid3d",
                                                position=[[0.0, 0.13, 0, 0, 0, 0, 1]])

        # 创建 GelScene，并将其与 TactoController 的刚体对象绑定
        self.gel_scene = GelScene(vtk_file=vtk_file, tacto_mechanics=self.rigid_object)
        self.gel_scene.create_scene(self.node)


