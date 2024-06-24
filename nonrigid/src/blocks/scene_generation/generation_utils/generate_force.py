import bpy
import mathutils
import random
import math
import os
import sys
import bmesh
import argparse
import traceback
import importlib
from typing import Optional

try:    # Wrap this in try block so that documentation can be built without bpy.data
    d = os.path.dirname(bpy.data.filepath)
    sys.path.append(d)
    sys.path.append(os.path.join(d, "..", "src", "utils"))
    sys.path.append(os.path.join(d, "src", "utils"))
except:
    print("WARNING: Could not add blender paths. Make sure you're running this from" +\
        " within blender!")

import blenderutils

importlib.reload(blenderutils)

def create(
        source_obj: bpy.types.Object,
        obj_name: str = "Force",
        rnd: random.Random = random.Random(),
        magnitude: float = 1,
        base_on_normal: bool = False,
        ang_from_normal: Optional[float] = None
    ) -> bpy.types.Object:
    """ Create an object representing a nodal force, connected to "source_obj".
    
    Args:
        source_obj: The object to attach the force to.
        rnd: Random number generator to use
    """
    
    source_bm = bmesh.new()
    source_bm.from_mesh(source_obj.data)
    source_bm.verts.ensure_lookup_table()
    
    id = rnd.randint( 0, len(source_bm.verts) )
    source_vert = source_bm.verts[id]
    
    if base_on_normal:
        force_vec = source_vert.normal.normalized()*magnitude
        if not ang_from_normal is None:
            force_vec = blenderutils.perturb_direction(
                            force_vec,
                            -ang_from_normal,
                            ang_from_normal,
                            rnd )
    else:
        force_vec = mathutils.Vector(
            (rnd.random()*2-1, rnd.random()*2-1, rnd.random()*2-1)
        )
        force_vec = force_vec.normalized()*magnitude
            
    force_bm = bmesh.new()
    v0 = force_bm.verts.new( source_vert.co )
    v1 = force_bm.verts.new( source_vert.co + force_vec )
    force_bm.edges.new( (v0, v1) )
    
    force_obj = blenderutils.new_empty_object(name=obj_name)
    force_bm.to_mesh(force_obj.data)
    
    return force_obj
