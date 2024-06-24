import random
import os
import sys
import importlib
import mathutils
import re
import math
import yaml
import bpy

try:    # Wrap this in try block so that documentation can be built without bpy.data
    d = os.path.dirname(bpy.data.filepath)
    sys.path.append(d)
    sys.path.append(os.path.join(d, "..", "src", "utils"))
    sys.path.append(os.path.join(d, "..", "..", "utils"))
    sys.path.append(os.path.join(d, "src", "utils"))
except Exception as e:
    print(e)
    print("WARNING: Could not add blender paths. Make sure you're running this from" +\
        " within blender!")

print("directory", os.path.dirname(bpy.data.filepath))
print(sys.path)
d2 = os.getcwd()
sys.path.append(os.path.join(d2, "src", "blocks", "rendering"))

import blenderutils
import renderutils
import camera

importlib.reload(blenderutils)
importlib.reload(renderutils)
importlib.reload(camera)

#def find_matching_files( path, filename ):
#    base_name, ext = os.path.splitext( filename )
#    print("Search:", filename, "in", path)
#    
#    file_pattern = f"{base_name}(_[A-Z])*(_f[0-9]+)*\\{ext}"
#    print("Pattern:", file_pattern)
#    
#    # Get all file names in the sample's folder:
#    all_filenames = os.listdir(path)
#    # Sort the files alphabetically:
#    all_filenames = sorted(all_filenames)
#    
#    #print("matchijng against:", all_filenames)

#    matches = []
#    for name in all_filenames:
#        # Todo: consider using re.fullmatch
#        if re.match(file_pattern, name):
#            matches.append( name )

#    return matches

def load_from_source(
        path: str,
        filename: str,
        overlay: bool = False,
        subcollection_name: str = None ):
    """
    """
    full_filename = os.path.join( path, filename )
    print("loading:", full_filename)
    if not os.path.exists( full_filename ):
        return None
    obj = blenderutils.import_mesh( full_filename )
    obj.name = filename
    
   
    if overlay:
        parent_collection = bpy.data.collections["Overlay Collection"]
        #parent_collection = bpy.data.collections.new("Overlay Collection")
        # Link new collection into the scene:
        #bpy.context.scene.collection.link( parent_collection )
    else:
        parent_collection = bpy.data.collections["Organ Collection"]
        #parent_collection = bpy.data.collections.new("Organ Collection")
        # Link new collection into the scene:
        #bpy.context.scene.collection.link( parent_collection )

    # Use an optional sub-collection (to group meshes from the same organ)
    if subcollection_name:
        if subcollection_name in parent_collection.children.keys():
            collection = parent_collection.children[ subcollection_name ]
        else:
            collection = bpy.data.collections.new( subcollection_name )
            # Link new collection into the scene:
            parent_collection.children.link( collection )
    else:
        collection = parent_collection

    # Remove from all previous collections:
    for c in obj.users_collection:
        c.objects.unlink(obj)
    # Add to correct collection:
    print(f"Adding {obj.name} to collection {collection.name}")
    collection.objects.link( obj )

    # Shade smooth:
    blenderutils.shade_smooth( obj )
    mod = obj.modifiers.new( "EdgeSplit", "EDGE_SPLIT" )
    mod.split_angle = 60/180*math.pi # 30 degrees
    mod.use_edge_sharp = False      # Note: This is a workaround for all edges being marked as sharp for some reason...
    
    return obj

def animate_visibility( obj, frame_start, frame_end ):
    """ Animate the visibility property of an object
    
    After this call, the object will only be visible from frame_start to frame_end (TODO: -1?)
    """
    #return  # DEBUG
    print("Show from to:", obj.name, frame_start, frame_end)
   
    if frame_start:
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=frame_start-1)
        obj.hide_viewport = True
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_start-1)
        
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_render", frame=frame_start)
        obj.hide_viewport = False
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_start)

    if frame_end:
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_render", frame=frame_end-1)
        obj.hide_viewport = False
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_end-1)
        
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=frame_end)
        obj.hide_viewport = True
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_end)


def load_scene_object( folder_path, object_arguments, unique_materials, compositing ):
    
    frame_start = object_arguments["frame_start"] if "frame_start" in object_arguments.keys() else None
    frame_end = object_arguments["frame_end"] if "frame_end" in object_arguments.keys() else None
    
    loaded_objects = []
    loaded_objects_meta = []
 
    base_name, extension = os.path.splitext( object_arguments["filepattern"] )
    if frame_start is None or frame_end is None:
        filename = object_arguments["filepattern"]
        
        obj = load_from_source( folder_path, filename, subcollection_name = base_name )
        if obj:
            obj_meta = {    # Also save info on when this object should be visible:
                    "obj":obj,
                    "frame_start":frame_start,
                    "frame_end":frame_end
                    }
            loaded_objects.append( obj)
            loaded_objects_meta.append( obj_meta )
    else:
        for frame in range(frame_start, frame_end):
            filename = f"{base_name}_f{frame}{extension}"
            try:
                obj = load_from_source( folder_path, filename, subcollection_name = base_name )
                if obj:
                    #animate_visibility( obj, frame, frame+1 )

                    obj_meta = {    # Also save info on when this object should be visible:
                        "obj":obj,
                        "frame_start":frame,
                        "frame_end":frame+1
                        }
                    loaded_objects.append( obj)
                    loaded_objects_meta.append( obj_meta )
                else:
                    print(f"Could not find object {filename} for frame {frame}, skipping")
            except:
                print(f"Could not find object {filename} for frame {frame}, skipping")
    
    
    unique_materials.new_material( loaded_objects, object_arguments["color"],
            material_name = object_arguments["filepattern"] )
            
    overlay = False
    if "render_late" in object_arguments.keys() and object_arguments["render_late"] == True:
        overlay = True
            
    for obj in loaded_objects:
        # Set up compositioning for the object:
        compositing.setup_object_mask( obj,
            color = object_arguments["color"],
            overlay = overlay )
        obj["is_overlay"] = overlay
        
#    matches = find_all_matching_files( folder_path, full_filepattern )
#    #for m in matches:
#    if len(matches) < 1:
#        raise IOError( f"Could not find any mesh matching '{args.object_of_interest['filepattern']}'!" )
#    # For now, only load the last matching mesh:
#    target_obj = load_from_source( args.outdir, matches[-1] )
#    all_objects.append( target_obj )
#    # Apply the color:
#    unique_materials.new_material( target_obj, object_arguments["color"] )
#    
#    
#     #####################
#    filepattern = other_object["filepattern"]
#    print("searching for:", filepattern)
#    matches = find_matching_files( args.outdir, filepattern )
#    if len(matches) < 1:
#        raise IOError( f"Could not find any mesh matching '{filepattern}'!" )
#    print("matches:", matches)
#    
#    overlay = False
#    if "render_late" in object_arguments.keys() and object_arguments["render_late"] == True:
#        overlay = True
#    
#    # For now, only load the last matching mesh:
#    obj = load_from_source( args.outdir, matches[-1], overlay = overlay )
#    all_objects.append( obj )
#    
#    unique_materials.new_material( obj, other_object["color"] )


    return loaded_objects_meta

def setup_and_render_scene( args ):
    
    rnd = random.Random( args.random_seed )
    
    blenderutils.clear_scene()
    all_objects = []
    
    # Set up render layers:
    compositing = renderutils.CompositingSetup( outdir = args.outdir )
    
    # DEBUG:
    #args.outdir = os.path.abspath("./Projects/Deformation/nonrigid-data-generation-pipeline/test_data/000001")
    
    unique_materials = blenderutils.MaterialFactory( unique_colors = True )
     
    
    
    ###########################################
    ## Set up compositioning. This sets up the rendering in such a way that the different
    ## meshes end up in the correct images
    
    # Clear everything in the compositing tree
    compositing.setup_composition_nodes()
    
    
    ###########################################
    ## Load the target mesh (the object of onterest):
    target_objects_meta = load_scene_object( args.outdir, args.object_of_interest, unique_materials, compositing )
    all_objects += target_objects_meta
    target_objects = [o["obj"] for o in target_objects_meta]

    ###########################################
    ## Set up a camera that we can animate later on:
    cam = camera.Camera( target_objects )
    obj_meta = {    # Also save info on when this object should be visible:
            "obj":cam.cam,
            "frame_start":None,
            "frame_end":None
            }
    all_objects.append( obj_meta )
    
    ###########################################
    ## Load surrounding organs:
    # Debug:
#    if args.other_object == None:
#        args.other_object = [
#            {"filepattern":"abdominal_wall_A.stl", "color":(0.5,0.2,0.1,1)},
#            {"filepattern":"abdominal_wall_fat_A.stl", "color":(0.8,0.8,0.2,1)},
#            {"filepattern":"attached_organ_A.stl", "color":(0.5,0.4,0.2,1)},
#            {"filepattern":"attached_organ_B.stl", "color":(0.5,0.4,0.2,1)}
#            ]

            
    if args.other_object != None:
        for other_object in args.other_object:
            objs = load_scene_object( args.outdir, other_object, unique_materials, compositing )
            all_objects += objs
    
    compositing.combine()
                    
    ## Update all view layers (important for ray casts):
    for layer in bpy.context.scene.view_layers:
        layer.update()
    
    ################
    ## DEBUG SAVE FILE:
    
    #print("save:", os.path.join( os.path.dirname(bpy.data.filepath),args.outdir, "render_setup.blend") )
    #bpy.ops.wm.save_as_mainfile(filepath=os.path.join( os.path.dirname(bpy.data.filepath),args.outdir, "render_setup.blend"))

   
    
    ############################################
    # Generate the view points and camera path:
    
    abdominal_wall = None
    for obj in bpy.context.collection.all_objects:
        if "abdominal_wall" in obj.name.lower() and not ("fat" in obj.name.lower()):
            abdominal_wall = obj
            break
    
    # This function performs a simple check of whether a position lies inside the abdominal
    # wall (if present) and not inside other objects. Note that this is only called for
    # keyframes, and the interpolation between keyframes could still move the camera through
    # tissue.
    def is_valid_camera_pose( pos, view_dir ):
        """ Given a potential camera position, check if it's within the abdominal wall"""
        
        # If there is no abdominal wall, allow only points along the positive X axis:
#        if abdominal_wall is None:
#            return pos.x > 0 and pos.x > abs(pos.y) and pos.x > abs(pos.z)
#    
#        # Discard all points outside the abdominal wall:
#        if not blenderutils.point_inside_mesh( abdominal_wall, pos ):
#            return False
#        
#        # If there is a fat mesh, also make sure the camera is not inside it:
#        if abdominal_wall_fat is not None:
#            return not blenderutils.point_inside_mesh( abdominal_wall_fat, pos )

        # Ensure the target object is still visible from this camera position:
        result, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(
                    depsgraph=bpy.context.evaluated_depsgraph_get(),
                    origin=pos,
                    direction=view_dir )

        if not (obj in target_objects):
            return False
        
        for obj in bpy.context.collection.all_objects:
            if not obj.type == "MESH":
                continue
        
            if "abdominal_wall" in obj.name.lower() and not ("fat" in obj.name.lower()):
                if not blenderutils.point_inside_mesh( obj, pos ):
                    return False
            else:
                #users = [c.name for c in obj.users_collection]
                # Only check against organs, not overlay objects:
                #if "Organ Collection" in users:
                if not hasattr( obj, "is_overlay" ) or obj["is_overlay"] == False:
                    if blenderutils.point_inside_mesh( obj, pos ):
                        return False
                
                
        return True
        
    
    cam.save_calibration( args.outdir )
    
    #print("save:", os.path.join( os.getcwd(),args.outdir, "render_setup.blend") )
    #bpy.ops.wm.save_as_mainfile(filepath=os.path.join( os.getcwd(),args.outdir, "render_setup.blend"))

    cam.animate( args.num_frames, args.num_view_points, rnd, valid_pose_check=is_valid_camera_pose )
    
    # DEBUG: Save main file:
    #print("save:", os.path.join( os.getcwd(),args.outdir, "render_setup.blend") )
    #bpy.ops.wm.save_as_mainfile(filepath=os.path.join( os.getcwd(),args.outdir, "render_setup.blend"))
    
    #####################################################
    ## Animate visibility:

    for obj_meta in all_objects:
        obj = obj_meta["obj"]
        frame_start = obj_meta["frame_start"]
        frame_end = obj_meta["frame_end"]
        animate_visibility( obj, frame_start, frame_end )

    
    #####################################################
    ## Animate and render:

    # Let animation run from 0 to num_frames.
    # Note: This is not really needed, it's just more convenient for debugging.
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = args.num_frames


    
    # Go through each individual frame, and render everything:
    #cam.render_and_save_all_frames( args.num_frames, args.outdir, valid_pose_check=is_valid_camera_pose )
    rendered_frames = 0
    for frame in range(1,args.num_frames):
        
        #print("Moving to frame:", frame)
        bpy.context.scene.frame_set( frame )
        
        # Test if the camera pose in this frame is valid
        # (It may not be due to interpolation, even if the keyframes were valid!)
#        if valid_pose_check:
#            bpy.context.view_layer.update()     # Not sure if needed
#            view_dir = self.cam.matrix_world @ mathutils.Vector((0,0,-1))
#            if not valid_pose_check( self.cam.location, view_dir ):
#                print("\tCamera pose invalid, skipping frame.")
#                continue
        
        cam.render()
        
        obj_poses = {}
        for obj_meta in all_objects:
            obj = obj_meta["obj"]
            pose = obj.matrix_world
            obj_poses[obj.name] = [list(row) for row in pose]
        filename = os.path.join( args.outdir, f"{frame:04}_poses.yaml" )
        with open(filename, 'w') as f:
            yaml.dump( obj_poses, f )
        
        rendered_frames += 1
    
    if rendered_frames == 0:
        raise ValueError( "No frames with valid camera pose found. Nothing rendered!" )
    
    print(f"Rendered {rendered_frames} valid frames.")

    if args.save_blend_file or True:
        # DEBUG: Save main file:
        print("save:", os.path.join( os.getcwd(),args.outdir, "render_setup.blend") )
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join( os.getcwd(),args.outdir, "render_setup.blend"))

if __name__ == "__main__":
    
    import argparse
    import json
    
    # Remove all arguments passed to Blender, only take those after the double dash '--' into account:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Generate a (random) camera path and render each frame.")
    parser.add_argument("--outdir", type=str, default="test_data", help="Folder in which to save the results. Also used to load existing meshes.")
    #parser.add_argument("--bounds", type=float, default=0.3, help="Edge of the cube defining the volume where the object must lie.")
    parser.add_argument("--random_seed", type=int, default=23124)
    parser.add_argument("--object_of_interest", type=json.loads, default={"filepattern":"intraop_surface.stl", "color":(0.7,0.2,0.1,1), "frame_start":0, "frame_end":15}, help="The object to focus the camera on")
    parser.add_argument("--other_object", action="append", type=json.loads, help="Other organs to render, in json format.")
    parser.add_argument("--camera_path_length", type=float, default=0.3, help="The length of the path which the camera moves along")
    # TODO: If there are multiple deformed states (i.e. we output a time-series of meshes in the simulation)
    # then the number of frames should be determined by that.
    parser.add_argument("--num_frames", type=int, default=30, help="The number of frames to render while the camera is moving")
    parser.add_argument("--num_view_points", type=int, default=3, help="The number of key viewpoints to generate")
    parser.add_argument("--save_blend_file", action="store_true", help="Save the created scene as a .blend file")
    args = parser.parse_args(argv)
    
    assert args.num_frames >= args.num_view_points, \
            f"Cannot generate more key frames ({args.num_view_points}) than total frames ({args.num_frames})!"
    
    setup_and_render_scene( args )


