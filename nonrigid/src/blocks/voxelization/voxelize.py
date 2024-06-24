from optparse import Option
from vtk import *
import math
import inspect
import sys
import os

#from utils.generalutils import *
from utils.vtkutils import *
#from utils.pytorchutils import *

def distance_field( 
    mesh: vtkDataSet, 
    grid: vtkStructuredGrid, 
    name: str = "distance_field", 
    signed: bool = False,
) ->None:
    """ 
    Embeds the mesh into a grid volume via its distance field. The provided grid is changed in-place.

    Args:
        mesh: The mesh that has to be encoded into the grid.
        grid: The target grid where the mesh will be encoded.
        name: Name of the array of the grid where the distance field will be saved.
        signed: If True, the signed distance field is computed, instead of regular distance field. This
            means that points inside the mesh will be assigned with negative values, while points outside
            the mesh will be assigned with positive values.
    """

    # Initialize distance field:
    df = vtkFloatArray()
    df.SetNumberOfTuples( grid.GetNumberOfPoints() )
    df.SetName(name)

    # Data structure to quickly find cells:
    cellLocator = vtkCellLocator()
    cellLocator.SetDataSet( mesh )
    cellLocator.BuildLocator()


    for i in range(0, grid.GetNumberOfPoints() ):
        # Take a point from the target...
        testPoint = [0]*3
        grid.GetPoint( i, testPoint )
        # ... find the point in the surface closest to it
        cID, subID, dist2 = mutable(0), mutable(0), mutable(0.0)
        closestPoint = [0]*3
        
        cellLocator.FindClosestPoint( testPoint, closestPoint, cID, subID, dist2 )
        #closestPoint = [0]*3
        #mesh.GetPoint( closestPointID, closestPoint )
        #dist = math.sqrt( vtkMath.Distance2BetweenPoints( testPoint, closestPoint ) )
        dist = math.sqrt(dist2)

        df.SetTuple1( i, dist )

    if signed:
        pts = vtkPolyData()
        pts.SetPoints( grid.GetPoints() )

        enclosedPointSelector = vtkSelectEnclosedPoints()
        e = ErrorObserver()
        enclosedPointSelector.AddObserver("ErrorEvent", e)
        enclosedPointSelector.GetExecutive().AddObserver("ErrorEvent", e)
        enclosedPointSelector.CheckSurfaceOn()
        enclosedPointSelector.SetInputData( pts )
        enclosedPointSelector.SetSurfaceData( mesh )
        enclosedPointSelector.SetTolerance( 1e-9 )
        enclosedPointSelector.Update()

        enclosedPoints = enclosedPointSelector.GetOutput()


        if e.ErrorOccurred():
            raise ArithmeticError( "Could not calculate enclosed points. Maybe mesh is not closed?\nFull error was: " + e.ErrorMessage())

        enclosedPoints = enclosedPointSelector.GetOutput()

        for i in range(0, grid.GetNumberOfPoints() ):
            if enclosedPointSelector.IsInside(i):
                df.SetTuple1( i, -df.GetTuple1(i) )     # invert sign

    grid.GetPointData().AddArray( df )

def distance_field_from_cloud(
    cloud: vtkDataSet, 
    grid: vtkStructuredGrid, 
    name: str = "distance_field", 
) ->None:
    """ 
    Embeds the point cloud into a grid volume via its distance field. The provided grid is changed in-place.

    Args:
        cloud: The point cloud that has to be encoded into the grid.
        grid: The target grid where the mesh will be encoded.
        name: Name of the array of the grid where the distance field will be saved.
    """

    # Initialize distance field:
    df = vtkFloatArray()
    df.SetNumberOfTuples( grid.GetNumberOfPoints() )
    df.SetName(name)

    # Data structure to quickly find cells:
    pointLocator = vtkPointLocator()
    pointLocator.SetDataSet( cloud )
    pointLocator.BuildLocator()

    for i in range(0, grid.GetNumberOfPoints() ):
        # Take a point from the target...
        testPoint = [0]*3
        grid.GetPoint( i, testPoint )
        # ... find the point in the surface closest to it
        cID, subID, dist2 = mutable(0), mutable(0), mutable(0.0)
        closestPoint = [0]*3
        
        closestPointID = pointLocator.FindClosestPoint( testPoint )
        closestPoint = [0]*3
        cloud.GetPoint( closestPointID, closestPoint )
        #closestPoint = [0]*3
        #mesh.GetPoint( closestPointID, closestPoint )
        dist = math.sqrt( vtkMath.Distance2BetweenPoints( testPoint, closestPoint ) )
        #dist = math.sqrt(dist2)
        df.SetTuple1( i, dist )

    grid.GetPointData().AddArray( df )

def distance_field_GPU(
    surface, 
    targetGrid, 
    targetArrayName
):
    device = on_gpu()

    surface_tensor = torch.from_numpy(vtkPointSetToNumpyArray(surface)).float().to(device)
    grid_tensor = torch.from_numpy(vtkPointSetToNumpyArray(targetGrid)).float().to(device)

    batch_size_estimate = estimate_grid_mesh_batch_size(grid_tensor, surface_tensor, device=device)
    df_tensor = Distances.batched_min_cdist(grid_tensor, surface_tensor, batch_size_estimate)

    df = numpyArrayToVTK(df_tensor.cpu())
    df.SetName(targetArrayName)
    targetGrid.GetPointData().AddArray(df)

    return df

def to_SDF(
    surfaceMesh, 
    targetGrid, 
    targetArrayName
):
    # surfaceMesh.GetCell(0).GetPointIds().GetId(0) for corner of first triangle
    pts = vtkPolyData()
    pts.SetPoints(targetGrid.GetPoints())

    enclosedPointSelector = vtkSelectEnclosedPoints()
    e = ErrorObserver()
    enclosedPointSelector.AddObserver("ErrorEvent", e)
    enclosedPointSelector.GetExecutive().AddObserver("ErrorEvent", e)

    enclosedPointSelector.CheckSurfaceOn()
    enclosedPointSelector.SetInputData(pts)
    enclosedPointSelector.SetSurfaceData(surfaceMesh)

    enclosedPointSelector.SetTolerance(1e-9)
    enclosedPointSelector.Update()

    if e.ErrorOccurred():
        raise Exception( "Could not calculate enclosed points. Maybe mesh is not closed?\nFull error was: " + e.ErrorMessage())
    sdf = targetGrid.GetPointData().GetArray(targetArrayName)

    for i in range(0, targetGrid.GetNumberOfPoints()):
        if enclosedPointSelector.IsInside(i):
            sdf.SetTuple1(i, -sdf.GetTuple1(i))  # invert sign

    return sdf

def create_grid(
    size: float = 0.5, 
    num_cells: int = 64,
) ->vtkStructuredGrid:
    """ 
    Creates a vtk grid with side length size meters, and num_cells cells.
    
    Args:
        size: side-length of the generated grid in meters
        num_cells: number of cells per grid side (total number of cells will be num_cells^3)
    
    Returns:
        vtkStructuredGrid
    """
    grid = vtkStructuredGrid()
    grid.SetDimensions((num_cells, num_cells, num_cells))
    points = vtkPoints()
    points.SetNumberOfPoints(num_cells**3)
    pID = 0
    start = -size/2
    d = size/(num_cells-1)
    for i in range(0, num_cells):
        for j in range(0, num_cells):
            for k in range(0, num_cells):
                x = start + d*k
                y = start + d*j
                z = start + d*i
                points.SetPoint(pID, x, y, z)
                pID += 1
    grid.SetPoints(points)
    return grid


def interpolate_arrays_to_grid( 
    mesh: vtkDataSet, 
    grid: vtkStructuredGrid, 
    cell_size: float = 0.005, 
    sharpness: int = 10, 
    radius: Optional[float] = None, 
) ->vtkStructuredGrid:
    """     
    Interpolates all the vtk arrays present in mesh onto the grid using a Gaussian kernel. 
    
    Note: Be careful because all DataArrays belonging to mesh will be interpolated.
    
    Args:
        mesh: The initial mesh with the fields to be interpolated to the grid.
        grid: Grid where the arrays will be interpolated to.
        cell_size: Dimension of an individual grid cell, in meters.
        sharpness: Sharpness of the Gaussian kernel. As the sharpness increases, the effect of distant points decreases.
        radius: Radius of the Gaussian kernel. If not specified, kernel radius is defined as 5*cell_size.
            
    Returns:
        vtkStructuredGrid where the interpolated arrays have been added.
    """
    if radius is None:
        radius = cell_size * 5
    
    # Perform the interpolation
    interpolator = vtkPointInterpolator()
    gaussianKernel = vtkGaussianKernel()
    gaussianKernel.SetRadius(radius)
    gaussianKernel.SetSharpness(sharpness)
    interpolator.SetSourceData(mesh)
    interpolator.SetInputData(grid)
    interpolator.SetKernel(gaussianKernel)
    #interpolator.SetNullPointsStrategy(vtkPointInterpolator.CLOSEST_POINT)
    interpolator.Update()

    #output = interpolator.GetOutput()
    output = vtkStructuredGrid()
    output.DeepCopy(interpolator.GetOutput())
    del interpolator, gaussianKernel
    return output


def spread_values_on_grid(
    mesh: vtkDataSet, 
    grid: vtkStructuredGrid,
    array_name: str,
    radius: Optional[float] = None,
    binary: bool = False, 
) ->vtkStructuredGrid:
    """ 
    Transfers the mesh field (Tuple1) described by array_name to the grid.
    For each mesh point, finds the grid cell it falls into and associates the mesh field value
    to all the grid nodes defining the corresponding cell. As an alternative, If radius is specified, it associates the 
        
    Note: that no interpolation is computed here: values are just transferred to grid as they are.

    Args:
        mesh: The initial mesh with the fields to be interpolated to the grid.
        grid: Grid where the arrays will be interpolated to.
        array_name: Name of the DataArray in mesh that has to be transferred to the grid with this method.
        radius: If specified, the mesh field value will be associated to all the grid nodes whose distance 
            from the corresponding mesh point is lower than that radius.  
        binary: If True, when field is different from 0, sets the grid value to 1.
        
    Returns:
        vtkStructuredGrid where a new DataArray "array_name" has been added.
    """

    # Create array for grid
    grid_array = vtkDoubleArray()
    grid_array.SetNumberOfComponents(1)
    grid_array.SetName(array_name)
    grid_array.SetNumberOfTuples(grid.GetNumberOfPoints())
    grid_array.Fill(0.0)

    if radius:
        locator = vtkPointLocator()
    else:
        locator = vtkCellLocator()
    locator.SetDataSet(grid)
    locator.Update()
    cell_pts_idx = vtkIdList()

    # Get data array in mesh
    mesh_array = mesh.GetPointData().GetArray(array_name)
    
    for i in range(mesh_array.GetNumberOfTuples()):
        field_value = mesh_array.GetTuple1(i)
        if not field_value == 0.0:

            if radius:
                locator.FindPointsWithinRadius( radius, mesh.GetPoint(i), cell_pts_idx)
            else:
                cell = locator.FindCell(mesh.GetPoint(i))
                grid.GetCellPoints(cell,cell_pts_idx)

            if binary:
                field_value = 1.0
            for j in range(cell_pts_idx.GetNumberOfIds()):
                grid_array.SetTuple1(cell_pts_idx.GetId(j), field_value)

    grid.GetPointData().AddArray( grid_array )   
    return grid
