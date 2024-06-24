import numpy as np
from typing import Optional, Union

import Sofa.Core

class FixedBoundaries:
    
    def __init__(
        self, 
        parent_node: Sofa.Core.Node, 
        indices: tuple = (0), 
        roi_obj: Sofa.Core.Object = None, 
        name: str = 'FixedConstraint', 
        view: bool = True,
    ):
        self.indices = indices

        if roi_obj:
            self.indices = f"{roi_obj.getLinkPath()}.indices"
        
        fixed_node = parent_node.addObject(
                    'FixedConstraint', 
                    indices=self.indices,
                    listening=1,
                    name=name,
                    showObject=view
                    )
        self.node = fixed_node



class SpringBoundaries(Sofa.Core.Controller):
    """ Springs connecting two objects """

    def __init__( 
        self, 
        parent_node: Sofa.Core.Node,
        attached_object: Optional[Sofa.Core.Controller] = None,
        start_indices: list = [0],
        end_points: list = [0,0,0],
        name: str = "SpringAttachments",
        stiffness: Union[list, float] = 0.0,
        rest_length: Union[list, float] = 0.0,
        active: bool = False,
        incremental: bool = False,
        num_steps: int = 10,
        view_end_points: bool = False,
        view: bool = True
    ):
        """
        Args:
            parent_node: parent node to which the object is attached.
            attached_object: User-defined class with the components describing the tissue which is subject to 
                spring forces. It is used to retrieve the link to the MechanicalObject for connecting the springs.
                If not provided, we will assume the MechanicalObject is in the parent node. 
            start_indices:  List of N indices of the organ mesh nodes where springs will be attached.
            end_points: Nx3 array with coordinates of the end points where the springs will be attached. Such points are
                fixed and do not move. First point is attached to the first index in start_indices.
            name: Name of the node where the springs are created (default 'SpringAttachments').
            stiffness: Stiffness of the springs. If a single float is provided, the same value is used for all the springs.
                If a list is provided, it must be of length N (one value per spring).
            rest_length: Rest length of the springs. 
                If a single float is provided, the same value is used for all the springs.
                If a list is provided, it must be of length N (one value per spring).
            active: if True, springs are activated. Otherwise, spring stiffness is set to zero
                at the beginning and activated once the flag is manually triggered during the simulation.
            incremental: if True, spring stiffness is incremented at each simulation step (if "active" flag is also True)
                until it reaches the final value provided in "stiffness" (default: False).
            num_steps: if spring stiffness is applied incrementally, it defines the number of steps to use to apply it (default: 10).
            view_end_points: If True, springs end points are drawn in green.
            view: If True, springs will be drawn as green cylinders.
        """

        super().__init__(self)

        self.start_indices 	= start_indices
        self.end_points 	= end_points
        self.node_name 	  	= name		
        self.stiffness 	 	= stiffness
        self.rest_length 	= rest_length
        self.active 		= active
        self.incremental 	= incremental
        self.num_steps 		= num_steps
        self.view_end_pts 	= view_end_points

        # Initialize spring list and related arrays
        self.stiff_springs = []
        self.ssff_start_id = np.asarray(self.start_indices, dtype=int)
        self.ssff_end_id   = np.arange(len(self.end_points), dtype=int)
        self.ssff_k  	   = self.active * self.__init_array(self.stiffness, len(self.start_indices))
        self.ssff_kd 	   = np.zeros_like(self.ssff_start_id)
        self.ssff_l 	   = self.__init_array(self.rest_length, len(self.start_indices))

        self.__is_inactive = True
        self.dissect_ids = []
        
        if attached_object is None:
            parent_node_state_link = '@../'
        else:
            parent_node_state_link = attached_object.state.getLinkPath()

        if not self.incremental:
            self.num_steps = 1.0
        else:
            self.delta_k = np.asarray(self.stiffness) / self.num_steps
            if isinstance(self.delta_k, float):
                self.delta_k = self.delta_k * np.ones((len(self.start_indices),))
        
        assert len(self.start_indices) == len(self.end_points), "Number of start_indices must be the same as number of end_points."

        # --------------------------------------------------#
        # Scene graph creation
        # --------------------------------------------------#

        # Create components
        self.node = parent_node.addChild( self.node_name )
        if view:
            self.node.addObject('VisualStyle', displayFlags='showInteractionForceFields')

        if not isinstance(self.end_points, list):
            self.end_points = self.end_points.tolist()
            
        self.end_points_state = self.node.addObject('MechanicalObject', name='end_points', position=self.end_points, showObject=False)
        self.node.addObject('FixedConstraint', indices=np.arange(len(self.end_points)))
        if self.view_end_pts:
            self.__visualize_end_pts()

        # Create one stiff spring per point
        for i in range(len(self.end_points)):
            ss = self.node.addObject("StiffSpringForceField", 
                                name="Spring"+str(i),
                                stiffness = self.ssff_k[i],
                                #length 	  = self.ssff_l[i],
                                lengths   = [self.ssff_l[i]],
                                damping   = self.ssff_kd[i],
                                object1   = parent_node_state_link, 
                                object2   = "@end_points", 
                                indices1  = self.ssff_start_id[i],
                                indices2  = self.ssff_end_id[i],
                                listening = 1,
                                drawMode  = 1,
                                showArrowSize = int(view)*0.0002 )
            self.stiff_springs.append(ss)
        
        #print('Number of spring attachments created:', len(self.stiff_springs))

        #print("SPRING BOUNDARIES")
        #for a in dir( self ):
        #    print("\t", a, getattr(self, a), type(getattr(self,a)))
        #for a in vars( self ):
        #    print("\t", a, getattr(self, a), type(getattr(self,a)))

    def onAnimateEndEvent(self,dt):
        # If the component is active
        if self.active:
            # If springs needs to be incremented
            if self.incremental:
                self.__increment_stiffness()
                if self.ssff_k[0] >= (self.delta_k[0]*self.num_steps - 1e-05): 
                    #print('STOP incrementing spring stiffness')
                    self.incremental = False
                    self.__is_inactive = False
            elif self.__is_inactive:
                self.ssff_k = self.__init_array(self.stiffness, len(self.start_indices))
                self.__populate_springs()
                self.__is_inactive = False
            
    def update_rest_length(self, pos1, pos2):
        assert len(pos1) == len(pos2), "The two lists must have the same dimension"
        assert len(pos1) == len(self.ssff_l), "Provided positions and rest length must have the same dimension"
        pos1 = np.asarray(pos1)
        pos2 = np.asarray(pos2)
        rest_length = np.linalg.norm((pos2 - pos1), axis=1).tolist()

        #print('Updating springs rest length from provided positions')
        self.ssff_l = rest_length
        self.__populate_springs()


    #########################################################
    ####### CUSTOM - private
    #########################################################
    def __init_array(self, in_data, out_length):
        if isinstance(in_data, float) or isinstance(in_data, int):
            out_array = in_data * np.ones((out_length))
        else:
            out_array = np.asarray(in_data)
        return out_array

    def __increment_stiffness(self):
        self.ssff_k += self.delta_k
        self.__populate_springs()
    
    def __populate_springs(self):
        for i, ss in enumerate(self.stiff_springs):
            ss.stiffness.value = self.ssff_k[i]
            ss.damping.value   = self.ssff_kd[i]
            #ss.d_length.value    = self.ssff_l[i]
            ss.lengths.value    = [self.ssff_l[i]]
            ss.reinit()

    def __visualize_end_pts(self, scale=10, color=[0,1,0,1] ):
        self.end_points_state.showObject=1
        self.end_points_state.showObjectScale=scale
        self.end_points_state.showColor=color		


