import os
import vtk
import numpy as np
from math import dist
from pathlib import Path
from vtk.util.numpy_support import numpy_to_vtk
from typing import List, Tuple, Dict

from .branch import Branch, BranchFactory
from .vascular_tree import VascularTree
from .utils import vtk_to_numpy
from core import io

# this needs reworking to avoid for loops - thoughts see VascularTree

"""
Methods to generate a 3D model from the graph representation 
of a vascular tree. The 3D model is made up of a set of tubes 
that are joined at bifurcation points.
The algorithm used to generate the bifurcation meshes
is based on an algorithm presented in reference [1].

Functionality partially extended, structure adapted
from the bachelor thesis work of Jan Biedermann:
"Generating Synthetic Vasculature in Organ-Like 3D
Meshes" in the Translational Surgical Oncology (TSO)
group of the National Center for Tumor Diseases (NCT)
Dresden.

References:
[1] Chlebiej, M., Zurada, A., Gielecki, J. et al.
Customizable tubular model for n-furcating blood vessels
and its application to 3D reconstruction of the cerebrovascular system.
Med Biol Eng Comput 61, 1343-1361 (2023).
https://doi.org/10.1007/s11517-022-02735-5
"""


def get_branch_polydata(
    branch: Branch,
    num_sides: int
) -> vtk.vtkPolyData:
    """
    Generates a tube around a branch centerline.

    Args:
        num_sides: the number of sides of each tube in the tree
    """

    tube_filter = vtk.vtkTubeFilter()
    branch_source = branch.get_source()

    tube_filter.SetInputConnection(branch_source.GetOutputPort())
    tube_filter.SetNumberOfSides(num_sides)
    tube_filter.CappingOff()
    tube_filter.SetRadius(branch.radius)

    geometry_filter = vtk.vtkGeometryFilter()
    geometry_filter.SetInputConnection(tube_filter.GetOutputPort())
    geometry_filter.Update()

    return geometry_filter.GetOutput()


def get_projections(
    points: np.array,
    sphere_center: np.array,
    tube_endpoint: np.array,
    r: float,
    delta_r: float,
) -> np.array:
    """
    Finds projection of tube endpoints onto the surface of a sphere.
    For more information on this step, see reference [1].
    """

    # Normalizes an array of vectors
    normalized = lambda vecs: np.array([x / np.linalg.norm(x) for x in vecs])

    proj_center = sphere_center + (r - delta_r) * normalized([tube_endpoint - sphere_center])
    proj_vecs = normalized(points - proj_center)
    proj_points = proj_center + delta_r * proj_vecs

    return proj_points


def remove_bifurcation_caps(
    bif_polydata: vtk.vtkPolyData,
    num_branches: int,
    num_sides: int,
) -> None:
    """
    Bifurcation meshes are generated using delaunay triangulation.
    However, the resulting meshes are closed.
    Hence, this function inserts holes into the bifurcation mesh
    so that the bifurcating tubes can be attached.

    Args:
        bif_polydata: Polydata representing the closed bifurcation mesh
        num_branches: Number of branches adjacent to this bifurcation
        num_sides: the number of sides of each tube in the tree
    """

    bif_polys = bif_polydata.GetPolys()
    bif_polys_cleaned = vtk.vtkCellArray()

    id_list = vtk.vtkIdList()
    bif_polys.InitTraversal()

    # Iterate over all polygons of the bifurcation mesh
    while (bif_polys.GetNextCell(id_list)):

        remove = False
        # Extract the vertex ids corresponding to the current polygon
        num_ids = id_list.GetNumberOfIds()
        ids = np.array([id_list.GetId(i) for i in range(num_ids)])

        for branch_idx in range(num_branches):

            # If all vertices of this polygon are projected endpoints
            # of a single common tube, this polygon is an end cap polygon.
            # Remove this polygon.
            above_min_index = ids >= branch_idx * num_sides
            below_max_index = ids < (branch_idx + 1) * num_sides
            is_cap_point = np.logical_and(above_min_index,
                                          below_max_index)
            if np.all(is_cap_point):
                remove = True
                break

        # Keep track of polygons that should not be removed
        if not remove:
            bif_polys_cleaned.InsertNextCell(id_list)

    bif_polydata.SetPolys(bif_polys_cleaned)


def get_bifurcation_polydata(
    tube_centers: np.array,
    tube_endpoints: vtk.vtkPoints,
    bifurcation_center: np.array,
    num_sides: int
) -> vtk.vtkPolyData:
    """
    Generates the bifurcation mesh using Delaunay triangulation.
    This step closely follows the procedure in reference [1].
    """

    dim = 3  # Number of components per point
    num_branches = len(tube_centers)

    num_points = tube_endpoints.GetNumberOfPoints()
    points_numpy = vtk_to_numpy(tube_endpoints)
    points_numpy = points_numpy.reshape(num_branches, -1, dim)

    # Find parameters for the projection of the tube endpoints
    # onto a sphere
    # TODO Try different configurations for r and delta_r
    r = 0.5 * min(dist(x, bifurcation_center) for x in tube_centers)
    delta_r = 0.5 * r

    proj_points = np.ndarray((num_branches, num_points // num_branches, dim))

    # Execute the projection of tube endpoints onto a sphere
    for i, points in enumerate(points_numpy):
        proj_points[i] = get_projections(points,
                                         bifurcation_center,
                                         tube_centers[i],
                                         r,
                                         delta_r)
    proj_points = proj_points.reshape((num_points, dim))

    # Use delaunay triangulation to triangulate the projected endpoints
    # Translate and scale the projected endpoints in order to avoid
    # issues with floating point precision.
    delauny_points_numpy = (proj_points - bifurcation_center) / r

    # Todo remove debugging part from here
    # for debugging
    # before projecting the points:
    debugging_points = vtk.vtkPoints()
    points_numpy_reshaped = points_numpy.reshape((num_points, dim))
    points_numpy_reshaped = (points_numpy_reshaped - bifurcation_center) / r
    # after projecting the points:
    all_points = np.append(points_numpy_reshaped, delauny_points_numpy, axis=0)
    # bifurcation center to check for an indexing error
    all_points = np.append(all_points, np.array([bifurcation_center]), axis=0)
    debugging_points.SetData(numpy_to_vtk(all_points))
    debugging_polydata = vtk.vtkPolyData()
    debugging_polydata.SetPoints(debugging_points)
    # to here -----------------------------------------------

    delaunay_points = vtk.vtkPoints()
    delaunay_points.SetData(numpy_to_vtk(delauny_points_numpy))
    delaunay_polydata = vtk.vtkPolyData()
    delaunay_polydata.SetPoints(delaunay_points)

    delaunay = vtk.vtkDelaunay3D()
    delaunay.SetTolerance(0.0)
    delaunay.SetInputData(delaunay_polydata)
    delaunay.Update()

    geometry_filter = vtk.vtkGeometryFilter()
    geometry_filter.SetInputConnection(delaunay.GetOutputPort())
    geometry_filter.Update()

    # Undo the translation and scaling that was
    # applied prior to the triangulation
    transform = vtk.vtkTransform()
    transform.Translate(bifurcation_center)
    transform.Scale((r, r, r))

    transformer = vtk.vtkTransformPolyDataFilter()
    transformer.SetInputConnection(geometry_filter.GetOutputPort())
    transformer.SetTransform(transform)
    transformer.Update()

    bif_polydata = transformer.GetOutput()
    #bif_polydata = geometry_filter.GetOutput()  # debugging
    remove_bifurcation_caps(bif_polydata, num_branches, num_sides)
    return bif_polydata


def link_bifurcation(
    polys: vtk.vtkCellArray,
    tube_offset: int,
    bifurcation_offset: int,
    num_sides: int,
) -> None:
    """
    Connects the endpoints of a vessel tube to the corresponding
    bifurcation mesh.

    Args:
        num_sides: The number of sides of each tube in the tree
    """

    for i in range(num_sides):

        idx1 = tube_offset + i
        idx2 = tube_offset + (i + 1) % num_sides
        idx3 = bifurcation_offset + (i + 1) % num_sides
        idx4 = bifurcation_offset + i

        polys.InsertNextCell(4, [idx1, idx2, idx3, idx4])


def branch_cone_has_intersection(
    intersected: Branch,
    intersecting: Branch,
    bifurcation_center: np.array,
) -> bool:
    """
    In order to generate bifurcation meshes, tube endpoints are
    projected onto a sphere. The projected points together
    with their original endpoints form a cone.
    See reference [1] for more details on this.
    This function heuristically determines whether the cone
    of the branch "intersected" is being intersected by the branch
    "intersecting".
    """

    p_intersecting = intersecting.get_min_endpoint()
    p_intersected = intersected.get_min_endpoint()
    dp = p_intersecting - p_intersected

    cone_axis = (bifurcation_center - p_intersected)
    cone_axis /= np.linalg.norm(cone_axis)

    # Let p_interescting_proj be the projection of p_intersecting
    # onto the cone axis.
    # Then v_basepoint = p_intersecting - p_intersecting_proj
    v_basepoint = dp - dp.dot(cone_axis) * cone_axis
    v_basepoint_length = np.linalg.norm(v_basepoint)
    v_basepoint /= v_basepoint_length
    if v_basepoint_length < intersected.radius:
        return True

    # Find a line from the base circle of the cone
    # to the tip of the cone.
    # This line is determined such that the distance between
    # it and p_intersecting is minimal.
    # It's tangent vector is stored as "boundary_axis"
    basepoint = p_intersected + intersected.radius * v_basepoint
    boundary_axis = (bifurcation_center - basepoint)
    boundary_length = np.linalg.norm(boundary_axis)

    # Find the minimum distance between the boundary axis and
    # p_intersecting. Using this, check whether the boundary axis
    # intersects the circumsphere of the end cap of "intersecting".
    # TODO Use exact disk-line intersection test instead of this heuristic
    t = boundary_axis.dot(p_intersecting - basepoint) / boundary_length**2
    t = np.clip(t, 0.0, 1.0)
    distance = np.linalg.norm(p_intersecting - (basepoint + t * boundary_axis))
    return distance < intersecting.radius


def get_branches(
    tree: VascularTree,
    branch_factory: BranchFactory,
) -> Tuple[Dict[int, Branch], List[List[int]], List[Tuple[float, float, float]]]:
    """
    This function generates Branch instances for the entire tree.
    In order for bifurcation meshes to be generated using the algorithm
    in reference [1], the corresponding branches must be non-intersecting.
    To this end, this function iteratively updates
    the t_min and t_max attributes of each branch.
    It may be the case that no combination
    of values t_min, t_max with t_min < t_max
    and no intersections to adjacent branches is found.
    In this case, this function sets t_min = 0.0 or t_max = 1.0 and
    no bifurcation mesh will be generated.

    Args:
        tree: VascularTree managing all structural information (nodes, edges)
        branch_factory: a BranchFactory instance that can produce
            Branch instances for this tree
    """

    branches, bifurcations, centers = tree.create_linked_branches(branch_factory)

    for i, (parent, *children) in enumerate(bifurcations):

        parent_branch = branches[parent]

        # Swap the t_min and t_max values of the parent branch,
        # so that only t_min values need to be updated here
        parent_branch.swap_orientation()

        # Initialize a flag indicating whether values t_min
        # were found for all branches in this bifurcation
        parent_branch.bifurcation_failed = False

        bifurcation_branches = [parent_branch] + \
            [branches[child] for child in children]

        bifurcation_center = np.array(centers[parent])

        dt = 0.02  # Increment for updating t_min
        epsilon = 1e-6

        # Stores pairs of branches that may still intersect
        tube_queue = [(x, y) for x in bifurcation_branches
                      for y in bifurcation_branches if x != y]

        while tube_queue:

            intersected, intersecting = tube_queue.pop(0)

            # If intersecting.t_min + dt >= intersecting.t_max,
            # no solution could be found for this bifurcation
            if intersecting.t_min + dt + epsilon >= intersecting.t_max:

                parent_branch.bifurcation_failed = True

                # Reset the corresponding t_min values
                for branch in bifurcation_branches:
                    branch.t_min = 0.0

                break

            # Update t_min
            intersecting.t_min += dt

            # If this condition is met, the endpoint of "intersected" has
            # not been moved yet and no projection cone can be computed
            if intersected.t_min < dt - epsilon:

                tube_queue.append((intersected, intersecting))
                continue

            # If "intersecting" still intersects the projection cone of
            # "intersected", further changes are necessary
            if branch_cone_has_intersection(intersected,
                                            intersecting,
                                            bifurcation_center):
                tube_queue.append((intersected, intersecting))

        # Revert the parent branch to its original orientation
        parent_branch.swap_orientation()

    return branches, bifurcations, centers


def insert_branch_polydata(
    tree_points: vtk.vtkPoints,
    tree_strips: vtk.vtkCellArray,
    branches: dict,
    num_sides: int,
) -> dict:
    """
    Generates a tube for each vessel branch in the tree.
    The resulting points and triangle strips are inserted into the
    tree_points and tree_strips arrays.

    Args:
        num_sides: The number of sides of each tube in the tree
    """

    # Current index at which to store new points in the tree_points array
    vertex_index = 0

    # Dict that assigns to each branch_id a starting offset and an
    # ending offset.
    # The offsets point to the positions of the tube cap points
    # in the tree_points array.
    # These offsets can be used when connecting the tube endpoints
    # to their bifurcation meshes.
    vertex_offsets = dict()

    # For each branch, insert the branch poly data into the tree
    # and set the vertex offsets
    for branch_id, branch in branches.items():

        start_offset = vertex_index

        tube = get_branch_polydata(branch, num_sides)
        num_points = tube.GetPoints().GetNumberOfPoints()
        tree_points.InsertPoints(vertex_index, num_points, 0, tube.GetPoints())
        tree_strips.Append(tube.GetStrips(), vertex_index)

        vertex_index += num_points
        end_offset = vertex_index - num_sides
        vertex_offsets[branch_id] = start_offset, end_offset

    return vertex_offsets


def add_tube_caps(
    tree_polydata: vtk.vtkPolyData,
    vertex_offsets: dict,
    bifurcations: list,
    num_sides: int,
) -> None:
    """
    Add end caps to terminal branches.

    Args:
        num_sides: The number of sides of each tube in the tree
    """

    # Find terminal branches for which to add endcaps
    parent_ids = [bif[0] for bif in bifurcations]
    child_ids = sum([bif[1:] for bif in bifurcations], [])
    terminal_node_ids = set(child_ids).difference(set(parent_ids))

    # Compute a triangulation for a single, arbitrary terminal end cap.
    # The same triangulation can be used for all other end caps,
    # as long as the correct vertex offset is added to the vertex ids.
    cap_polydata = vtk.vtkPolyData()
    cap_points = vtk.vtkPoints()
    cap_points.InsertPoints(0, num_sides, 0, tree_polydata.GetPoints())
    cap_polydata.SetPoints(cap_points)

    # Find polygons for the end cap using delaunay triangulation
    triangulator = vtk.vtkDelaunay2D()
    triangulator.SetInputData(cap_polydata)
    triangulator.SetTolerance(0.0)
    triangulator.Update()

    cap_polys = triangulator.GetOutput().GetPolys()
    tree_polys = tree_polydata.GetPolys()

    # Insert the determined polygons as the end cap of the root branch
    tree_polys.Append(cap_polys, 0)

    # Insert the determined polygons as end caps of all terminal branches
    for terminal_node_id in terminal_node_ids:

        _, start_index = vertex_offsets[terminal_node_id]
        tree_polys.Append(cap_polys, start_index)


def extend_child_tube(
    branch: Branch,
    offset: int,
    tree_points: vtk.vtkPoints,
    num_sides: int,
) -> None:
    """
    Extends a tube to its original length in the t_min direction.

    Args:
        num_sides: The number of sides of each tube in the tree
    """

    # Get the poly data corresponding to the extended tube
    branch.t_min = 0.0
    tube_extended = get_branch_polydata(branch, num_sides)

    # Replace the endpoints of the tube with those of the extended tube
    for i in range(num_sides):
        point = tube_extended.GetPoint(i)
        tree_points.SetPoint(offset + i, point)


def extend_parent_tube(
    branch: Branch,
    *args,
) -> None:
    """
    Parent-tube version of the extend_child_tube function.
    Extends a tube to its original length in the t_max direction.
    """

    branch.swap_orientation()
    extend_child_tube(branch, *args)
    branch.swap_orientation()


def generate_model(
    num_sides: int,
    tree: VascularTree,
    branch_factory: BranchFactory,
) -> vtk.vtkPolyData:
    """
    Executes 3D model generation.

    Args:
        num_sides: The number of sides of each tube in the tree
        tree: VascularTree managing all structural information (nodes, edges)
        branch_factory: a BranchFactory instance that can produce
            Branch instances for this tree

    Returns:
        3D model of the VascularTree as a surface mesh.
    """

    branches, bifurcations, centers = get_branches(tree, branch_factory)

    tree_points = vtk.vtkPoints()
    tree_polys = vtk.vtkCellArray()
    tree_strips = vtk.vtkCellArray()
    vertex_offsets = insert_branch_polydata(tree_points,
                                            tree_strips,
                                            branches,
                                            num_sides)
    # Current index at which to store new points in the tree_points array
    vertex_index = tree_points.GetNumberOfPoints()

    for i, (parent, *children) in enumerate(bifurcations):
        # Do not generate a bifurcation if t_min and t_max values
        # for the corresponding branches could not be determined
        if branches[parent].bifurcation_failed:
            continue
        # Before inserting a new bifurcation mesh into the tree poly data,
        # store it in a separate poly data
        # so it can be smoothed individually
        bifurcation_polys = vtk.vtkCellArray()
        smoothing_polydata = vtk.vtkPolyData()
        smoothing_polydata.SetPoints(tree_points)
        smoothing_polydata.SetPolys(bifurcation_polys)

        _, parent_offset = vertex_offsets[parent]

        # Determine the tube centers and tube endpoints for the
        # get_bifurcation_polydata function
        c_parent = branches[parent].get_max_endpoint()
        tube_centers = [c_parent]
        tube_endpoints = vtk.vtkPoints()
        tube_endpoints.InsertPoints(0 * num_sides, num_sides, parent_offset, tree_points)

        for i, child in enumerate(children):
            child_offset, _ = vertex_offsets[child]
            c_child = branches[child].get_min_endpoint()
            tube_centers.append(c_child)
            tube_endpoints.InsertPoints((i + 1) * num_sides, num_sides, child_offset, tree_points)

        # Attempt to generate the bifurcation mesh
        bifurcation = get_bifurcation_polydata(
            np.array(tube_centers),  # centers of the 3 branch cylinder end circles facing the bifurcation
            tube_endpoints,  # points describing the surface of the 3 branch cylinder ends facing the
                             # bifurcation (cylinders already discretized)
            np.array(centers[parent]),  # bifurcation center = original place in the bifurcation in the (linear) tree
            num_sides  # number of polygon strips for each branch cylinder
        )

        # 
        bifurcation.GetPoints().SetDataTypeToFloat()


        if bifurcation.GetPoints() is not None:
            num_points = bifurcation.GetPoints().GetNumberOfPoints()
        else:
            num_points = 0
        num_branches = len(tube_centers)

        # If the bifurcation generation was unsuccessful, extend
        # the tubes so that they intersect at the bifurcation point.
        # Then, continue with the next bifurcation.
        if num_points != num_branches * num_sides:

            offset, _ = vertex_offsets[parent]
            extend_parent_tube(branches[parent], offset, tree_points, num_sides)

            for child in children:

                offset, _ = vertex_offsets[child]
                extend_child_tube(branches[child], offset, tree_points, num_sides)

            continue

        # Insert the bifurcation mesh into the tree poly data
        tree_points.InsertPoints(vertex_index, num_points, 0, bifurcation.GetPoints())
        bifurcation_polys.Append(bifurcation.GetPolys(), vertex_index)

        # Link the parent branch to the bifurcation mesh
        link_bifurcation(bifurcation_polys, parent_offset,
                         vertex_index + 0 * num_sides, num_sides)

        # Link all child branches to the bifurcation mesh
        for i, child in enumerate(children):

            child_offset, _ = vertex_offsets[child]
            link_bifurcation(bifurcation_polys,
                             child_offset,
                             vertex_index + (i + 1) * num_sides,
                             num_sides)

        # Smooth the generated bifurcation
        # TODO Ultimately it would be best if smoothing were
        # applied to the entire tree at once, instead of individual bifurcations
        smoother = vtk.vtkWindowedSincPolyDataFilter()
        smoother.SetInputData(smoothing_polydata)
        smoother.SetNumberOfIterations(30)
        smoother.SetPassBand(0.0001)
        smoother.SetEdgeAngle(120.0)
        smoother.SetFeatureAngle(90.0)
        smoother.NormalizeCoordinatesOn()
        smoother.BoundarySmoothingOff()
        smoother.Update()

        # Update tree_points to use smoothed points
        smoothed_points = smoother.GetOutput().GetPoints()
        tree_points.InsertPoints(vertex_index, num_points,
                                 vertex_index, smoothed_points)
        tree_polys.Append(bifurcation_polys)
        vertex_index += num_points

    tree_polydata = vtk.vtkPolyData()
    tree_polydata.SetPoints(tree_points)
    tree_polydata.SetStrips(tree_strips)
    tree_polydata.SetPolys(tree_polys)

    add_tube_caps(tree_polydata, vertex_offsets, bifurcations, num_sides)
    return tree_polydata

