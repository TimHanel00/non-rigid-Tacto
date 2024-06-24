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

def create(
        rnd: random.Random = random.Random(),
        bounds: blenderutils.BoundingBox =blenderutils.BoundingBox(0.3),
        add_concavity: bool = True,
        name: str = "RandomMesh",
        predeform_twist: bool = False,
        predeform_noise: bool = False,
        cut_to_fit: bool = False,
        extrusion_size: float = 0.5,
        containing_obj: bpy.types.Object = None,
        target_minimum_voxel_size: float = 0.02,
        clean_method: str = "VOXEL" ):
    """ Creates a random organic-looking object. Usually used to simulate organ or tumor shape.
    
    Arguments:
        rnd: Random number generator to use (for determinism)
        bounds: Maximum extensions on each axis. Important: These are grid-aligned, i.e.
            supplying a bounding box of size (0.1, 0.3, 0.1) will create a shape that is around
            3 times longer along the y-axis than it is on the x- and z- axis.
            Be careful not to introduce bias into the data (for example by rotating the shapes
            randomly after creating them).
        add_concavity: Whether or not to subtract another random shape from this shape during
            generation. This tends to add concavities into the final shape, but note that
            this is a random process: Setting add_concavity does not guarantee that there is
            any large concavity in the final shape (because the subtrahend shape is randomly
            placed).
        name: The name given to the created object.
        predeform_twist: Add a twisting deformation to the mesh to increase shape diversity.
            Uses the blender "Simple Deform" modifier.
        predeform_twist: Add noise to the mesh vertices. Uses blender's "Displace" modifier.
        cut_to_fit: To ensure the final mesh fits into the given bounds, cut pieces which
            extend beyond the bounding box off. Useful for very thin meshes, for example.
            If this is False, will scale the mesh to fit the bounds instead.
        extrusion_size: Size of the extrusions which are performed to create the initial shape.
            This is a factor of the largest dimension in "bounds". So if bounds has a size of
            (3,1,2), and extrusion_size is 0.5, then the extrusion distance would be 3*0.5 = 1.5.
        containing_obj: If given, the newely generated object will be moved _inside_ the
            containing_obj. For this to work, containing_obj should be watertight. Note: We
            currently only ensure that the _center_ of the new object lies within the
            containing_obj (its sides may pertrude outside the containing_obj). This is used
            for tumors (which may lie on the surface of the organ and may thus be visible.
            Default: None
        clean_method: VOXEL or SMOOTH. Method to use for the final cleaning step. Internally,
            this will use a remesh filter. VOXEL may give more regular, "meshable" results, but
            may fail for small regions/meshes. Current recommendation: Use "VOXEL" for large meshes
            which need to be 3D meshed afterwards using Gmsh or similar and use "SMOOTH" for smaller,
            tumor-like meshes.
    """
    print("RND ORGAN:", rnd, bounds, add_concavity, name, predeform_twist, predeform_noise, cut_to_fit, extrusion_size, containing_obj,target_minimum_voxel_size )
    try:
        
        # Go to object mode if possible:
        blenderutils.set_mode("OBJECT")

        # Clear previous meshes:
#        for o in bpy.data.objects:
#            o.select_set(False)
#        for o in bpy.data.objects:
#            if "RandomMesh" in o.name:
#                o.select_set(True)
#        bpy.ops.object.delete()
        
        scene = bpy.context.scene
        
        # Create an empty mesh and the object.
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Add the object into the scene.
        bpy.context.collection.objects.link( obj )
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        largest_dim = max(bounds.dimensions)
        smallest_dim = min(bounds.dimensions)

        # Construct the bmesh sphere and assign it to the blender mesh.
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=rnd.uniform(smallest_dim*0.5,largest_dim*0.5))
        bm.to_mesh(mesh)
        

        # Extrude the mesh a random number of times:
        extrusions = rnd.randint(2,6)
        bm.faces.ensure_lookup_table()
        
        blenderutils.set_mode("EDIT")
        for i in range( 0, extrusions ):
            
            for v in bm.verts:
                v.select_set(False)
            bm.select_flush(False)
            bm.faces.ensure_lookup_table()
            #id = rnd.randint(0, len(bm.faces)-1)
            #face = bm.faces[id]
            face = blenderutils.get_random_face(bm, rnd)

            face.select_set(True)
            
            ntimes = rnd.randint(1,2)
            blenderutils.select_more(bm, ntimes=ntimes)
            
            # Randomly scale the selected face:
            #random_scale( bm, i, extrusions, face.verts, rnd )
            
            #bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 0.05), "constraint_axis":(False, False, True), "constraint_orientation":'NORMAL', "mirror":False, "proportional":'DISABLED', "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False})
            #bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0.05,0,0)})
            selection = [f for f in bm.faces if f.select]
            extruded = bmesh.ops.extrude_face_region(bm, geom=selection)
            vec = -face.normal*largest_dim*extrusion_size
            bmesh.ops.delete(bm, geom=selection, context="FACES") # Delete previous faces
            verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]
            faces = [f for f in extruded['geom'] if isinstance(f, bmesh.types.BMFace)]
            #vec = mathutils.Vector((0.05, 0, 0))
            bmesh.ops.translate(bm, vec=vec, verts=verts)
        
        # Re-sort mesh to ensure determinism:
        bm = blenderutils.resort_mesh( bm )
            
        blenderutils.set_mode("OBJECT")
        bm.to_mesh(obj.data)
        bm.free()
        
        
        # Randomly rotate the object:
        blenderutils.set_mode("OBJECT")
        eul = mathutils.Euler((rnd.uniform(0,2*math.pi),rnd.uniform(0,2*math.pi),rnd.uniform(0,2*math.pi)), 'XYZ')
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = eul.to_quaternion()
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        obj.rotation_euler = eul
        
        
        # Before adding cncavity or twists etc., clean the mesh:
        blenderutils.clean_mesh(obj, rnd=rnd, remesh_mode="SMOOTH")
        
        #########################################################
        ## Optionally cut out a piece of the mesh to generate more interesting shapes.
        ## This is done via a boolean modifier which intersects the mesh with a
        ## rotated and translated copy of itself:
        if add_concavity:
            # Duplicate object:
            duplicated = blenderutils.duplicate( obj, "RandomMeshCopy" )
            
            vec = mathutils.Vector((0,0,0))
            while vec.length < bounds.max_val*0.3:
                x = rnd.uniform(-bounds.max_val*0.75, bounds.max_val*0.75)
                y = rnd.uniform(-bounds.max_val*0.75, bounds.max_val*0.75)
                z = rnd.uniform(-bounds.max_val*0.75, bounds.max_val*0.75)
                vec = mathutils.Vector((x,y,z))
            duplicated.location = vec
            x=rnd.uniform(-math.pi,math.pi)
            y=rnd.uniform(-math.pi,math.pi)
            z=rnd.uniform(-math.pi,math.pi)
            duplicated.rotation_euler = (x,y,z)
        
            #scene.update()
            bpy.context.view_layer.update()
            
            # Subtract the duplicate from this object:
            boolModifier = obj.modifiers.new(type="BOOLEAN", name="bool")
            boolModifier.object = duplicated
            boolModifier.operation = "DIFFERENCE"
            bpy.ops.object.modifier_apply(modifier="bool")
            
            # Remove duplicate again:
            blenderutils.delete_obj( duplicated )
            
        # Sometimes, the previous steps resulted in an empty mesh.
        # This should be highly unlikely now, but just in case, we'll check
        # here.
        if min( obj.dimensions ) < 1e-10:
            raise ValueError("Random mesh generation resulted in empty mesh, aborting.")
            
        #########################################################
        ## Bring object down to the final required dimesion.
        ## Either by scaling or by boolean operation with the bounding box:
        if cut_to_fit:
            # Create a cube the size of the mesh:
            bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
            bpy.ops.mesh.primitive_cube_add()
            box = bpy.context.view_layer.objects.active
            box.scale = [tgt/cur for cur, tgt in zip(box.dimensions, bounds.dimensions)]
            box.name = "bounds"
            box.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
            # Scale object so that minimums dimension fits into bounds:
            #scale_factors = [dim_target/dim_cur for dim_cur, dim_target in zip(obj.dimensions, bounds.dimensions)]
            #max_scale_factor = max(scale_factors)
            #obj.scale = (max_scale_factor,max_scale_factor,max_scale_factor)
            
            # Scale object so that one dimension fits into bounds:
            scale_factors = [dim_target/dim_cur for dim_cur, dim_target in zip(obj.dimensions, bounds.dimensions)]
            scale_factor = sorted(scale_factors)[1]    # median
            scale_factor *= rnd.uniform(0.8,1.1)
            obj.scale = (scale_factor,scale_factor,scale_factor)
            
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
            # Keep only the intersection of the mesh and the bounds-box:
            boolModifier = obj.modifiers.new(type="BOOLEAN", name="bool")
            boolModifier.object = box
            boolModifier.operation = "INTERSECT"
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier="bool")
            
            blenderutils.delete_obj(box)
        else:
            # Scale object down if necessary:
            
            assert min(obj.dimensions) > 0, "Mesh empty. Aborting."
            
            scale_factors = [dim_max/dim_cur for dim_cur, dim_max in zip(obj.dimensions, bounds.dimensions)]
            obj.scale = scale_factors
            
            # Move the object (and the curve) to fit into a predefined bounding box:
            local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
            origOffset = -local_bbox_center     # Offset to move object into world origin
            obj.location = origOffset

            # Offset to randomly place object inside bounding box:
            maxOffset = (mathutils.Vector(bounds.dimensions) - obj.dimensions)*0.5
            randOffset = mathutils.Vector(( rnd.uniform(-maxOffset.x,maxOffset.x),
                                rnd.uniform(-maxOffset.y,maxOffset.y),
                                rnd.uniform(-maxOffset.z,maxOffset.z) ))
            obj.location += randOffset
            
            #########################################################
            ## Apply scale:
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        #########################################################
        ## Pre-deform:
        
        # Important: I don't know why, but this duplicate must be done
        # before applying the following modifiers, otherwise the modifiers will weirdly
        # also affect the other objects...?
        prev_obj = obj
        obj = blenderutils.duplicate( obj, obj.name )
        # Set active:
        bpy.context.view_layer.objects.active = obj
        
        blenderutils.delete_obj( prev_obj )

 
        ################
        ## DEBUG SAVE FILE:
       
        #fp = os.path.join( "/home/pfeiffemi", "scene_setup.blend" )
        #print("save:", fp)
        #bpy.ops.wm.save_as_mainfile( filepath = fp )


    
        #########################################################
        ## Cleanup:



        # TODO: Gmsh and the whole simulation seem to be relatively vulnverable to changes in the
        # target_minimum_voxel_size, and how remeshing or subdivision is performed. It would be really
        # good to get some more solid background on what values to use, i.e. what does the input mesh
        # need to look like in order for Gmsh to not fail and Sofa to converge in a reasonable time...?
        if clean_method == "VOXEL":
            smallest_dim = min(obj.dimensions)
            target_minimum_voxel_size = min(smallest_dim*0.1, target_minimum_voxel_size)
            blenderutils.clean_mesh( obj, rnd=rnd,
                    remesh_mode = "VOXEL",
                    target_minimum_voxel_size = target_minimum_voxel_size,
                    subdiv = False )

        else:
            blenderutils.clean_mesh( obj, rnd=rnd,
                    remesh_mode = "SMOOTH",
                    subdiv = False )
                #subdiv = False )
 
        obj = blenderutils.remove_non_manifolds(obj)
  
        blenderutils.set_mode("OBJECT")

        #########################################################
        ## Simple deformation to generate more interesting shapes:
    
        if predeform_twist:
            # Create an empty object to use as twisting origin:
            empty = blenderutils.new_empty_object("Empty")
            empty.location = mathutils.Vector(
                            (rnd.random()-0.5
                            , rnd.random()-0.5, rnd.random()-0.5)
                        )*largest_dim
            
            blenderutils.set_mode("OBJECT")
            twist_deform = obj.modifiers.new(type="SIMPLE_DEFORM", name="twist")
            twist_deform.deform_method = 'TWIST'
            twist_deform.origin = empty
            twist_deform.angle = rnd.uniform(-math.pi/3., math.pi/3.)
            bpy.ops.object.modifier_apply(modifier="twist")

            blenderutils.delete_obj(empty)

#            bend_deform = obj.modifiers.new(type="SIMPLE_DEFORM", name="bend")
#            bend_deform.deform_method = 'BEND'
#            bend_deform.angle = rnd.uniform(-math.pi/4., math.pi/4.)
#            print("bend_deform angle:", bend_deform.angle)
#            bpy.ops.object.modifier_apply(modifier="bend")
        
        if predeform_noise:
            
            blenderutils.set_mode("OBJECT")
            
            displace = obj.modifiers.new(type="DISPLACE", name="displace")
            freq =  rnd.uniform(0.001, 0.2)
            max_strength = min(smallest_dim*0.25, 0.02)
            displace.texture = blenderutils.create_noise_texture( freq = freq )
            displace.strength = rnd.uniform( 0, max_strength )

            bpy.context.view_layer.objects.active = obj
            bpy.context.view_layer.update()
            obj.select_set(True)
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
                with bpy.context.temp_override(active_object=obj):
                    bpy.ops.object.modifier_apply(modifier="displace")
                print("Displace modifier applied successfully.")
            except RuntimeError as e:
                print(f"RuntimeError: {e}")
                    # Apply the modifier
            #try:
                #bpy.ops.object.modifier_apply(modifier="displace")
                #print("Displace modifier applied successfully.")
            #except RuntimeError as e:
                #print(f"RuntimeError: {e}")  
        
        
        ############################################################
        ## Optionally, move the generated object so that it's center point
        ## lies inside another, given object. Used for tumors.
        ## Note that this only adjusts the center point, so the side of the tumor
        ## may protrude outside the ogran surface!
        if containing_obj is not None:
            pos = blenderutils.random_point_within_mesh( containing_obj, rnd=rnd )
            center = blenderutils.get_center_point( obj )
            diff = pos - center
            obj.location += diff
            
        
        # Remove all but the wanted object:
#        for o in bpy.data.objects:
#            o.select_set(True)
#            if "RandomMesh" in o.name and not "RandomMeshCopy" in o.name:
#                o.select_set(False)

        #fp = os.path.join( "/home/pfeiffemi", "scene_setup.blend" )
        #print("save:", fp)
        #bpy.ops.wm.save_as_mainfile( filepath = fp )

        # Re-sort mesh to ensure determinism:
        bm = bmesh.new()
        bm.from_mesh( obj.data )
        bm = blenderutils.resort_mesh( bm )
        bm.to_mesh( obj.data )

        return obj

    except:
        print( "Could not generate model." )
        print( "Unexpected error:", sys.exc_info()[0] )
        print( traceback.format_exc() )
        
        # Note: This closes blender, which is annoying during debugging, but currently the safest
        # option for usage of this script in the pipeline (because everything else is aborted this way,
        # avoiding calculation of invalid things)
        # A better way might be to raise an error (because that can optionally be caught when
        # debugging things)
        exit(1)
        
    return None

#bpy.ops.wm.quit_blender()

if __name__ == "__main__":
    
    # Remove all arguments passed to Blender, only take those after the double dash '--' into account:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Generate a random mesh using Blender functionality.")
    parser.add_argument("--outdir", type=str, default=".", help="Folder in which to save the random mesh.")
    parser.add_argument("--filename", type=str, default="surface.obj", help="Name of output file to generate. Must be .stl or .obj!")
    parser.add_argument("--bounds", type=float, default=0.3, help="Edge of the cube defining the volume where the object must lie.")
    parser.add_argument("--random_seed", type=int, default=1)
    args = parser.parse_args(argv)
    
    rnd = random.Random()
    rnd.seed(args.random_seed)

    blenderutils.clear_scene()
    
    obj = create(rnd, blenderutils.BoundingBox(args.bounds))
    
    blenderutils.export(obj, outdir=args.outdir, filename=args.filename)


