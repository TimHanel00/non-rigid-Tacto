"""Common conversions between data types for cached data - no i/o!"""
# structure copied from core.io

from vtk import *
from collections.abc import Callable

from utils import vtkutils

####################################################
## Keep track of all available conversion functions:

# registered type-type pairs with their conversion function
# key = 2-tuples of data types (from, to), value = fun
_registered = {}


def register_type_pair(
    in_type: type,
    out_type: type,
    conversion_func
) -> None:
    """Register a conversion function from one data type to another."""
    if (in_type, out_type) in _registered.keys():
        raise KeyError(f"A conversion function from {in_type} to {out_type} is already registered!")

    _registered[(in_type, out_type)] = conversion_func


# longest file extension iteration used from core.io
def _find_registered_handler(
    in_type: type,
    out_type: type
) -> Callable:
    """Given the input and output data type, find the (previously registered) conversion
    function. If output type cannot be found, try to find a conversion into a subclass. If
    input type cannot be found, try to find a conversion from a superclass.

    Args:
        in_type: Input data type for conversion
        out_type: Output data type or file extension of intended use of output type

    Returns:
        Conversion function from input type to requested output type
    """
    if (in_type, out_type) in _registered.keys():
        return _registered[(in_type, out_type)]
    else:
        # query dictionary for input and output super-/subclasses for first match
        for fun_in, fun_out in _registered.keys():
            # if conversion function can handle superclass, it should be able to handle subclass
            # if downstream job can handle superclass, it should be able to handle subclass
            # issubclass(sub,super), issubclass(myclass, myclass)=True
            if issubclass(in_type, fun_in) and issubclass(fun_out, out_type):
                return _registered[(fun_in, fun_out)]

    raise AssertionError(f"Trying to convert from {in_type} to {out_type}, but no " +\
                         "handler was registered for this conversion. Use " +\
                         "conversions.register_type_pair to register your own!")


# TODO: extend this to automatically build conversion chains
def convert(
        data,
        out_type: type
):
    """Given the data and an output type, check for the appropriate handler and use it
    to convert the data. Output type needs to be given as precisely as needed - if given
    a superclass, the first subclass match will be used for conversion (e.g. request
    vtkPolyData instead of vtkDataSet, otherwise a vtkUnstructuredGrid may be returned).

    Args:
        data: Input data that should be converted.
        out_type: Output data type.

    Returns:
        Input data in requested output format.

    Raises:
        AssertionError if conversion function for these data types is not available.

    """
    converter = _find_registered_handler(type(data), out_type)
    return converter(data)

####################################################
## VTK conversions

# use the one with the geometry filter for unstructured grid to polydata because it preserves topological connectivity
def vtk_unstructured_grid_to_vtk_polydata(
        mesh: vtkUnstructuredGrid
) -> vtkPolyData:
    """Convert an unstructured grid to polygonal data using a vtkGeometryFilter."""
    return vtkutils.extract_surface(mesh)

register_type_pair(vtkUnstructuredGrid, vtkPolyData, vtk_unstructured_grid_to_vtk_polydata)


