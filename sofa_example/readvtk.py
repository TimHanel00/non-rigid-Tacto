import vtk

def read_vtk_file(file_path):
    # 读取 VTK 文件
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(file_path)
    reader.Update()

    # 获取点数据
    points = reader.GetOutput().GetPoints()
    num_points = points.GetNumberOfPoints()
    print(f"Number of points: {num_points}")
    for i in range(num_points):
        print(f"Point {i}: {points.GetPoint(i)}")

    # 获取单元数据
    cells = reader.GetOutput().GetCells()
    num_cells = reader.GetOutput().GetNumberOfCells()
    print(f"Number of cells: {num_cells}")
    for i in range(num_cells):
        cell = reader.GetOutput().GetCell(i)
        print(f"Cell {i}: {cell.GetPointIds()}")

# 替换为你的 VTK 文件路径
vtk_filename = "mesh/gel_tetrahedral.vtk"
read_vtk_file(vtk_filename)
