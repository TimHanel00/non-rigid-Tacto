import trimesh
import numpy as np

def print_vertices_in_x_range(stl_file, x_min, x_max):
    # 加载 STL 文件
    mesh = trimesh.load_mesh(stl_file)

    # 获取顶点坐标数组
    vertices = mesh.vertices  # 形状为 (N, 3)

    # 找到 x 坐标在指定范围内的顶点索引
    indices_in_range = np.where((vertices[:, 0] >= x_min) & (vertices[:, 0] <= x_max))[0]

    # 打印满足条件的顶点索引
    print(f"X 坐标在 {x_min} 和 {x_max} 之间的顶点数量：{len(indices_in_range)}")
    print(f"顶点索引列表：{indices_in_range.tolist()}")

    # 可选：打印这些顶点的坐标
    for idx in indices_in_range:
        coordinate = vertices[idx]
        print(f"顶点 {idx} 的坐标：{coordinate}")

if __name__ == '__main__':
    stl_file_path = 'mesh/gel.stl'  # 请确保路径正确
    x_min = 0.016
    x_max = 0.017
    print_vertices_in_x_range(stl_file_path, x_min, x_max)
