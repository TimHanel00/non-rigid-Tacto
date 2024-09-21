import vtk

def visualize_tetrahedral_mesh(vtk_filename):
    # Read the tetrahedral mesh from a VTK file
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(vtk_filename)
    reader.Update()

    # Mapper for the mesh
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputData(reader.GetOutput())

    # Actor to represent the mesh
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(1.0, 0.8, 0.7)  # Set color (light pink)

    # Create a rendering window, renderer, and interactor
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    # Add the actor to the renderer
    renderer.AddActor(actor)
    renderer.SetBackground(0.1, 0.2, 0.4)  # Set background color (dark blue)

    # Add axes to the renderer
    axes = vtk.vtkAxesActor()
    axes_widget = vtk.vtkOrientationMarkerWidget()
    axes_widget.SetOrientationMarker(axes)
    axes_widget.SetInteractor(render_window_interactor)
    axes_widget.EnabledOn()
    axes_widget.InteractiveOn()

    # Render and start interaction
    render_window.Render()
    render_window_interactor.Start()

# Usage
vtk_filename = "mesh/gel_tetrahedral.vtk"  # Path to your tetrahedral VTK file
visualize_tetrahedral_mesh(vtk_filename)
