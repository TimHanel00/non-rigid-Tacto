import numpy as np
from typing import Optional

from core.objects.sceneobjects import DeformableOrgan

import Sofa.Core

class NodalForce:
    
    def __init__(
        self, 
        parent_node: Sofa.Core.Node,
        magnitude: list, 
        indices: list,
        name: str = 'NodalForce',
    ) ->None: 

        force = parent_node.addObject(
                            'ConstantForceField',
                            name=name, 
                            listening=1,
                            )

        self.node = force

        self.set_forces(
            magnitude=magnitude,
            indices=indices
        )      

    
    def set_forces(
        self, 
        magnitude: list, 
        indices: list,
    ) ->None:
        
        num_indices = len(indices)
        nodal_forces = np.zeros((num_indices, 3), dtype=float)
        nodal_forces[:] = magnitude
        self.node.forces = nodal_forces.tolist()
        self.node.indices = indices
    
