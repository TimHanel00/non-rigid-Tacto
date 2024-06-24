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
from typing import List

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
        organs: List[bpy.types.Object],
        obj_name: str,
        outset_amplitude: float = 0.05,
        outset_frequency: float = 5
    ) -> bpy.types.Object:
    """ Create a hull around the given objects
    
    Args:
        organs: All organs which should end up inside the hull
        obj_name: Name of created object
        outset_amplitude: Maximum distance along normal (set to 0 to disable)
        outset_frequency: Frequency to use for the outset noise
    """
    
    obj = blenderutils.new_empty_object(obj_name)
    
    # Merge all input vertices into one object:
    bm = bmesh.new()
    for o in organs:
        for v in o.data.vertices:
            bm.verts.new( v.co )
    
    # Create the convex hull for all these vertices:
    res = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    bmesh.ops.delete(bm,
        geom=list(set(res["geom_unused"] + res["geom_interior"])),
        context='VERTS')
    
#    # Put data into object:    
    bm.to_mesh( obj.data )
    bm.free()
    
    # Remesh the result:
    mod = obj.modifiers.new("Remesh", type='REMESH')
    mod.mode = "SMOOTH"
    mod.octree_depth = 4
    mod.scale = 0.85
    mod.use_remove_disconnected = True
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='Remesh')
    
    # Outset all vertices along their (outward-pointing) normal:
    bm = bmesh.new()
    bm.from_mesh( obj.data )
    if outset_amplitude > 0:
        for v in bm.verts:
            n = mathutils.noise.noise( v.co*outset_frequency,
                    noise_basis="PERLIN_NEW" )
            n = abs(n)
            v.co = v.co + v.normal*outset_amplitude*n
    
    bm.to_mesh( obj.data )
    
    return obj

if __name__ == "__main__":
    
    internal_organs = bpy.context.selected_objects
    
    create( internal_organs, obj_name="hull" )
