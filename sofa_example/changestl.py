import bpy
import os

# 文件路径
file_path = os.path.join('mesh', 'gel.stl')

# 删除所有现有对象（可选）
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 导入 STL 文件
bpy.ops.import_mesh.stl(filepath=file_path)

# 获取导入的对象
obj = bpy.context.selected_objects[0]

# 确保对象处于对象模式
bpy.ops.object.mode_set(mode='OBJECT')

# 创建一个新的顶点组
vertex_group = obj.vertex_groups.new(name="Fixed_Vertices")

# 顶点索引列表（这些顶点将保持不变）
fixed_vertex_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 17, 23, 26, 28, 30, 34, 37, 41, 45]

# 将指定的顶点添加到顶点组中
for index in fixed_vertex_indices:
    vertex_group.add([index], 1.0, 'ADD')  # 将这些顶点添加到顶点组

# 切换回对象模式
bpy.ops.object.mode_set(mode='OBJECT')

# 添加软体体模拟
bpy.ops.object.modifier_add(type='SOFT_BODY')
soft_body = obj.modifiers['Softbody']

# 关联软体体模拟的目标属性到顶点组
soft_body.settings.use_goal = True
soft_body.settings.goal_vertex_group = "Fixed_Vertices"  # 使用创建的顶点组

# 设置目标强度（可调节）
soft_body.settings.goal_default = 0.0  # 其他未在顶点组中的部分可形变
soft_body.settings.goal_max = 1.0  # 顶点组中的部分保持刚性

# 设置其他软体体参数（根据需求调整）
soft_body.settings.goal_spring = 0.5  # 弹性系数
soft_body.settings.goal_friction = 5  # 摩擦系数

print(f"已成功导入并设置文件: {file_path}，指定的顶点已固定，其他部分可以形变。")
