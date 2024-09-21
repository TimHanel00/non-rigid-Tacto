import vtk

# 读取现有的 VTK 文件
reader = vtk.vtkUnstructuredGridReader()
reader.SetFileName("mesh/gel_tet.vtk")
reader.Update()

# 写入新的 VTK 文件并设置版本为 4.2
writer = vtk.vtkUnstructuredGridWriter()
writer.SetFileName("mesh/gel_tet_4.2.vtk")
writer.SetInputData(reader.GetOutput())
writer.SetFileVersion(42)  # 设置 VTK 版本为 4.2
writer.Write()
