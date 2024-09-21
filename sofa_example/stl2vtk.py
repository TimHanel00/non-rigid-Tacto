import vtk


def convert_stl_to_vtk(stl_file, vtk_file):
    # 读取 STL 文件
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_file)
    reader.Update()

    # 将 vtkPolyData 转换为 vtkUnstructuredGrid
    poly_data = reader.GetOutput()

    # 创建一个 vtkPoints 对象来存储点
    points = vtk.vtkPoints()
    points.DeepCopy(poly_data.GetPoints())

    # 创建一个 vtkUnstructuredGrid 对象
    unstructured_grid = vtk.vtkUnstructuredGrid()
    unstructured_grid.SetPoints(points)

    # 添加三角形单元
    num_cells = poly_data.GetNumberOfCells()
    for i in range(num_cells):
        triangle = poly_data.GetCell(i)
        unstructured_grid.InsertNextCell(triangle.GetCellType(), triangle.GetPointIds())

    # 写入 VTK 文件
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(vtk_file)
    writer.SetInputData(unstructured_grid)
    writer.Write()

    print(f"Successfully converted {stl_file} to {vtk_file}")

# 示例用法
stl_filename = "mesh/gel.stl"  # 替换为你的 STL 文件路径
vtk_filename = "mesh/gel.vtk"  # 转换后的 VTK 文件路径
convert_stl_to_vtk(stl_filename, vtk_filename)
