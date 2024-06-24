from typing import Optional

import Sofa.Core
from core.sofa.components.topology import Topology, add_loader, add_topology
from utils.sofautils import convert2rigid

class MechanicalPoints():
    """
    Mechanical object containing only DOFs, usually for visualization purposes.
    DOFs can be defined either as a list of positions, or can be associated to a given surface mesh.
    """

    #########################################################
    ####### CREATION
    #########################################################
    def __init__(
                self, 
                parent_node: Sofa.Core.Node, 
                node_name: str = "MechanicalPoints",
                position: list = [0,0,0],
                quaternion: list = [0,0,0,1],
                map_frames: bool = False,
                surface_mesh: Optional[str] = None,
                map2parent: bool = False,
                view: bool = True,
                scale: int = 2,
                color: list = [1,1,1,1],
                ):
        """ 
        Args:
            parent_node (Sofa Node):
                parent node to which the object is attached.
            name (str):  
                Name of the node where points will be created (default 'VisiblePoints').
            position (list):
                Nx3 list of DOFs coordinates.
            quaternion (list):
                Nx4 list of DOFs orientations.
            map_frames (bool):
                if True, the MechanicalObject containing the points will be templated Rigid3d such that
                both position and quaternion will be saved. 
            surface_mesh (str):
                if surface_mesh is provided, the DOFs are taken from the loaded topology. 
                In this case, input position and orientation will be neglected.
            map2parent (bool):
                if True, a Barycentric mapping is added to map DOFs to the parent node.
            view (bool):
                if False, visualization will be deactivated.
            scale (int):
                Dimension of the points, for visualization purposes.
            color (list):
                RGBDA for visualization of the points.			
        """
        super(MechanicalPoints, self).__init__()

        self.parent_node  = parent_node
        self.position	  = position
        self.quaternion   = quaternion
        self.surface_mesh = surface_mesh
        self.map_frames   = map_frames
        self.state 		  = None
        
        # --------------------------------------------------#
        # Scene graph creation
        # --------------------------------------------------#
        node = self.parent_node.addChild(node_name)

        template = "Vec3d"

        if self.map_frames:
            template = "Rigid3d"
            scale /= 1000.

            # If we have 3D points coordinates as input, convert to rigid template syntax
            if self.surface_mesh is None:
                self.position = convert2rigid(self.position, self.quaternion)

        if self.surface_mesh:
            surface_mesh_name = "surface_mesh"
            surface_mesh_loader = add_loader( parent_node=node,
                                            filename=self.surface_mesh,
                                            name=surface_mesh_name
                                            )
            add_topology( parent_node=node,
                          mesh_loader=surface_mesh_loader,
                          topology=Topology.TRIANGLE,
                          name=f"{surface_mesh_name}_topology"
                          )
            
            self.state = node.addObject('MechanicalObject', 
                                        name=f"{node_name}_state", 
                                        src=surface_mesh_loader.getLinkPath(), 
                                        template=template, 
                                        showObject=view, 
                                        showObjectScale=scale, 
                                        showColor=color
                                        )
        else:
            # Create MechanicalObject and fill it with provided positions.
            self.state = node.addObject('MechanicalObject', 
                                name=f"{node_name}_state", 
                                position=self.position,
                                template=template, 
                                showObject=view, 
                                showObjectScale=scale, 
                                showColor=color,
                                listening=1
                                )

        if map2parent:
            node.addObject('BarycentricMapping')

        
    #########################################################
    ####### CUSTOM
    #########################################################
    def update_positions(self, new_position, new_quaternion=None):
        if self.map_frames:
            if new_quaternion is None:
                new_quaternion = self.quaternion
            new_position = convert2rigid(new_position, new_quaternion)

        self.state.size     	  = len(new_position)
        self.state.position.value = new_position
