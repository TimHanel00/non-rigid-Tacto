import bpy
import os
import sys
import bmesh
import importlib
import mathutils

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


def fill_with_fat(container, inner, up_vector, amount, obj_name="fat", resolution=30,
        noise_frequency=10, noise_amplitude=0.02):
    """ Fill the "container" object with fat
    
    Fills the container with fat, but only until "amount" of the "inner" object is covered.
    While creating the fat object, the lower part of the "inner" object will be covered in
    fat, increasing in the direction of the "up_vector", i.e. those parts of the "inner"
    object which are further along the "up_vector" will be left unconvered.
    """
    
    first_vert = blenderutils.first_vert_pos_along_axis(inner, up_vector)
    last_vert = blenderutils.first_vert_pos_along_axis(inner, -up_vector)
    
    fat_pos = first_vert + amount*(last_vert-first_vert)
    
    # Size of the plane to create which shoul definitely span the entire container:
    diag = container.dimensions.length
    size = diag*1.1
    
    # Find a rotation which rotates the (0,0,1) vector to "up_vector":
    up_vector = up_vector.normalized()
    if up_vector == mathutils.Vector((0,0,1)):
        rotation = mathutils.Quaternion()
    else:
        Z = mathutils.Vector((0,0,1))
        ang = up_vector.angle( Z )
        axis = up_vector.cross( Z )
        rotation = mathutils.Quaternion( axis, ang )
    
    # Create a grid, centered at the calculated position, facing the given "up" vector
    # This will be the "upper" side of the fat, i.e. the region usually facing the camera
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=resolution,
        y_subdivisions=resolution,
        size = size,
        location = fat_pos,
        rotation = rotation.to_euler("XYZ")
    )
    fat = bpy.context.object
    fat.name = obj_name
    
    # Take every vertex and perturb it according to the noise function:
    local_up_vector = fat.matrix_world.inverted() @ up_vector
    for v in fat.data.vertices:
        noise = mathutils.noise.noise( v.co*noise_frequency )
        c = v.co + local_up_vector*noise*noise_amplitude
        v.co = c
    
    # Turn into bmesh for easier manipulation:
    bm = bmesh.new()
    bm.from_mesh( fat.data )
    
    # Extrude the faces:
    extruded = bmesh.ops.extrude_face_region(bm, geom=bm.faces)
    extruded_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=-local_up_vector*size, verts=extruded_verts)
    
    # Flip normals:
    bmesh.ops.recalc_face_normals( bm, faces=bm.faces )
    
    # Write data back to original object:
    bm.to_mesh( fat.data )
    bm.free()
    
    mod_outer = fat.modifiers.new(type="BOOLEAN", name="bool_outer")
    mod_outer.object = container
    mod_outer.operation = 'INTERSECT'
    try:
        mod_outer.solver = "EXACT"
    except AttributeError as e:
        print("Warning: BOOLEAN modifier could not be set to 'EXACT'. Consider using a newer Blender version.")
    try:
        mod_outer.use_hole_tolerant = True
    except AttributeError as e:
        print("Warning: BOOLEAN modifier missing 'use_hole_tolerant' setting. Consider using a newer Blender version.")
    try:
        mod_outer.use_self = True
    except AttributeError as e:
        print("Warning: BOOLEAN modifier missing 'use_self' setting. Consider using a newer Blender version.")
    
    mod_inner = fat.modifiers.new(type="BOOLEAN", name="bool_inner")
    mod_inner.object = inner
    mod_inner.operation = 'DIFFERENCE'
    try:
        mod_outer.solver = "EXACT"
    except AttributeError as e:
        print("Warning: BOOLEAN modifier could not be set to 'EXACT'. Consider using a newer Blender version.")
    try:
        mod_outer.use_hole_tolerant = True
    except AttributeError as e:
        print("Warning: BOOLEAN modifier missing 'use_hole_tolerant' setting. Consider using a newer Blender version.")
    try:
        mod_outer.use_self = True
    except AttributeError as e:
        print("Warning: BOOLEAN modifier missing 'use_self' setting. Consider using a newer Blender version.")
    
    
    bpy.ops.object.modifier_apply(modifier="bool_outer")
    bpy.ops.object.modifier_apply(modifier="bool_inner")

    
    return fat
