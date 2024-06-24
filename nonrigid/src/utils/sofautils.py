from typing import Optional
from numpy import linalg as LA
import numpy as np
from scipy import spatial
from vtk import *
from vtk.util import numpy_support

def get_bbox(position):
	""" 
	Gets the bounding box of the object defined by the given vertices.

	Arguments
	-----------
	position : list
		List with the coordinates of N points (position field of Sofa MechanicalObject).

	Returns
	----------
	xmin, xmax, ymin, ymax, zmin, zmax : floats
		min and max coordinates of the object bounding box.
	"""
	try:
		points_array = np.asarray(position)
	except:
		points_array = numpy_support.vtk_to_numpy(position)

	m = np.min(points_array, axis=0)
	xmin, ymin, zmin = m[0], m[1], m[2]

	m = np.max(points_array, axis=0)
	xmax, ymax, zmax = m[0], m[1], m[2]

	return xmin, xmax, ymin, ymax, zmin, zmax

def check_valid_displacement(displacement, low_thresh=0.0, high_thresh=np.nan):
	""" 
	Analyzes the provided displacement and tells if the displacement is associated with 
	(1) a stable deformation (i.e., lower than high_thresh), (2) a significant deformation 
	(i.e., higher than low_thresh).

	Arguments
	-----------
	displacement : array_like
		Nx3 array with x,y,z displacements of N points.
	low_thresh : float
		value below which the displacement is considered negligible (default 0.0).
	high_thresh : float
		value above which the displacement is associated to unstable deformation (default NaN).
	
	Returns
	-----------
	is_stable, is_moving
		* is_stable = False if there is at least one displacement whose norm is >= high_thresh
		  or there is at least one displacement with NaN value
		* is_moving = False if there is at least one displacement whose norm is <= low_thresh 
	"""
	is_stable = True
	is_moving = True

	displ_norm = LA.norm(displacement, axis=1)
	max_displ_norm = np.amax(displ_norm)

	if np.isnan(high_thresh): 
		if np.isnan(max_displ_norm):
			#print('Simulation is unstable')
			is_stable = False
			is_moving = True
	elif max_displ_norm >= high_thresh:
		#print('Max displacement is too big')
		is_stable = False
		is_moving = True
	
	if max_displ_norm <= low_thresh:
		#print('Max displacement is too small')
		is_stable = True
		is_moving = False

	return is_stable, is_moving

def get_distance_np( array1, array2 ):
	"""
	For each point in array2, returns the Euclidean distance with its closest point in array1 and
	the index of such closest point. 
	
	Arguments
	----------
	array1 (ndarray):
		N1 x M array with the points.
	array2 (ndarray):
		N2 x M array with the points.
	
	Returns
	----------
	dist:
		N2 x 1 Euclidean distance of each point of array2 with the closest point in array1.
		dist contains the same result as: 	np.nanmin( distance.cdist( array1, array2 ), axis=1 )
	indexes:
		N2 x 1 Indices of closest point in array1

	"""
	mytree = spatial.cKDTree(array1)
	dist, indexes = mytree.query(array2)
	return dist, indexes

def get_indices_in_roi( 
	positions: list, 
	center: Optional[np.ndarray] = None,
	radius: Optional[float] = 0.01,
	bbox: Optional[list] = None,
	) ->list:
	""" Get the indices of the points falling within the specified bounding box.
	
	Args:
	    positions: N x 3 list of points coordinates.
	    center:
	    radius:
        bbox: [xmin, ymin, zmin, xmax, ymax, zmax] extremes of the bounding box.
	
	Returns: indices: List of indices of points enclosed in the bbox.

	"""
	if center is not None:
		positions = np.asarray(positions)
		center_position = center.reshape((1,-1))
		dist, idx = get_distance_np(center_position, positions)
		indices = np.where(dist <= radius)[0]
		indices = indices.tolist()
	elif bbox is not None:
		assert len(bbox) == 6
		indices = []
		for i, x in enumerate( positions ):
			if x[0] >= bbox[0] and x[0] <= bbox[3] and x[1] >= bbox[1] and x[1] <= bbox[4] and x[2] >= bbox[2] and x[2] <= bbox[5]:
				indices.append( i )
	return indices

def convert2rigid( positions, quaternions=[0,0,0,1] ):
	"""
	Converts an Nx3 list of coordinates, that describe 3D coordinates of a SOFA object templated as Vec3d template into
	the corresponding Nx7 (position+quaternion) format, needed for SOFA Rigid template.
	Orientation (as quaternion) associated to each point can also be provided. If a single quaternion is provided,
	the same value is associated to all the points.
	
	Arguments
	----------
	positions (list):
		N x 3 list of coordinates.
	quaternions (list):
		1 x 7 or N x 7 list of quaternions associated to the points.

	Returns
	----------
	list:
		N x 7 list of coordinates concatenated with the corresponding quaternion, for compatibility with Rigid template.
	"""
	positions = np.asarray( positions )
	positions = positions.reshape((-1,3))
	num_positions = positions.shape[0]

	quaternions = np.asarray( quaternions )
	quaternions = quaternions.reshape((-1,4))
	num_quaternions = quaternions.shape[0]

	if num_positions == num_quaternions:
		quat = quaternions
	elif num_quaternions == 1:
		quat = np.tile(quaternions, (num_positions, 1))

	rigid_positions = np.hstack( (positions, quat) )
	return rigid_positions.tolist()

def sofa2vtk( state, topology ):
	"""
	Converts a sofa object to a vtkPolyData. 
	
	Parameters
	----------
	state ():
		SOFA mechanical object
	topology (?):
		SOFA object containing information about triangles (either topology or a loader)

	"""

	# Convert the current positions to VTK:
	points = vtkPoints()
	for i, p in enumerate( state.position.value ):
		points.InsertNextPoint( p )

	# Convert triangles to VTK:
	cells = vtkCellArray()
	cellTypes = []
	for i, t in enumerate( topology.triangles.value ):
		cells.InsertNextCell( 3, t )
		cellTypes.append( VTK_TRIANGLE )

	# Create vtk polydata from the data:
	polydata = vtkPolyData()
	polydata.SetPoints( points )
	polydata.SetPolys( cells )
	
	return polydata

def sofa2vtu( state, vtk_mesh ):
	"""
	Converts a sofa object to a vtkUnstructuredGrid. 
	
	Parameters
	----------
	state ():
		SOFA mechanical object
	topology (?):
		SOFA object containing information about triangles (either topology or a loader)

	"""

	# Convert the current positions to VTK:
	updated_points = numpy_support.numpy_to_vtk(state.position.value)
	vtk_mesh.GetPoints().SetData(updated_points)
	
	output_vtk_mesh = vtkUnstructuredGrid()
	output_vtk_mesh.DeepCopy(vtk_mesh)
	return output_vtk_mesh

