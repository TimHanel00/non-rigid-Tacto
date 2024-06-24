import numpy as np

from scipy.stats import truncnorm
from vtk import vtkPoints
from vtkmodules.util import vtkConstants

"""
Functionality taken
from the bachelor thesis work of Jan Biedermann:
"Generating Synthetic Vasculature in Organ-Like 3D
Meshes" in the Translational Surgical Oncology (TSO)
group of the National Center for Tumor Diseases (NCT)
Dresden.
"""


def vtk_to_numpy(points: vtkPoints, starting_index: int=0) -> np.array:
    """
    Converts a vtkPoints array to a numpy array.
    Ideally, this function should be replaced by the vtk_to_numpy function
    in the vtk.util.numpy_support module.
    However, the numpy_support module seems to be broken for certain
    combinations of VTK and numpy versions.

    Args:
        points: the vtkPoints array to convert
        starting_index: the index of the source array
            at which to start the conversion
    """

    dim = 3 # Assume each point has 3 components
    num_points = points.GetNumberOfPoints()

    # Find the correct data type for the target array
    vtk_type = points.GetDataType()
    numpy_type = None

    if vtk_type == vtkConstants.VTK_FLOAT:
        numpy_type = np.float32
    elif vtk_type == vtkConstants.VTK_DOUBLE:
        numpy_type = np.float64
    else:
        raise ValueError()

    bytes_per_dim = np.dtype(numpy_type).itemsize
    starting_byte = bytes_per_dim * dim * starting_index

    # Interpret the vtk points array as a numpy array.
    # Note that this does not copy any data.
    points = np.frombuffer(points.GetData(),
                            count=dim * num_points,
                            offset=starting_byte,
                            dtype=numpy_type)
    
    return points.reshape(num_points, dim)