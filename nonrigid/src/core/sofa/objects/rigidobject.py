import Sofa.Core
from typing import Optional, Union

from utils.sofautils import get_bbox
from core.sofa.components.topology import Topology, add_loader, add_topology
from core.sofa.components.models import add_collision_models

class RigidObject():
    """
    Class describing a static and rigid object that can be added to the simulation for collision computation, 
    visualization, or both.
    """

    #########################################################
    ####### CREATION
    #########################################################
    def __init__(
                self, 
                parent_node: Sofa.Core.Node, 
                node_name: str = "Object",
                visual_model: Optional[str] = None,
                color: list = [1,0,0,1],
                collision_model: Optional[str] = None,
                contact_stiffness: float = 10,
                collision_group: int = 0,
                moving: int = 0,
                simulated: int = 0,
                collision_triangles: bool = True,
                collision_lines: bool 	= True,
                collision_points: bool 	= True,
                collision_spheres: bool 	= False,
                collision_spheres_radii: Union[float, list] = 0.005,
                map2parent: bool = False,
                ):
        """ 
        Keyword arguments:
            parent_node (Sofa Node):
                parent node to which the object is attached.
            name (str):  
                Name of the node where the object is created (default 'Plane').
            visual_model (str): 
                Path to the surface mesh for visualization (default None).
            collision_model (str):
                Path to the surface mesh for collision (default None).
            map2parent (bool):
                if True, BarycentricMapping is added to map the object to parent node (default None).
            color (list):
                RGBA for the visual surface (default [1,0,0,1]).
            contact_stiffness (int):
                stiffness associated to the collision models for collision response (default 10).
            collision_group (int):
                objects of the same group do not collide among themselves (default 0).

        """
        self.parent_node  	 = parent_node
        self.visual_model 	 = visual_model
        self.collision_model = collision_model
        self.map2parent 	 = map2parent
        self.state 			 = None

        if collision_spheres == True:
            collision_triangles = False
            collision_lines 	= False
            collision_points 	= False
            
        # --------------------------------------------------#
        # Scene graph creation
        # --------------------------------------------------#
        node = self.parent_node.addChild(node_name)
        self.node 	= node
        visual_node = node # init visual node with current node 

        # Load surface topology
        surface_mesh_name = 'surface_mesh'
        surface_mesh = [ s for s in [self.collision_model, self.visual_model] if not s is None ][0]
        loader = add_loader( parent_node=node,
                            filename = surface_mesh,
                            name = surface_mesh_name 	
                            )
        self.main_topology = add_topology( parent_node=node, 
                                              mesh_loader=loader,
                                              topology=Topology.TRIANGLE,
                                              name=f"{surface_mesh_name}_topology"
                                              )
        
        xmin, xmax, ymin, ymax, zmin, zmax = get_bbox( self.main_topology.position.value )
        self.bounding_box = [xmin, ymin, zmin, xmax, ymax, zmax]

        # Define collision and/or visual models
        if not self.collision_model is None:
            self.state = self.node.addObject('MechanicalObject', 
                                            name=f"{node_name}_state", 
                                            showObject=False,
                                            )

            add_collision_models(
                                 self.node,
                                 moving=moving, 
                                 simulated=simulated, 
                                 contact_stiffness=contact_stiffness, 
                                 group=collision_group,
                                 triangles=collision_triangles,
                                 lines=collision_lines,
                                 points=collision_points,
                                 spheres=collision_spheres,
                                 radius=collision_spheres_radii,
                                 )
            
            if not (self.visual_model is None):
                visual_node = self.node.addChild('Visual'+node_name)
            
        if not (self.visual_model is None):	
            self.__visualize_surface(visual_node, color)
                        
        if self.map2parent:
            node.addObject('BarycentricMapping')


    #########################################################
    ####### CUSTOM - private
    #########################################################
    def __visualize_surface( self, parent_node, color ):
        parent_node.addObject('VisualStyle', displayFlags='showVisual hideWireframe')

        if self.collision_model is None:
            parent_node.addObject('OglModel', name="VisualSurfaceOGL", src="@surface_mesh", color=color)
        elif self.visual_model == self.collision_model:
            parent_node.addObject('OglModel', name="VisualSurfaceOGL", src="@../surface_mesh", color=color)
            parent_node.addObject('IdentityMapping')
        else:
            surface_mesh_name = "visual_surface_mesh"
            loader = add_loader( parent_node=parent_node,
                                filename = self.visual_model,
                                name = surface_mesh_name 	
                                )
            add_topology( parent_node=parent_node,
                         mesh_loader=loader,
                         topology=Topology.TRIANGLE,
                         name=f"{surface_mesh_name}_topology"
                         )
            
            parent_node.addObject('OglModel', name="VisualSurfaceOGL", src="@../surface_mesh", color=color)
            parent_node.addObject('BarycentricMapping')
        

