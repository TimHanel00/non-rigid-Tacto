####################################################
## Handles common disk input and output operations
import vtk
import yaml
from typing import Union, List

from core.log import Log
from blocks.scene_generation.vascusynth_wrapper.vascular_tree import VascularTree

####################################################
## Keep track of all available loading/saving functions:
_registered = {}
_filetype_datatype_mapping = {}
def register_filetype(
    extension: str, 
    loader_fnc, 
    writer_fnc,
) ->None:
    """  
    Args:
        extension:
        loader_fnc:
        writer_fnc:
    """
    if not extension[0] == ".":
        extension = "." + extension

    if extension in _registered.keys():
        raise KeyError(f"A reader/writer for {extension} is already registered!")

    _registered[extension] = {"loader":loader_fnc, "writer":writer_fnc}

def find_registered_handlers(
    filename: str,
):
    """ Given the filename, find the (previously registered) functions which should be used
    to read/write this kind of data. If multiple matches are available, return the longest,
    to allow something like ".tar.gz" vs ".gz".

    Args:
        filename:

    Returns:
        callable functions?
    """

    # Find the correct reader/writer:
    matching_extensions = []
    for key in _registered.keys():
        if filename.endswith(key):
            matching_extensions.append(key)

    assert len(matching_extensions) > 0, f"Trying to read or write {filename}, but no " +\
            "handler was registered for this file type. Use io.register_filetype to " +\
            "register your own!"

    longest_extension = max(matching_extensions, key=len)
    writer = _registered[longest_extension]["writer"]
    loader = _registered[longest_extension]["loader"]
    return writer, loader

    
def write(
    filename: str, 
    data,
) ->None:
    """Given a filename, checks for the appropriate handler and use it to write the data
    
    Args:
        filename:
        data:
    """
    writer, _ = find_registered_handlers(filename)
    writer(filename, data)
    Log.log( module="IO", msg=f"Wrote: {filename}" )

def read(
    filename: str,
):
    """Given a filename, checks for the appropriate handler and use it to read the file
    
    Args:
        filename:
    """
    _, reader = find_registered_handlers(filename)
    data = reader(filename)
    Log.log( module="IO", msg=f"Read: {filename}" )
    return data

####################################################
## Keep track of which writer requires which input data type:

def map_filetype_to_datatype(
        extension: str,
        writer_dtype: type
) -> None:
    """ Keep track of which writer requires which input data type. Relies on
    the writer function for each filetype to be unique as enforced by
    register_filetype().

    Args:
        extension: File type extension as ".ext".
        writer_dtype: Return type of the writer function for this file type.

    Notes:
        Could be extended to ask for the reader return type but this may
        never be necessary because one can call read() and then check that
        data's type directly.

    """
    if not extension[0] == ".":
        extension = "." + extension

    if extension not in _registered.keys():
        # needs to be changed for registering readers as well
        raise KeyError(f"No writer for {extension} has been registered! " + \
                       f"Use io.register_filetype to register your own!")

    if extension in _filetype_datatype_mapping.keys():
        # needs to be changed for registering readers as well
        raise KeyError(f"A writing type for {extension} is already registered!")

    _filetype_datatype_mapping[extension] = {"writer": writer_dtype}

def find_writer_input_type(
        filename: str
) -> type:
    """Given a filename, find the input data type of the writer function.
    Utility to find the target of type conversions at runtime.

    Args:
        filename: Input file name with desired file extension.

    Returns:
        Data type that the writer function for this file type can deal with.
    """

    # Find the correct reader/writer:
    matching_extensions = []
    for key in _filetype_datatype_mapping.keys():
        if filename.endswith(key):
            matching_extensions.append(key)

    assert len(matching_extensions) > 0, f"Trying to query the input type for writing {filename}, but no " + \
                                         "handler was registered for this file type. Use io.register_filetype to " + \
                                         "register your own!"

    longest_extension = max(matching_extensions, key=len)
    return _filetype_datatype_mapping[longest_extension]["writer"]

####################################################
## Utility function to ensure a filename has the expected ending:
def check_extension(
    filename: str, 
    expected_extension: str,
) ->None:
    """Utility function to ensure the filename has the expected extension. 
    
    Args:
        filename:
        expected_extension:
    """
    assert filename.lower().endswith(expected_extension.lower()), \
            f"Expected {filename} to have extension" +\
            expected_extension + "!"


####################################################
## STL:

def load_stl( 
    filename: str, 
) ->vtk.vtkPolyData:
    """Load STL file, return as vtkPolyData. 
    
    Args:
        filename:

    Returns:
        vtkPolyData
    """

    check_extension(filename, ".stl")

    reader = vtk.vtkSTLReader()
    reader.SetFileName( filename )
    reader.Update()
    mesh = reader.GetOutput()

    return mesh

def write_stl( 
    filename: str, 
    mesh: vtk.vtkPolyData,
) ->None:
    """ Write vtkPolyData to STL. """

    check_extension(filename, ".stl")

    writer = vtk.vtkSTLWriter()
    writer.SetFileName( filename )
    writer.SetInputData( mesh )
    writer.Update()

## Register:
register_filetype( ".stl", load_stl, write_stl )
# vtkSTLWriter needs vtkPolyData:
# https://gitlab.kitware.com/vtk/vtk/-/blob/master/IO/Geometry/vtkSTLWriter.cxx#L498
map_filetype_to_datatype(".stl", vtk.vtkPolyData)

####################################################
## OBJ:

def load_obj( 
    filename: str, 
) ->vtk.vtkPolyData:
    """ Load OBJ file, return as vtkPolyData. 

    Args:
        filename:

    Returns:
        vtkPolyData
    """

    check_extension(filename, ".obj")

    reader = vtk.vtkOBJReader()
    reader.SetFileName( filename )
    reader.Update()
    mesh = reader.GetOutput()

    #### NOTE:
    # vtkOBJReader may produce duplicated vertices, usually to allow for hard shading.
    # To avoid this, a vtkCleanPolyData filter can be used. However, this filter not only
    # removes duplicated vertices but also removes "unused" vertices, i.e. points which
    # aren't part of any cell. I've found no way to disable this. vtkStaticCleanPolyData
    # works similarly, and the current documeentation claims that removing unused verts
    # can be turned off, but the function SetRemoveUnusedPoints() doesn't exist in my version.
    # Tested vtk version: 9.0.1, installed via pip.
    # The issue is that we have meshes which only contain points, which we currently use to mark
    # fixed boundary conditions, for example.
    # The (ugly) workaround is to check whether the mesh has cells. If not, we treat it like a
    # points-only object and let all points pass. If it _does_ have cells, it will be cleaned,
    # because in this case I assume we're interested in a surface mesh. However, this will remove
    # individual unused points if present.
    if mesh.GetNumberOfCells() > 0:
        cleaner = vtk.vtkCleanPolyData()
        #cleaner.SetRemoveUnusedPoints( False )
        cleaner.SetInputData( mesh )
        cleaner.Update()
        mesh = cleaner.GetOutput()

    return mesh

def write_obj( 
    filename: str, 
    mesh: vtk.vtkPolyData,
) ->None:
    """ Write vtkPolyData to OBJ. 
    
    Args:
        filename:
        mesh: 
    """

    check_extension(filename, ".obj")

    writer = vtk.vtkOBJWriter()
    writer.SetFileName( filename )
    writer.SetInputData( mesh )
    writer.Update()

## Register:
register_filetype( ".obj", load_obj, write_obj )
# vtkOBJWriter needs vtkPolyData:
# https://gitlab.kitware.com/vtk/vtk/-/blob/master/IO/Geometry/vtkOBJWriter.cxx#L404
map_filetype_to_datatype(".obj", vtk.vtkPolyData)


####################################################
## PLY:

def load_ply( 
    filename: str, 
) ->vtk.vtkPolyData:
    """ Load PLY file, return as vtkPolyData. 
    
    Args:
        filename:

    Returns:
        vtkPolyData
    """

    check_extension(filename, ".ply")

    reader = vtk.vtkPLYReader()
    reader.SetFileName( filename )
    reader.Update()
    mesh = reader.GetOutput()

    return mesh

def write_ply( 
    filename: str, 
    mesh: vtk.vtkPolyData,
) ->None:
    """ Write vtkPolyData to PLY.     

    Args:
        filename:
        mesh: 
    """

    check_extension(filename, ".ply")

    writer = vtk.vtkPLYWriter()
    writer.SetFileName( filename )
    writer.SetInputData( mesh )
    writer.Update()

## Register:
register_filetype( ".ply", load_ply, write_ply )
# vtkPLYWriter needs vtkPolyData:
# https://gitlab.kitware.com/vtk/vtk/-/blob/master/IO/PLY/vtkPLYWriter.cxx#L509
map_filetype_to_datatype(".ply", vtk.vtkPolyData)


####################################################
## VTK:

def load_vtk( 
    filename: str, 
) ->vtk.vtkUnstructuredGrid:
    """ Load VTK file, return as vtkUnstructuredGrid. 
    
    Args:
        filename:

    Returns:
        vtkUnstructuredGrid.
    """

    check_extension(filename, ".vtk")

    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName( filename )
    reader.Update()
    mesh = reader.GetOutput()

    return mesh

def write_vtk( 
    filename: str, 
    mesh: vtk.vtkUnstructuredGrid,
) ->None:
    """ Write vtkUnstructuredGrid to VTK. 
            
    Args:
        filename:
        mesh: 
    """

    check_extension(filename, ".vtk")

    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName( filename )
    writer.SetInputData( mesh )
    writer.Update()

## Register:
register_filetype( ".vtk", load_vtk, write_vtk )
# vtkUnstructuredGridWriter needs vtkUnstructuredGridBase:
# https://gitlab.kitware.com/vtk/vtk/-/blob/master/IO/Legacy/vtkUnstructuredGridWriter.cxx#L197
# but as long as we're not using vtkMappedUnstructuredGrids anywhere it's fine to request vtkUnstructuredGrid
map_filetype_to_datatype(".vtk", vtk.vtkUnstructuredGrid)

####################################################
## VTU:

def load_vtu( 
    filename: str, 
) ->vtk.vtkUnstructuredGrid:
    """ Load VTU file, return as vtkUnstructuredGrid. 
    
    Args:
        filename:

    Returns:
        vtkUnstructuredGrid.
    """

    check_extension(filename, ".vtu")

    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName( filename )
    reader.Update()
    mesh = reader.GetOutput()

    return mesh

def write_vtu( 
    filename: str, 
    mesh: vtk.vtkUnstructuredGrid,
) ->None:
    """ Write vtkUnstructuredGrid to VTU. 
        
    Args:
        filename:
        mesh: 
    """

    check_extension(filename, ".vtu")

    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName( filename )
    writer.SetInputData( mesh )
    writer.Update()

## Register:
register_filetype( ".vtu", load_vtu, write_vtu )
# vtkXMLUnstructuredGridWriter needs vtkUnstructuredGridBase:
# https://gitlab.kitware.com/vtk/vtk/-/blob/master/IO/XML/vtkXMLUnstructuredGridWriter.cxx#L54
# but as long as we're not using vtkMappedUnstructuredGrids anywhere it's fine to request vtkUnstructuredGrid
map_filetype_to_datatype(".vtu", vtk.vtkUnstructuredGrid)

####################################################
## VTS:

def load_vts( 
    filename: str, 
) ->vtk.vtkStructuredGrid:
    """ Load VTS file, return as vtkStructuredGrid. 
    
    Args:
        filename:

    Returns:
        vtkUnstructuredGrid.
    """

    check_extension(filename, ".vts")

    reader = vtk.vtkXMLStructuredGridReader()
    reader.SetFileName( filename )
    reader.Update()
    mesh = reader.GetOutput()

    return mesh

def write_vts( 
    filename: str, 
    mesh: vtk.vtkStructuredGrid,
) ->None:
    """ Write vtkStructuredGrid to VTS. 
        
    Args:
        filename:
        mesh: 
    """

    check_extension(filename, ".vts")

    writer = vtk.vtkXMLStructuredGridWriter()
    writer.SetFileName( filename )
    writer.SetInputData( mesh )
    writer.Update()

## Register:
register_filetype( ".vts", load_vts, write_vts )
# vtkXMLStructuredGridWriter needs vtkStructuredGrid:
# https://gitlab.kitware.com/vtk/vtk/-/blob/master/IO/XML/vtkXMLStructuredGridWriter.cxx#L49
map_filetype_to_datatype(".vts", vtk.vtkStructuredGrid)

####################################################
## VTP:

def load_vtp( 
    filename: str, 
) ->vtk.vtkPolyData:
    """ Load VTP file, return as vtkPolyData. 
    
    Args:
        filename:

    Returns:
        vtkPolyData
    """

    check_extension(filename, ".vtp")

    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName( filename )
    reader.Update()
    mesh = reader.GetOutput()

    return mesh

def write_vtp( 
    filename: str, 
    mesh: vtk.vtkPolyData,
) ->None:
    """ Write vtkPolyData to VTP. 
        
    Args:
        filename:
        mesh: 
    """

    check_extension(filename, ".vtp")


    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName( filename )
    writer.SetInputData( mesh )
    writer.Update()

## Register:
register_filetype( ".vtp", load_vtp, write_vtp )
# vtkXMLPolyDataWriter needs vtkPolyData:
# https://gitlab.kitware.com/vtk/vtk/-/blob/master/IO/XML/vtkXMLPolyDataWriter.cxx#L59
map_filetype_to_datatype(".vtp", vtk.vtkPolyData)

####################################################
## YAML:

def load_yaml( 
    filename: str, 
) ->dict:
    """ Load YAML file, return as dict. 
    
    Args:
        filename:

    Returns:
        dict
    """

    check_extension(filename, ".yaml")
    with open(filename, "r") as stream:
        data = yaml.safe_load(stream)

    return data

def write_yaml( 
    filename: str, 
    data: dict,
) ->None:
    """ Write dict to YAML. 
        
    Args:
        filename:
        data: 
    """

    check_extension(filename, ".yaml")
    
    with open(filename, 'w') as stream:
        yaml.dump(data, stream, default_flow_style=False)

## Register:
register_filetype( ".yaml", load_yaml, write_yaml )
# this may need more work in utils.conversions counterpart if more file formats are included that require dict as input
map_filetype_to_datatype(".yaml", dict)

####################################################
## LOG Files (simple text files where each line is a log entry):

def load_log(
    filename: str, 
) -> list:
    """ Load LOG file, return as list of strings, one entry per line.
    
    Args:
        filename:

    Returns:
        dict
    """

    check_extension(filename, ".log")
    with open(filename, "r") as stream:
        data = stream.readlines()

    return data

def write_log( 
    filename: str, 
    data: Union[str, List[str]],
) ->None:
    """ Write string or list of strings to LOG.
        
    Args:
        filename:
        data: 
    """

    check_extension(filename, ".log")
    
    with open(filename, 'w') as stream:
        stream.writelines(data)

## Register:
register_filetype( ".log", load_log, write_log )
# no filetype datatype mapping for now because logging is mostly issued


####################################################
## Diff Files (simple text files containing a git diff):

def load_diff(
        filename: str,
) -> str:
    """ Load diff file, return as string.

    Args:
        filename: Path to the target file.

    Returns:
        Diff file as a single string with several lines. That is how the GitPython
        repo object returns it, too.
    """

    check_extension(filename, ".diff")
    with open(filename, "r") as stream:
        data = stream.readlines()

    return " ".join(data)


def write_diff(
        filename: str,
        data: Union[str, List[str]]
) -> None:
    """ Write git diff to a diff file.

    Args:
        filename: Path to the target file including desired name.
        data: String or list of strings to write. Should already have newlines.
    """

    check_extension(filename, ".diff")

    with open(filename, 'w') as stream:
        stream.writelines(data)

## Register:
register_filetype(".diff", load_diff, write_diff)
# no filetype datatype mapping for now

####################################################
## GXL files (XML file syntax describing a vascular tree structure with its nodes and edges):

def load_gxl(
        filename: str,
) -> VascularTree:
    """ Load a vascular tree structure description (nodes, edges)
    from file generated by VascuSynth (https://doi.org/10.54294/j0ws9u).

    Args:
        filename: Path to the target file.
    """

    check_extension(filename, ".gxl")
    tree = VascularTree(filename)

    return tree


def write_gxl(
        filename: str,
        tree: VascularTree
) -> None:
    """ Store a vascular tree structure description (nodes, edges)
    in the format also used by VascuSynth (https://doi.org/10.54294/j0ws9u).

    Args:
        filename: Path to the target file including desired name.
        tree: VascularTree object that holds data to be written and can be called to
            execute its storing function.
    """

    check_extension(filename, ".gxl")

    Log.log(module="IO", msg=f"Trying to write: {filename} but GXL writing is not implemented yet!", severity="WARN")

    pass

## Register:
register_filetype(".gxl", load_gxl, write_gxl)
map_filetype_to_datatype(".gxl", VascularTree)

####################################################
## GRAPHML files (XML file syntax describing a vascular tree structure with its nodes and edges):

def load_graphml(
        filename: str,
) -> VascularTree:
    """ Load a vascular tree structure description (nodes, edges)
    from file generated by the VascularTree class and intraoperable with e.g. the
    VesselVio software.

    Args:
        filename: Path to the target file.
    """

    check_extension(filename, ".graphml")
    tree = VascularTree(filename)

    return tree


def write_graphml(
        filename: str,
        tree: VascularTree
) -> None:
    """ Store a vascular tree structure description (nodes, edges)
    in the format used by the VascularTree class and intraoperable with
    e.g. the VesselVio software.

    Args:
        filename: Path to the target file including desired name.
        tree: VascularTree object that holds data to be written and can be called to
            execute its storing function.
    """

    check_extension(filename, ".graphml")

    tree.store_graphml(filename)


## Register:
register_filetype(".graphml", load_graphml, write_graphml)
map_filetype_to_datatype(".graphml", VascularTree)

####################################################
## TXT Files (simple text files):

def load_txt(
        filename: str,
) -> list:
    """ Load text file, return as list of strings, one entry per line.

    Args:
        filename:

    Returns:
        dict
    """

    check_extension(filename, ".txt")
    with open(filename, "r") as stream:
        data = stream.readlines()

    return data


def write_txt(
        filename: str,
        data: Union[str, List[str]],
) -> None:
    """ Write string or list of strings to text file.

    Args:
        filename:
        data:
    """

    check_extension(filename, ".txt")

    with open(filename, 'w') as stream:
        stream.writelines(data)


## Register:
register_filetype(".txt", load_txt, write_txt)
# no filetype datatype mapping for now because logging is mostly issued