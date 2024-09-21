from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# 读取 STL 文件
stl_file_path = "mesh/gel.stl"  # 替换为你自己的 .stl 文件路径
your_mesh = mesh.Mesh.from_file(stl_file_path)

# 提取所有顶点坐标
points = your_mesh.vectors.reshape(-1, 3)  # 所有三角形顶点展平为 (N, 3) 的形状
unique_points, indices = np.unique(points, axis=0, return_inverse=True)  # 获取唯一顶点

# 创建一个3D图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 绘制顶点
ax.scatter(unique_points[:, 0], unique_points[:, 1], unique_points[:, 2], c='r', marker='o')

# 在每个顶点标注索引
for i, point in enumerate(unique_points):
    ax.text(point[0], point[1], point[2], f'{i}', fontsize=10, color='blue')

# 设置图形标签
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# 显示图形
plt.show()
