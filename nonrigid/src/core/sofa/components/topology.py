import Sofa.Core

from typing import Union
from enum import Enum
from pathlib import Path

LOADER_INFOS = {
    ".obj": "MeshObjLoader",
    ".stl": "MeshSTLLoader",
    ".vtk": "MeshVTKLoader",
    ".msh": "MeshGmshLoader",
    ".gidmsh": "GIDMeshLoader",
}

class Topology(Enum):
    """ Class defining possible topologies. """
    TRIANGLE    = "Triangle"
    TETRAHEDRON = "Tetrahedron"
    HEXAHEDRON  = "Hexahedron"


# Loader
def add_loader(
    parent_node: Sofa.Core.Node, 
    filename: Union[Path, str],
    name: str = "loader",
    transformation: list = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,1]
) ->Sofa.Core.Object:
    """  
    Adds a mesh loader component to the simulation.

    Args:
        parent_node: Node where the loader will be created.
        filename: Path to the mesh to load.
        name: Name that will be given to the created loader.
        transformation: Transform to be applied to the loaded model.
    
    Returns:
        Loader component.
    """
    filepath = Path(filename)
    assert filepath.absolute().is_file(), f"Could not find file {filepath.absolute()}"
    filetype = filepath.suffix
    assert filetype in LOADER_INFOS, f"No loader found for filetype {filetype}"

    loader = parent_node.addObject(
                            LOADER_INFOS[filetype], 
                            filename=str(filepath),
                            name=name,
                            transformation=transformation
                            )
    
    if filetype == ".vtk":
        loader.createSubelements.value = 1
        
    return loader

# Topology
def add_topology(
    parent_node: Sofa.Core.Node, 
    mesh_loader: Sofa.Core.Object,
    topology: Topology,
    name: str = "topology"
) ->Sofa.Core.Object:
    """  
    Adds a topology component to the simulation.

    Args:
        parent_node: Node where the topology component will be created.
        mesh_loader: SOFA loader component.
        topology: Type of topology to be created.
        name: Name that will be given to the created topology.

    Returns:
        Topology container component.
    """
    topology_container = parent_node.addObject(f"{topology.value}SetTopologyContainer", 
                                                name=name, 
                                                src=mesh_loader.getLinkPath()
                                                )
    return topology_container

