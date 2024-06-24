import math
import inspect
import sys
import os
import time

from vtk import *

#from utils.generalutils import *
from utils.vtkutils import *
#from utils.pytorchutils import *
from core.log import Log

def undeform( mesh, scale=1 ):
    
    warpByVector = vtkWarpVector()
    warpByVector.SetScaleFactor(-1*scale)
    warpByVector.SetInputData( mesh )
    #warpByVector.SetInputArrayToProcess(0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_POINTS,"displacement");
    mesh.GetPointData().SetActiveVectors("displacement")
    warpByVector.Update()

    #writer = vtkUnstructuredGridWriter()
    #writer.SetFileName( "unwarped.vtk" )
    #writer.SetInputData( warpByVector.GetOutput() )
    ##writer.SetInputConnection( warpByVector.GetOutputPort() )
    #writer.Update()

    return warpByVector.GetOutput()

def calc_displacement( mesh_initial, mesh_deformed, subset=None, thr=1e-20):
    """ Given an initial and deformed mesh, computes the displacement for each point.
    
    Arguments:
        mesh_initial (vtkDataSet):
            Topology of the starting mesh
        mesh_deformed (vtkDataSet):
            Topology of the deformed mesh
        subset (list of ints):
            If specified, displacement is computed only on nodes with indices specified in subset list.
            Other nodes are associated to zero displacement.
            Default: None
        thr (float):
            Displacement of the subset points whose value is below the threshold is clipped to threshold value.
            Default: 1e-20
    
    Returns:
        vtkDataSet
            Same as mesh_initial where a new DataArray "displacement" has been added
    """
    if not mesh_initial.GetNumberOfPoints() == mesh_deformed.GetNumberOfPoints():
        raise IOError( "mesh_initial and mesh_deformed must have the same number of points!" )

    displacement = vtkFloatArray()
    displacement.SetName( "displacement" )
    displacement.SetNumberOfComponents( 3 )
    displacement.SetNumberOfTuples( mesh_initial.GetNumberOfPoints() )

    for i in range( mesh_initial.GetNumberOfPoints() ):
        # If subset is specified, set displacement of points not belonging to the subset to 0
        if subset and not i in subset:
            displacement.SetTuple3(i, 0.0, 0.0, 0.0)
        else:
            p1 = mesh_initial.GetPoint( i )
            p2 = mesh_deformed.GetPoint( i )
            displ = np.array([p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2]])

            displ[np.abs(displ) < thr] = thr
            displacement.SetTuple3( i, displ[0], displ[1], displ[2] )
        
    mesh_initial.GetPointData().AddArray( displacement )

    return mesh_initial

def interpolate_to_grid( mesh, grid, cellSize, sharpness=10, radius=None ):
    """     
    Interpolates DataArrays present in mesh onto the grid using a Gaussian Kernel. 
    Be careful because all DataArrays belonging to mesh will be interpolated.
    Default kernel radius is defined as 5*cellSize.
    
    Arguments:
        mesh (vtkDataSet):
            Initial mesh with the fields to be interpolated into grid.
        grid (vtkDataSet):
            Grid where the DataArrays will be interpolated to.
        cellSize (list of ints):
            Size of the grid cells.
        sharpness (int):
            Sharpness of the Gaussian kernel. As the sharpness increases, the effect of distant points decreases.
            Default: 10
        radius (float):
            Radius of the Gaussian kernel. If not specified, kernel radius is defined as 5*cellSize.
            Default: None
    
    Returns:
        vtkDataSet
            Same as mesh_initial where a new DataArray "displacement" has been added
    """
    if not radius:
        radius = cellSize * 5
    
    # Perform the interpolation
    interpolator = vtkPointInterpolator()
    gaussianKernel = vtkGaussianKernel()
    gaussianKernel.SetRadius( radius )
    gaussianKernel.SetSharpness(sharpness)
    interpolator.SetSourceData( mesh )
    interpolator.SetInputData( grid )
    interpolator.SetKernel( gaussianKernel )
    #interpolator.SetNullPointsStrategy(vtkPointInterpolator.CLOSEST_POINT)
    interpolator.Update()

    #output = interpolator.GetOutput()
    output = vtkStructuredGrid()
    output.DeepCopy(interpolator.GetOutput())
    del interpolator, gaussianKernel
    return output

def interpolate_to_grid_gpu(mesh, grid, cellSize, sharpness=10, radius=None):
    if not radius:
        radius = cellSize * 5

    device = on_gpu()

    mesh_tensor = torch.from_numpy(vtkPointSetToNumpyArray(mesh)).float().to(device)
    displacement_tensor = torch.from_numpy(vtkDataArrayToNumpyArray(mesh.GetPointData()
                                                                    .GetArray("displacement"))).float().to(device)
    grid_tensor = torch.from_numpy(vtkPointSetToNumpyArray(grid)).float().to(device)
    start = time.time()
    bounding_box_lower = mesh_tensor.min(0, keepdim=True).values - radius
    bounding_box_upper = mesh_tensor.max(0, keepdim=True).values + radius
    bounding_box_mask = torch.logical_and((bounding_box_lower <= grid_tensor).all(1), (grid_tensor <= bounding_box_upper).all(1))
    relevant_grid_points = grid_tensor[bounding_box_mask]

    distances = torch.cdist(relevant_grid_points, mesh_tensor)  # grid_points x mesh_points
    inside_kernel_mask = distances < radius  # bool, grid_points x mesh_points

    gaussian_weights = torch.exp(-1 * torch.pow((sharpness/radius * distances), 2))
    gaussian_weights[~inside_kernel_mask] = 0
    interpolated_vals = torch.mm(gaussian_weights, displacement_tensor)

    interpolated_grid = torch.zeros(grid_tensor.size(0), 3, device=device)

    relevant_grid_points_vals = interpolated_vals / inside_kernel_mask.sum(1).unsqueeze(1)
    relevant_grid_points_vals[torch.isnan(relevant_grid_points_vals)] = 0

    interpolated_grid[bounding_box_mask] = relevant_grid_points_vals
    #print("gpu",time.time()-start)
    return interpolated_grid

def spread_values_on_grid_points( mesh, grid, field_name, radius=None, binary=False ):
    """ 
    Transfers the mesh field (Tuple1) described by field_name to the grid.
    For each mesh point, finds the grid cell it falls into and associates the mesh field value
    to all the grid nodes defining the corresponding cell. If radius is specified, it associates the 
    the mesh field value to all the grid nodes whose distance from the corresponding mesh point 
    is lower than that radius. 
    Note that no interpolation is computed here (values are just transferred to grid as they are).

    Arguments:
        mesh (vtkDataSet):
            Topology of the mesh
        grid (vtkDataSet):
            Topology of the grid
        field_name (str):
            Name of the DataArray present in mesh that has to be transferred to the grid.
        radius (float):
            Maximum distance between a cell point and a mesh point to have the mesh field associated.
            Default: None 
        binary (bool):
            If True, when field is different from 0, sets the grid value to 1.
            Default: False
    
    Returns:
        vtkDataSet
            Same as grid where the new DataArray "field_name" has been added
    """

    # Create array for grid
    grid_array = vtkDoubleArray()
    grid_array.SetNumberOfComponents(1)
    grid_array.SetName(field_name)
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
    mesh_array = mesh.GetPointData().GetArray(field_name)
    
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

def fixNotMovingCells( mesh, grid, field_name, min_moving_displ=1e-03, thr=1e-20 ):
    """ Create binary field (Tuple1) called field_name in the input grid depending on some conditions
    defined on the 'displacement' field present in the input mesh. These conditions identify the situation
    when a point is visible (= it has an associated displacement which is not null) but not moving ( = its displacement
    magnitude is below a threshold (min_moving_displ)). 
    A value of 1 is associated to a mesh point if the magnitude of the corresponding displacement falls
    between magnitude([thr, thr, thr]) and min_moving_displ. 
    Then, for each mesh point, finds the grid cell it falls into and associated the mesh field value
    to all the grid nodes defining the corresponding cell.
    Note that no interpolation is computed here (values are just transferred to grid as they are).

    Arguments:
        mesh (vtkDataSet):
            Topology of the mesh
        grid (vtkDataSet):
            Topology of the grid
        field_name (str):
            Name of the DataArray present in mesh that has to be transferred to the grid.
        min_moving_displ (float):
            Minimum magnitude of the displacement associated to a point which is considered "moving".
            Default: 1e-03 
        thr (float):
            A point is considered visible (= associated to a not null displacement) if its displacement
            magnitude is above magnitude([thr, thr, thr]).
            Default: 1e-20
    
    Returns:
        vtkDataSet
            Same as grid where the new DataArray "field_name" has been added
    """

    # Create array for grid
    grid_array = vtkDoubleArray()
    grid_array.SetNumberOfComponents(1)
    grid_array.SetName(field_name)
    grid_array.SetNumberOfTuples(grid.GetNumberOfPoints())
    grid_array.Fill(0.0)

    # Create cell locator
    locator = vtkCellLocator()
    locator.SetDataSet(grid)
    locator.Update()
    cell_pts_idx = vtkIdList()

    # Get data array in mesh
    displacement_array = mesh.GetPointData().GetArray('displacement')
    min_visible_displ = np.linalg.norm( np.array([thr, thr, thr]) )

    for i in range( mesh.GetNumberOfPoints() ):

        displ = displacement_array.GetTuple3(i)
        displ_mag = np.linalg.norm( np.array(displ) )

        if displ_mag <= min_moving_displ and displ_mag > min_visible_displ:
            cell = locator.FindCell(mesh.GetPoint(i))
            grid.GetCellPoints(cell,cell_pts_idx)
            for j in range(cell_pts_idx.GetNumberOfIds()):
                grid_array.SetTuple1(cell_pts_idx.GetId(j), 1.0)

    grid.GetPointData().AddArray( grid_array )   
    return grid

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Given a (deformed) mesh with a field called \"displacement\", create a displacement field on a regular grid." )
    group = parser.add_argument_group("Mesh")
    group.add_argument("--mesh", type=filepath, help="Mesh to voxelize. Must have a point array called \"displacement\". Will first be \"undeformed\", i.e. the negative displacement will be applied as a first step (to obtain the original undeformed mesh). Mutually exclusive with mesh_initial and mesh_deformed")
    group.add_argument("--mesh_initial", type=filepath, help="Mesh to voxelize. Requires '--mesh_deformed' to be given, which must be the same mesh as this one, but deformed. Mutually exclusive with '--mesh'")
    group.add_argument("--mesh_deformed", type=filepath, help="Mesh to voxelize. Requires '--mesh_initial' to be given. Mutually exclusive with '--mesh'")
    parser.add_argument("--arrayName", type=str, default="displacement", help="Name of the generated array. Defaults to \"displacement\".")
    parser.add_argument("--outputGrid", default="voxelized.vts", help="Name of the output file to generate. If this file exists, grid size and dimensions are used from the grid and --size and --grid_size are ignored. In this case, the new array is added to the existing file.")
    parser.add_argument("--size", type=float, default=0.3, help="Size of resulting grid (ignored if --outputGrid points to an already existing grid)")
    parser.add_argument("--grid_size", type=int, default=64, help="Number of voxels per dimension (ignored if --outputGrid points to an already existing grid)")
    args = parser.parse_args()

    if args.mesh is None and args.mesh_initial is None and args.mesh_deformed is None:
        parser.error("Either --mesh or --mesh_initial and --mesh_deformed are required.")

    if (args.mesh is not None) and (args.mesh_initial is not None or args.mesh_deformed is not None):
        parser.error("--mesh is mutually exclusive with --mesh_initial and --mesh_deformed!")

    if (args.mesh_initial is None) != (args.mesh_deformed is None):
        parser.error("--mesh_initial and --mesh_deformed must both be defined!")

    # Load the output mesh:
    if os.path.exists( args.outputGrid ):
        grid = loadStructuredGrid( args.outputGrid )

        if grid.GetPointData().GetArray( args.arrayName ):
            err = "The output file {} already has a field named {}!".format(args.outputGrid,args.arrayName)
            raise IOError(err)
        #args.size = grid.GetBounds()
        b = grid.GetBounds()
        args.size = b[1]-b[0]
        args.grid_size = grid.GetDimensions()[0]
    else:
        grid = voxelize.createGrid( args.size, args.grid_size )

    tf = vtkTransform()
    try:
        tf = voxelize.loadTransformationMatrix( grid )
        print("Will reuse transformation matrix found in grid:")
        print(tf)
    except:
        print("No transformation matrix found in grid. Will not apply any transformation.")

    if args.mesh is not None:
        # Load the input mesh:
        mesh = loadMesh( args.mesh )

        # Re-apply any transformation previously applied to the meshes:
        tfFilter = vtkTransformFilter()
        tfFilter.SetTransform( tf )
        tfFilter.SetInputData( mesh )
        tfFilter.Update()
        mesh_initial = tfFilter.GetOutput()

        # Undeform the mesh according to the "displacement" array in mesh:
        mesh = undeform( mesh, scale=tf.GetMatrix().GetElement(0,0) )
    else:

        # Load the initial mesh:
        mesh_initial = loadMesh( args.mesh_initial )
        # Load deformed mesh:
        mesh_deformed = loadMesh( args.mesh_deformed )

        # Re-apply any transformation previously applied to the meshes:
        tfFilter = vtkTransformFilter()
        tfFilter.SetTransform( tf )
        tfFilter.SetInputData( mesh_initial )
        tfFilter.Update()
        mesh_initial = tfFilter.GetOutput()

        tfFilter = vtkTransformFilter()
        tfFilter.SetTransform( tf )
        tfFilter.SetInputData( mesh_deformed )
        tfFilter.Update()
        mesh_deformed = tfFilter.GetOutput()

        print( "Calculating displacement of every point" )
        mesh = calc_displacement( mesh_initial, mesh_deformed )
    
    print( "Interpolating to grid" )

    start = time.time()
    interpolated_grid = interpolate_to_grid( mesh, grid, args.size/(args.grid_size-1) )
    print("cpu", time.time()-start)

    gridGpu = interpolate_to_grid_gpu(mesh, grid, args.size / (args.grid_size - 1))
    gridVTK = torch.from_numpy(vtkPointSetToNumpyArray(interpolated_grid)).float().to(torch.device("cuda"))

    def print_tensor_difference(t_0, t_1):
        equal = torch.eq(t_0, t_1)

        if equal.all():
            print("vectors are equal", "\n")
        else:
            different_values = (~equal).sum()
            difference = t_0 - t_1

            print("difference #values:", different_values.item(), "#equal values:", equal.sum().item())
            print("max diff:", difference.max(0))

    print_tensor_difference(gridGpu, gridVTK)

    print("Writing to {}".format( args.outputGrid ))
    writer = vtkXMLStructuredGridWriter()
    writer.SetFileName( args.outputGrid )
    writer.SetInputData( interpolated_grid )
    # writer.Update()


