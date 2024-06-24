import Sofa.Core

from typing import Optional, Tuple, Union
from enum import Enum

from numpy import isin

from core.sofa.components.topology import Topology, add_loader, add_topology

class MappingType(Enum):
    """ Class defining possible types of mapping between SOFA models. """
    RIGID = "RigidMapping"
    BARYCENTRIC = "BarycentricMapping"
    IDENTITY = "IdentityMapping"


def add_collision_models(
    parent_node: Sofa.Core.Node, 
    contact_stiffness: float = 10,
    moving: int = 1,
    simulated: int = 1,
    triangles: bool = False,
    lines: bool = False,
    points: bool = True,
    spheres: bool = False,
    radius: Union[float, list] = 0.01,
    spheres_number: int = 1,
    group: int = 0,
    triangles_color: list = [0.56,0.56,0.56,0],
    lines_color: list     = [0.56,0.56,0.56,1],
    points_color: list    = [0.56,0.56,0.56,1],
    spheres_color: list   = [0.56,0.56,0.56,1],
) ->None:
    """  
    Adds collision model/s in specified node.

    Args:
        parent_node: Node where the collision models will be created.
        contact_stiffness: Stiffness of the contacts, in case penalty method is used for collision response.
        moving: if True, the object with associated collision model can move between time steps.
        simulated: if True, the object with associated collision model can deform between time steps.
        triangles: Collision detection and response will use triangles (can be used together with lines and points).
        lines: Collision detection and response will use lines (can be used together with triangles and points).
        points: Collision detection and response will use points (can be used together with lines and triangles).
        spheres: Collision detection and response will use spheres.
        radius: Radius of the collision spheres.
        spheres_number: Number of collision spheres.
        group: Group number associated to the collision models. Collisions will be computed only between objects belonging to the same collision group.
        triangles_color: RGBA for triangles.
        lines_color: RGBA for lines.
        points_color: RGBA for points.
        spheres_color: RGBA for spheres. 
    """
    
    if spheres:
        if spheres_number > 1 or isinstance(radius, list): 
            if isinstance(radius, float):
                radius = [radius]*spheres_number      
            parent_node.addObject('SphereCollisionModel', listRadius=radius, moving=moving, simulated=simulated, contactStiffness=contact_stiffness, group=group, color=spheres_color)
        else:
            parent_node.addObject('SphereCollisionModel', radius=radius, moving=moving, simulated=simulated, contactStiffness=contact_stiffness, group=group, color=spheres_color)
        
    else:
        if triangles:
            parent_node.addObject('TriangleCollisionModel', moving=moving, simulated=simulated, contactStiffness=contact_stiffness, group=group, color=triangles_color)
        if lines:
            parent_node.addObject('LineCollisionModel'    , moving=moving, simulated=simulated, contactStiffness=contact_stiffness, group=group, color=lines_color)
        if points:
            parent_node.addObject('PointCollisionModel'   , moving=moving, simulated=simulated, contactStiffness=contact_stiffness, group=group, color=points_color)


def add_visual_models(
    parent_node: Sofa.Core.Node, 
    display_flags: list = ["showVisual", "showWireframe"],
    color: list = [1, 0, 1, 1],
    visual_mesh: Optional[str] = None,
    mapping_type: Optional[MappingType] = None
    ) ->tuple:
    """  
    Adds a visual model to the specified node.

    Args:
        parent_node: Node where the visual model needs to be added.
        display_flags: List of strings with visual flags.
        color: RGBA of the visual model.
        visual_mesh: If specified, the visual mesh will be loaded from this path.
        mapping_type: if specified, the appropriate mapping component will be added to map the visual model with its parent node.
    
    Returns:
        tuple with loader and topology.
    """

    if not visual_mesh is None:
        loader = add_loader(
                    parent_node=parent_node,
                    filename=visual_mesh,
                    name=f"{parent_node.name.value}_loader" 	
                    )

        topology = add_topology( 
                        parent_node=parent_node,
                        mesh_loader=loader,
                        topology=Topology.TRIANGLE,
                        name=f"{parent_node.name.value}_topology"
                        )

    parent_node.addObject('VisualStyle', displayFlags=display_flags)
    parent_node.addObject('OglModel', color=color)

    if not mapping_type is None:
        add_mapping(
            parent_node=parent_node,
            mapping_type=mapping_type
            )

    return loader, topology

def add_mapping(
    parent_node: Sofa.Core.Node, 
    mapping_type: MappingType = MappingType.BARYCENTRIC
    ):
    """  
    Adds a mapping to the specified node.

    Args:
        parent_node: Node where the mapping is added.
        mapping_type: The mapping type to be added.
    """
    parent_node.addObject(f"{mapping_type.value}")
