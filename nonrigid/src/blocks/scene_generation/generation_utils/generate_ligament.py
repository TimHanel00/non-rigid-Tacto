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

def connect(source_obj, target_obj, rnd=random.Random(), obj_name="Ligament"):
    
    source_bm = bmesh.new()
    source_bm.from_mesh(source_obj.data)
    source_bm.verts.ensure_lookup_table()
    
    target_bm = bmesh.new()
    target_bm.from_mesh(target_obj.data)
    target_bm.verts.ensure_lookup_table()
    
    ligamnet_verts = []
    
    source_vert_ids = blenderutils.select_surface_path(
            surface_bm = source_bm, rnd=rnd )
    source_verts = [source_bm.verts[id] for id in source_vert_ids]
    
    ligament_connections = []
    target_bm.faces.ensure_lookup_table()
    search_tree = mathutils.bvhtree.BVHTree.FromBMesh(
            target_bm )
    # Cast rays from source verts to the target mesh to see
    # where we should connect the ligament:
    for sv in source_verts:
        loc, _, face_ind, dist = search_tree.ray_cast(
                sv.co, sv.normal )
        if loc is not None:
            # Find the vertex of the hit face which is closest
            # to the hit location:
            hit_face = target_bm.faces[face_ind]
            # Calc dists for all:
            dists = [(v.co-loc).length for v in hit_face.verts]
            # Get index of vert with smalles dist:
            index_min = min(range(len(dists)), key=dists.__getitem__)
            # get vert:
            closest_vert = hit_face.verts[index_min]
            ligament_connections.append(
                    (sv, closest_vert) )
            
    ligament_bm = bmesh.new()
    for connectins in ligament_connections:
        v0 = ligament_bm.verts.new( connectins[0].co )
        v1 = ligament_bm.verts.new( connectins[1].co )
        ligament_bm.edges.new( (v0, v1) )
    
    ligament_obj = blenderutils.new_empty_object(name=obj_name)
    ligament_bm.to_mesh(ligament_obj.data)
    
    return ligament_obj
