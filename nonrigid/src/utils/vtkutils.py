import random

import numpy as np
from vtk import *
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
import math
from typing import Optional, Union

def polyDataToUnstructuredGrid(
        pd: vtkPolyData,
) -> vtkUnstructuredGrid:
    """
    Converts an input polydata into an unstructured grid.

    Args:
        pd: The input polydata

    Returns:
        The input polydata converted into an unstructured grid.

    """
    appendFilter = vtkAppendFilter()
    appendFilter.SetInputData(pd)
    appendFilter.Update()
    return appendFilter.GetOutput()

def has_tetra(
        mesh: vtkDataSet,
) -> bool:
    """ 
    Checks if input mesh has tetrahedral elements.
    
    Args:
        mesh: a vtkDataSet object.

    Returns:
        True if the provided object contains tetrahedral elements, False otherwise.
    """
    cell_types = vtkCellTypes()
    mesh.GetCellTypes(cell_types)
    return cell_types.IsType(VTK_TETRA)

def create_random_rigid_transform(
    max_rotation: float, 
    max_translation: float, 
    rot_center: Optional[tuple] = None,
    rnd: Optional[random.Random] = None,
) ->vtkTransform:
    """ 
    Creates a random rigid transformation parametrized on the provided input values.

    Optionally, a rotation center point can be given.
    Also optionally, a (seeded) random number generator can be given.

    Args:
        max_rotation: Maximum rotation angle allowed, in degrees.
        max_translation: Maximum random translation along each axis.
        rot_center: 3D coordinates of the position around which the rotation will be created.
        rnd: Instance of random.Random() that will be used to sample all random values (for deterministic output).
    Returns:
        vtkTransform
        """
    if rnd is None:
        rnd = random

    ang = rnd.uniform(-1, 1)*max_rotation
    axis = np.array([rnd.uniform(-1, 1),
                     rnd.uniform(-1, 1),
                     rnd.uniform(-1, 1)])

    axisNorm = np.linalg.norm(axis)
    if axisNorm == 0:
        # Fallback, just in case
        axis = [1, 0, 0]
    else:
        # Normalize
        axis = axis/axisNorm

    if rot_center is None:
        cx = rot_center[0]
        cy = rot_center[1]
        cz = rot_center[2]
    else:
        cx, cy, cz = 0, 0, 0

    # Create identity transform:
    t = vtkTransform()
    # Handle rotation center:
    t.Translate(-cx, -cy, -cz)
    # Rotate:
    t.RotateWXYZ(ang, axis)
    # Handle rotation center:
    t.Translate(cx, cy, cz)

    # Apply additional random translation:
    dx = rnd.uniform(-1, 1)*max_translation
    dy = rnd.uniform(-1, 1)*max_translation
    dz = rnd.uniform(-1, 1)*max_translation

    t.Translate(dx, dy, dz)
    return t

def calc_center_transform(
        mesh: vtkDataSet,
) ->vtkTransform:
    """ Calculates a transform that would center mesh's bounding box around the origin.

    Args:
        mesh: Mesh for which to caculate the center
    Returns:
        vtkTransform: The transform that would translate 'mesh' so that its bounding box is
        centered around the origin.
    """
    # Get the object bounds:
    bounds = [0]*6;
    mesh.GetBounds(bounds)
    dx = -(bounds[1]+bounds[0])*0.5
    dy = -(bounds[3]+bounds[2])*0.5
    dz = -(bounds[5]+bounds[4])*0.5

    # Create identity transform:
    tf = vtkTransform()
    # Add 
    tf.Translate( (dx,dy,dz) )

    return tf

def apply_transform(
    mesh: vtkDataSet, 
    vtk_transform: vtkTransform,
) ->vtkDataSet:
    """
    Applies the given transform to the input mesh and returns the result.

    Args:
        mesh: The input vtkDataSet object.

    Returns:
        Transformed vtkDataSet.
    """
    tf = vtkTransformFilter()
    tf.SetInputData(mesh)
    tf.SetTransform(vtk_transform)
    tf.Update()
    mesh = tf.GetOutput()
    return mesh


def calc_displacement(
        mesh_initial: vtkDataSet, 
        mesh_deformed: vtkDataSet,
        mesh_initial_indices: Optional[list]=None,
) -> vtkFloatArray:
    """     
    Given an initial and deformed mesh, computes the displacement for each point from the 
    initial mesh to the deformed mesh.

    Important: The function assumes that the ith point in mesh_initial corresponds to
    the ith point in the deformed mesh (and that the meshes have the same number of points).

    Args:
        mesh_initial: The starting vtkDataSet object.
        mesh_deformed: The corresponding deformed vtkDataSet object.
        mesh_initial_indices: For each point of mesh_deformed, the index of the corresponding point in mesh_initial.
            If None, mesh_initial and mesh_deformed must have the same number of points.

    Returns:
        Displacement array.
    """

    if mesh_initial_indices is None:
        mesh_initial_indices = list(range(mesh_initial.GetNumberOfPoints()))
        if not mesh_initial.GetNumberOfPoints() == mesh_deformed.GetNumberOfPoints():
            raise IOError("Either mesh_initial and mesh_deformed have the same number of points, or provide corresponding indices as input!")

    assert len(mesh_initial_indices) == mesh_deformed.GetNumberOfPoints()

    displacement = vtkFloatArray()
    displacement.SetNumberOfComponents(3)
    displacement.SetNumberOfTuples(mesh_initial.GetNumberOfPoints())

    for i in range(mesh_initial.GetNumberOfPoints()):
        displacement.SetTuple3(i, 0.0, 0.0, 0.0)

    for idx_deformed, idx_initial in enumerate(mesh_initial_indices):
        p1 = mesh_initial.GetPoint(idx_initial)
        p2 = mesh_deformed.GetPoint(idx_deformed)
        displ = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
        displacement.SetTuple3(idx_initial, displ[0], displ[1], displ[2])
    return displacement


def calc_mean_position(
        mesh: vtkDataSet,
) -> float:
    """  
    Computes the centroid of the input object.

    Args:
        mesh: A vtkDataSet object.

    Returns:
        3D coordinates of the object centroid.
    """
    pts = vtk_to_numpy(mesh.GetPoints().GetData())
    return pts.mean(axis=0)

def vtk2numpy(
        mesh: vtkDataSet,
) -> np.ndarray:
    """Converts the points in a vtkDataSet into a numpy array. 
    
    Args:
        mesh: A vtkDataSet object.

    Returns:
        Numpy array with the coordinates of the mesh points.
    """
    return vtk_to_numpy(mesh.GetPoints().GetData())


def calc_array_stats(
        arr: vtkDataArray,
) -> tuple:
    """
    Given a vtkDataArray with N components per tuple, this function calculates the length of each
    tuple and then the min, max and mean over all of these lengths.
    
    Args:
        arr: A vtkDataArray with...
    
    Returns:
        minimum, maximum, mean
    """
    raw = vtk_to_numpy(arr)
    l = np.linalg.norm(raw, axis=1)
    minimum = l.min(axis=0).item()
    maximum = l.max(axis=0).item()
    mean = l.mean(axis=0).item()

    return minimum, maximum, mean


def extract_surface(
    mesh: vtkDataSet,
) -> vtkPolyData:
    """  
    Given an input mesh, extracts its outer surface. Converts an input unstructured grid into a polydata object.
    Be careful since PolyData objects cannot contain 3D elements, thus all tetrahedra will be lost with this operation.
    vtkGeometryFilter is used because it is faster and delegates to vtkDataSetSurfaceFilter if it cannot handle a mesh
    (see issue #83). Replaces vtkutils.unstructuredGridToPolyData().

    Args:
        mesh: The vtkDataSet where we want to retain the external surface only.
    
    Returns:
        A vtkDataSet with surface elements only: The input grid converted into a polydata.
    """
    geometryFilter = vtkGeometryFilter()
    geometryFilter.SetInputData(mesh)
    geometryFilter.Update()
    return geometryFilter.GetOutput()


def generate_point_normals(
    mesh: vtkPolyData,
) ->vtkPolyData:
    """  
    Generates point normals for the input mesh.

    Args:
        mesh: A vtkPolyData object. Please be aware that the input must be a polydata in order 
        to calculate point normals.

    Returns:
        The same vtkPolyData provided as input, with the additional "Normals" array.
    """

    # Check if the point normals already exist
    if mesh.GetPointData().HasArray("Normals"):
        return mesh

    # If no normals were found, generate them:
    normal_gen = vtkPolyDataNormals()
    normal_gen.SetInputData(mesh)
    normal_gen.ComputePointNormalsOn()
    normal_gen.ComputeCellNormalsOff()
    normal_gen.SplittingOff()        # Don't allow generator to add points at sharp edges
    normal_gen.Update()
    return normal_gen.GetOutput()


def get_connected_vertices(
    mesh: vtkDataSet, 
    node_id: int,
) ->list:
    """
    Find the neighbor vertices of the node node_id in the provided mesh.

    Args:
        mesh: The vtkDataSet object.
        node_id: The ID of the node for which neighbors are to be found.

    Returns:
        The IDs of the vertices that are neighbors of node_id.
    """
    connected_vertices = []

    # get all cells that vertex 'id' is a part of
    cell_id_list = vtkIdList()
    mesh.GetPointCells(node_id, cell_id_list)

    for i in range(cell_id_list.GetNumberOfIds()):
        c = mesh.GetCell(cell_id_list.GetId(i))
        point_id_list = vtkIdList()
        mesh.GetCellPoints(cell_id_list.GetId(i), point_id_list)
        for j in range(point_id_list.GetNumberOfIds()):
            neighbor_id = point_id_list.GetId(j)
            if neighbor_id != node_id:
                if not neighbor_id in connected_vertices:
                    connected_vertices.append(neighbor_id)
    return connected_vertices


def calc_geodesic_distance(
    mesh: vtkDataSet, 
    node_id: int,
) ->vtkDoubleArray:
    """
    Computes the geodesic distance of each point in the input mesh with respect to the 
    point with index node_id.

    Args:
        mesh: The vtkDataSet object. 
        node_id: The ID of the node for which neighbors are to be found.

    Returns:
        A vtkDoubleArray named "geodesic_distance" containing the geodesic distance 
        of each point in the mesh to the point node_id.
    """

    # pre-compute cell neighbors:
    neighbors = {}
    for i in range(mesh.GetNumberOfPoints()):
        neighbors[i] = get_connected_vertices(mesh, i)

    distance = vtkDoubleArray()
    distance.SetNumberOfTuples(mesh.GetNumberOfPoints())
    distance.SetNumberOfComponents(1)
    distance.Fill(1e10)   # initialize with large numbers
    distance.SetName("geodesic_distance")

    front = [node_id]
    distance.SetTuple1(node_id, 0)

    while len(front) > 0:

        cur_id = front.pop(0)
        cur_pt = mesh.GetPoint(cur_id)
        cur_dist = distance.GetTuple1(cur_id)
        cur_neighbors = neighbors[cur_id]

        # Go through all neighboring points. Check if the distance in those points
        # is still up to date or whether there is a shorter path to them:
        for n_id in cur_neighbors:

            # Find distance between this neighbour and the current point:
            n_pt = mesh.GetPoint(n_id)
            dist = math.sqrt(vtkMath.Distance2BetweenPoints(n_pt, cur_pt))

            new_dist = dist + cur_dist
            if new_dist < distance.GetTuple1(n_id):
                distance.SetTuple1(n_id, new_dist)
                if not n_id in front:
                    # This neighbor node needs to be checked again!
                    front.append(n_id)

    return distance


def calc_surface_area(
    mesh: vtkDataSet
) -> float:
    """
    Computes the surface area of the input mesh and adds it to the mesh as a single entry
    field data float array "surfaceArea".

    The surface area is computed by summing up the areas of all the triangular elements
    of the mesh, done by vtk internally.

    Args:
        mesh: A vtkDataSet object.
    
    Returns:
        The computed surface area.
    """
    computation_filter = vtkIntegrateAttributes()
    computation_filter.SetInputData(mesh)
    computation_filter.Update()
    result_mesh = computation_filter.GetOutputDataObject(0)
    result = result_mesh.GetCellData().GetArray("Area")

    # 2D input data prompt filter to compute area
    if result is not None:
        val = result.GetValue(0)
    # 3D input data prompt filter to compute volume: try again with extracted surface
    elif result_mesh.GetCellData().GetArray("Volume") is not None:
        mesh_surface = extract_surface(mesh)
        computation_filter.SetInputData(mesh_surface)
        computation_filter.Update()
        result_mesh = computation_filter.GetOutputDataObject(0)
        result = result_mesh.GetCellData().GetArray("Area")
        if result is not None:
            val = result.GetValue(0)
        else:
            print(f"Warning: 3D type passed to area computation, but calculation for surface extracted from it with" +
                  f"vtkutils.extract_surface() failed. Returning 0.")
            val = 0.0
    # fail
    else:
        print(f"Warning: non-2D type {type(mesh)} passed to area computation. Returning 0.")
        val = 0.0

    # add to the mesh
    area_arr = make_single_float_array(val, "surfaceArea")
    mesh.GetFieldData().AddArray(area_arr)
    return val


def make_single_float_array(
    value: float,
    name: str = "array", 
) ->vtkFloatArray:
    """  
    Converts a float into a vtkFloatArray.

    Args:
        value: Value associated to the array.
        name: Name that will be associated to the created vtk array.

    Returns:
        A vtkFloatArray filled with the specified value and with the specified name.
    """
    arr = vtkFloatArray()
    arr.SetNumberOfTuples(1)
    arr.SetNumberOfComponents(1)
    arr.SetTuple1(0, value)
    arr.SetName(name)
    return arr


def transform_to_str(
    tf: vtkTransform,
) ->str:
    """
    Converts the input vtkTransform into a string.

    Args:
        tf: The input vtkTransform.
    
    Returns:
        String version of the input transform.
    """
    s = ""
    m = tf.GetMatrix()
    for i in range(4):
        for j in range(4):
            s += str(m.GetElement(i, j)) + " "
    s = s[:-1]  # remove trailing space
    return s

def transform_from_str(
    s: str,
) ->vtkTransform:
    """
    Converts the input string into a vtkMatrix.

    Args:
        s: A string containing exactly 16 values, separated by spaces (as output by
        transform_to_str)
    Returns:
        A vtkTransform where the matrix has been constructed from the given 16 values.
    """
    m = vtkMatrix4x4()
    vals = s.split()
    assert len(vals) == 16, "For transform_from_str to work, input must contain string " +\
            "with exactly 16 double values, separated by spaces."
    for i in range(4):
        for j in range(4):
            v = float(vals[i*4+j])
            m.SetElement(i, j, v)

    tf = vtkTransform()
    tf.SetMatrix(m)
    return tf


def find_corresponding_indices(
    mesh: vtkDataSet,
    points: np.ndarray,
) ->list:
    """
    For each point in the points array, returns the index of the closest point in the input mesh. 

    Args:
        mesh1: The input vtkDataSet.
        points: Nx3 array of points.

    Returns:
        A list of int with the ids of mesh vertices closest to each point.

    """
    locator = vtkPointLocator( )
    locator.SetDataSet( mesh )
    locator.SetNumberOfPointsPerBucket(1)
    locator.BuildLocator()

    corresponding_indices = []

    for idx in range(len(points)):
        point = points[idx]
        mesh_id = locator.FindClosestPoint( point )
        corresponding_indices.append(mesh_id)
    return corresponding_indices

def remap_arrays(
    input_geometry: vtkDataSet,
    source: vtkDataSet,
    sharpness: float = 1e3
) -> vtkDataSet:
    """ Remap arrays from source onto input_geometry.

    Returns:
        A dataset of the same type as 'input_geometry', but with the arrays from 'source'
        interpolated onto it.
    """

    kernel = vtkGaussianKernel()
    kernel.SetSharpness(sharpness)

    probe = vtkPointInterpolator()
    probe.SetInputData(input_geometry)
    probe.SetKernel(kernel)
    probe.SetNullPointsStrategyToClosestPoint()
    probe.SetSourceData(source)
    probe.Update()
    output = probe.GetOutput()

    return output

def copy_arrays(
    input_geometry: vtkDataSet,
    source: vtkDataSet,
    copy_point_data: bool = True,
    copy_cell_data: bool = True,
) -> vtkDataSet:
    """ Copy arrays from source onto input_geometry.

    Note: This performs a shallow copy only.
    Note: If an array with the same name already exists, this will be overwritten.

    Returns:
        'input_geometry', but with the arrays from 'source'.
    """

    if copy_point_data:
        assert source.GetNumberOfPoints() == input_geometry.GetNumberOfPoints, \
                "To copy data, source and geometry must have the same number of points!"
        source_pd = source.GetPointData()
        tgt_pd = input_geometry.GetPointData()
        for i in range(source_pd.GetNumberOfArrays()):
            arr = source_pd.GetArray(i)
            if tgt_pd.HasArray(arr.GetName()):
                tgt_pd.RemvoeArray(arr.GetName())
            tgt_pd.AddArray(arr)

    if copy_cell_data:
        assert source.GetNumberOfCells() == input_geometry.GetNumberOfCells, \
                "To copy data, source and geometry must have the same number of cells!"
        source_cd = source.GetCellData()
        tgt_cd = input_geometry.GetCellData()
        for i in range(source_cp.GetNumberOfArrays()):
            arr = source_cp.GetArray(i)
            if tgt_cp.HasArray(arr.GetName()):
                tgt_cp.RemvoeArray(arr.GetName())
            tgt_cp.AddArray(arr)
    
    return output

def calc_mesh_size(
    mesh: vtkDataSet
) -> (float, float, float):
    """ Calculate the dimensions of the mesh's bounding box by evaluating xmax-xmin etc.

    Args:
        mesh: A vtkDataSet object.

    Returns:
        size_x, size_y, size_z: The dimensions of the bounding box of the mesh.

    """
    bounds = [0, 0, 0, 0, 0, 0]
    mesh.GetBounds(bounds)
    size_x = bounds[1] - bounds[0]
    size_y = bounds[3] - bounds[2]
    size_z = bounds[5] - bounds[4]
    return size_x, size_y, size_z

def calc_volume(
        mesh: Union[vtkUnstructuredGrid, vtkPolyData]
) -> float:
    """
    Computes the volume of the input mesh.

    It can handle either an enclosed volume computation of a vtkPolyData triangle surface mesh
    or a volume computation of a vtkUnstructuredGrid with volumetric elements by integration.

    Args:
        mesh: A vtkDataSet object, restricted to a triangle surface mesh or data types with volumetric
            elements.

    Returns:
        The computed volume. 0.0 if there is an error (no processing available for this data type etc.).
    """
    val = 0.0
    if isinstance(mesh, vtkPolyData):
        val = _calc_volume_polydata(mesh)
    elif isinstance(mesh, vtkUnstructuredGrid):
        val = _calc_volume_unstructured_grid(mesh)
    else:
        print(f"Warning: Type {type(mesh)} can currently not be handled by vtkutils volume computation. Returning 0.")

    return val

def _calc_volume_polydata(
        mesh: vtkPolyData
) -> float:
    """
    Computes the enclosed volume of the input surface mesh.

    Only works for triangle meshes because it uses vtkMassProperties.

    Args:
        mesh: A vtkDataSet object with a triangle surface mesh.

    Returns:
        The computed volume. 0.0 if nothing can be computed.
    """
    computation_filter = vtkMassProperties()
    computation_filter.SetInputData(mesh)
    # there will be a printout but no exception if the vtkPolyData is empty
    computation_filter.Update()
    # this filter is written such that it returns 0.0 for any problems
    return computation_filter.GetVolume()

def _calc_volume_unstructured_grid(
        mesh: vtkUnstructuredGrid
) -> float:
    """
    Computes the volume of the input mesh using the vtkIntegrateAttributes filter.

    The volume is computed by summing up the volumes of all 3D elements of the mesh. The used filter does
    not compute enclosed volumes. Therefore, if there are no volumetric elements the result will be invalid
    (the filter will compute the surface area or line length unsolicited).

    Args:
        mesh: A vtkDataSet object with volumetric elements.

    Returns:
        The computed volume. 0.0 if no volumetric elements can be found in the input.
    """
    computation_filter = vtkIntegrateAttributes()
    computation_filter.SetInputData(mesh)
    computation_filter.Update()
    # from https://gitlab.kitware.com/vtk/vtk/-/blob/v9.2.0/Filters/Parallel/Testing/Python/TestIntegrateAttributes.py
    result = computation_filter.GetOutputDataObject(0)
    val = result.GetCellData().GetArray("Volume")
    if val is not None:
        return val.GetValue(0)
    else:
        print(f"Warning: non-volumetric type {type(mesh)} passed to volume computation. Returning 0.")
        return 0.0

##########################################
## Error handling:

class ErrorObserver:
    """ Class that can catch vtk errors.

    To use, instanciate and use vtk's ".AddObserver()" methods.
    Then, after running the vtk filter, use ErrorObserver.ErrorOccured
    to check if something went wrong.
    In this case, ErrorObserver.ErrorMessage() can be used to
    retrieve the error message.
    """

    def __init__(self):
        self.__ErrorOccurred = False
        self.__ErrorMessage = None
        self.CallDataType = 'string0'

    def __call__(self, obj, event, message):
        self.__ErrorOccurred = True
        self.__ErrorMessage = message

    def ErrorOccurred(self):
        occ = self.__ErrorOccurred
        self.__ErrorOccurred = False
        return occ

    def ErrorMessage(self):
        return self.__ErrorMessage


