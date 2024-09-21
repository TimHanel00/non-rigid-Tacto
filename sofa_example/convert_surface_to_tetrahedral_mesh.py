import vtk


def convert_surface_to_tetrahedral_mesh(input_vtk_file, output_vtk_file):
    # 检查输入文件类型
    if input_vtk_file.endswith('.vtk'):
        # 尝试使用 UnstructuredGridReader
        reader = vtk.vtkUnstructuredGridReader()
        reader.SetFileName(input_vtk_file)
        reader.Update()
        input_data = reader.GetOutput()

        # 如果未读取到 UnstructuredGrid，则尝试使用 PolyDataReader
        if input_data.GetNumberOfPoints() == 0:
            print("[INFO] Input is not UnstructuredGrid, trying PolyDataReader...")
            reader = vtk.vtkPolyDataReader()
            reader.SetFileName(input_vtk_file)
            reader.Update()
            input_data = reader.GetOutput()

        # 检查是否读取到有效的输入数据
        if input_data.GetNumberOfPoints() == 0:
            print("[ERROR] Failed to read input VTK file.")
            return
    else:
        print("[ERROR] Unsupported file format.")
        return

    # 使用 Delaunay3D 生成四面体
    delaunay = vtk.vtkDelaunay3D()
    delaunay.SetInputData(input_data)
    delaunay.Update()

    # 获取生成的四面体网格
    tetrahedral_mesh = delaunay.GetOutput()

    # 写入输出文件
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(output_vtk_file)
    writer.SetInputData(tetrahedral_mesh)
    writer.Write()

    print(f"[INFO] Tetrahedral mesh saved to {output_vtk_file}")


# 使用该函数
input_vtk_filename = "mesh/gel.vtk"  # 输入的 VTK 文件路径
output_vtk_filename = "mesh/gel_tetrahedral.vtk"  # 输出的 VTK 文件路径
convert_surface_to_tetrahedral_mesh(input_vtk_filename, output_vtk_filename)
