import math
import os
import sys
import bpy
import random
import mathutils
import importlib
import shutil
import yaml
import numpy as np

try:    # Wrap this in try block so that documentation can be built without bpy.data
    d = os.path.dirname(bpy.data.filepath)
    sys.path.append(d)
    sys.path.append(os.path.join(d, "..", "src", "utils"))
    sys.path.append(os.path.join(d, "..", "..", "utils"))
    sys.path.append(os.path.join(d, "src", "utils"))
    sys.path.append(os.path.join(d, "camera_utils"))
except Exception as e:
    print(e)
    print("WARNING: Could not add blender paths. Make sure you're running this from" +\
        " within blender!")

d2 = os.getcwd()
sys.path.append(os.path.join(d2, "src", "blocks", "scene_generation", "camera_utils"))
sys.path.append(os.path.abspath(os.path.join(d2, "..", "src", "blocks", "scene_generation", "camera_utils")))

import blenderutils
import renderutils

importlib.reload(blenderutils)
importlib.reload(renderutils)

class Camera:
    
    def __init__( self, target_objs, sensor_diagonal_mm=8.47, focal_length_mm=4.62,
                img_width=1920*0.5, img_height=1080*0.5 ):
        
        self.target_obj = target_objs[0]    # TODO: Handle multiple target objects (via convex hull?)
        
        # Create camera:
        camera_data = bpy.data.cameras.new(name='Camera')
        camera_object = bpy.data.objects.new('Camera', camera_data)
        self.cam = camera_object
            
            
        # From the diagonal in mm and the image sizes in pixels, we can calcuate the
        # width and height of the sensor in mm.
        # For this, use the image width to height ratio and the Pythagorean Theorem.
        ratio = img_width/img_height
        sensor_height = math.sqrt( sensor_diagonal_mm**2/( 1 + ratio**2 ) )
        sensor_width = sensor_height * ratio
        camera_data.sensor_width = sensor_width
        camera_data.sensor_height = sensor_height
        
        camera_data.clip_start = 0.005  # 5mm
        camera_data.clip_end = 1        # 1m
        camera_data.lens = focal_length_mm
        camera_data.lens_unit = "MILLIMETERS"
        camera_data.sensor_fit = "AUTO"       

        
        camera_data.display_size = 0.2
        
        bpy.context.scene.render.resolution_x = int(img_width)
        bpy.context.scene.render.resolution_y = int(img_height)
        
        # Create light:
        light_data = bpy.data.lights.new(name="Light", type='POINT')
        light_data.energy = 1
        light_data.shadow_soft_size = 0.003
        light_object = bpy.data.objects.new(name="Light", object_data=light_data)
        light_object.location.y = 0.003
        
        light_data = bpy.data.lights.new(name="Light", type='POINT')
        light_data.energy = 1
        light_data.shadow_soft_size = 0.003
        light_object2 = bpy.data.objects.new(name="Light", object_data=light_data)
        light_object2.location.y = -0.003

        # Link objects to collection:
        coll = bpy.data.collections["Misc Collection"]
        coll.objects.link(camera_object)
        coll.objects.link(light_object)
        coll.objects.link(light_object2)
        
        light_object.parent = camera_object
        light_object2.parent = camera_object
        
    def random_viewpoint( self, rnd=random.Random ):
        """ Set to random position near my target object

        Make sure to call bpy.context.scene.update() before this function!
        """

        
        #####################################
        ## Set position:
        pos = blenderutils.random_pos_in_vicinity( self.target_obj, rnd = rnd,
                    min_dist_from_surface=0.01,
                    max_dist_from_surface=0.15 )
        self.cam.location = pos
        
        #####################################
        ## Set rotation:
        
        # Get random vertex location on the mesh
        target_vert = rnd.choice( self.target_obj.data.vertices )
        target_pos = target_vert.co
        
        blenderutils.rotate_towards(self.cam, target_pos,
                                    forward_vec = mathutils.Vector((0,0,-1)),  # cameras look at -z direction
                                    roll_ang = rnd.random()*math.pi - math.pi*0.5)
        
        # DEBUG: Set small icosphere at target position to make sure we're looking straight
        # at it. Only for debugging purposes.
#        bpy.ops.mesh.primitive_ico_sphere_add(
#                radius = 0.01, location = target_pos )

    def render( self ):
        """ Renders all configured layers.
        
        Note: For this function to render the correct things, at least one view layer
            needs to be active (which it is by default), the correct passes need to be
            enabled (like "Z" for depth or "Normals", see "View Layer Properties" in the 
            "Properties" window) and in the compositor, these passes need to be hooked up
            to "File Output" nodes (see "Compositing" tab in Blender).
            This should all be done automatically by renderutils.CompositingSetup!
            The rendered images will end up wherever the paths of the File Output nodes point
            (as set up by renderutils.CompositingSetup).
        """
        
        # Check which frame we're currently at. This frame will be appended to the output
        # file names, so we need to be able to remove it later.
        frame = bpy.context.scene.frame_current
            
        # This could be used to enable the depth-pass on a view layer via python.
        # For the moment, we'll enable the passes via the GUI instead.
        #bpy.context.scene.view_layers[-1].use_pass_z = True
    
        # set this camera as the active camera:
        bpy.context.scene.camera = self.cam
        
        # Ensure the compositor is used:
        bpy.context.scene.use_nodes = True
        
        bpy.ops.render.render( scene = bpy.context.scene.name )
        
        # Get reference to the tree:
        tree = bpy.context.scene.node_tree

        ##################
        ## DEPRECATED!
        ## The following code was originally used to move the files which were rendered
        ## to the default output directory (usually /tmp) to the final destimation. This
        ## was replaced by the cleaner method of changing the output path (base_path) of
        ## the output nodes in the compositioning (see renderutils.CompositingSetup).
        ## The advantage of the new method is that mutliple blender instances can render
        ## at the same time, without overwriting each others' outputs.
        ## Old code below is only left here as reference/reminder.
        ##################
        # Search for nodes in the tree which output files.
        # Then attempt to reconstruct the file name for these nodes and copy those result
        # files to the output directory.
        # Note that this is a bit complicated because
        # a) The CompositorNodeOutputFile class only tells us what file format it uses,
        #   not the exact extension we should use
        # b) Blender appends the frame number to the file name
#        for node in tree.nodes:
#            if isinstance(node, bpy.types.CompositorNodeOutputFile):
#                print(f"Found file output node (image type {node.format.file_format})")
#                ext = blenderutils.img_type_to_extension(node.format.file_format)
#                for f_slot in node.file_slots:
#                    in_filename = f"{f_slot.path}{frame:04}{ext}"
#                    out_filename = f"{f_slot.path}{frame:04}{ext}"
#                    in_path = os.path.join( node.base_path, in_filename )
#                    out_path = os.path.join( output_path, out_filename )
#                    print( "\tAttempting to copy result: ", in_path, "->", out_path )
#                    shutil.copyfile( in_path, out_path )


#        # create input image node
#        image_node = tree.nodes.new(type='CompositorNodeImage')
#        image_node.image = bpy.data.images['YOUR_IMAGE_NAME']
#        image_node.location = 0,0

#        # create output node
#        comp_node = tree.nodes.new('CompositorNodeComposite')   
#        comp_node.location = 400,0

#        # link nodes
#        links = tree.links
#        link = links.new(image_node.outputs[0], comp_node.inputs[0])


    def animate( self, num_frames, num_view_points, rnd=random.Random, valid_pose_check=None ):

        blenderutils.set_mode( "OBJECT" )


        if num_view_points < 2:
            # If only one view point is to be generated, do so at the first frame
            key_frames = [1]
        else:
            # If two or more view points are to be generated, use the first and last frames:
            key_frames = [1, num_frames - 1]
            # ... and choose the others randomly:
            if num_view_points > 2:
                key_frames += rnd.sample(
                                    range( 1, num_frames - 1 ),
                                    num_view_points-2 )
                
        key_frames.sort()
        print("Selected key_frames:", key_frames)
        
        for kf in key_frames:
            
            # Switch to the given frame:
            bpy.context.scene.frame_set( kf+1 )
            # Ensure all meshes are up to date:
            bpy.context.view_layer.update()
            
            #bpy.ops.wm.save_as_mainfile(filepath = os.path.join( "/home/pfeiffemi/Projects/Deformation/nonrigid-data-generation-pipeline/data/tmp_dynamic10/", f"render_setup_f{kf}.blend"))

            # Note: Ugly workaround to only allow keyframes along the positive X direction.
            # This avoids (most) interesections with the mesh.
            # Should be replaced with a proper path-planning in the future!
            if valid_pose_check is not None:
                found_valid_position = False
                num_tries = 0
                while not found_valid_position:
                    if num_tries > 5000:
                        found_valid_position = True
                        break
                    
                        
                    # Set random position:
                    self.random_viewpoint( rnd )

                    # Important! Ensure the transform matrices are updated:
                    bpy.context.view_layer.update()
                    
                    view_dir = self.cam.matrix_world @ mathutils.Vector((0,0,-1))
                    if valid_pose_check( self.cam.location, view_dir ):
                        found_valid_position = True
                        
                    num_tries += 1
                
            
            # store keyframe location and rotation:
            self.cam.keyframe_insert(data_path="location", frame=kf)
            self.cam.rotation_mode = "QUATERNION"
            self.cam.keyframe_insert(data_path="rotation_quaternion", frame=kf)
    
    def save_calibration( self, outdir ):
        
        K, w, h = self.calibration
        
        print("K,w,h", K, w, h)
        
        data = {
            "camera_matrix":K.tolist(),
            "dist_coeff":[0]*5,
            "image_width":w,
            "image_height":h,
            }
        
        filename = "camera.yaml"
        full_filename = os.path.join( outdir, filename )
        with open(full_filename, "w") as f:
            yaml.dump(data, f)
        
        
    @property
    def calibration( self ):
        """ Read camera info from blender camera object """
        
        camera_data = self.cam.data
        
        assert camera_data.lens_unit == "MILLIMETERS"
        assert camera_data.sensor_fit == "AUTO"
        
        ## NOTE: Shift x and y are currently not used. I'd have to double-check what they
        ## correspond to in the camera matrix (are they added to cx and cy?).
        ## For now, we'll ignore them and keep them at 0.
        assert camera_data.shift_x == 0 and camera_data.shift_y == 0, \
                "Camera's shift_x and shift_y must both be zero. Values other than zero currently not implemented."
        
        # Image width and height:
        pct = bpy.context.scene.render.resolution_percentage
        w_pixels = bpy.context.scene.render.resolution_x*pct/100.0
        h_pixels = bpy.context.scene.render.resolution_y*pct/100.0
        print("Image size bpy.context.scene.render.resolution_x:", bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
        print("Image size (in pixels):", w_pixels, h_pixels)
                
        # Get camera focal length:
        fx_mm = camera_data.lens   # in MM!
        fy_mm = fx_mm
        print("fx, fy (in mm):", fx_mm, fy_mm)
        sensor_width_mm = camera_data.sensor_width
        sensor_height_mm = camera_data.sensor_height
        print("Sensor size (mm):", sensor_width_mm, sensor_height_mm)
        
        fx_pixels = fx_mm / sensor_width_mm * w_pixels
        fy_pixels = fy_mm / sensor_height_mm * h_pixels
        
        print("fx, fy (in pixels):", fx_pixels, fy_pixels)
        
        cx_pixels = w_pixels*0.5
        cy_pixels = h_pixels*0.5
        
        K = []
        K = np.zeros( shape=(3,3) )
        K[0,0] = fx_pixels
        K[1,1] = fy_pixels
        K[2,2] = 0
        K[0,2] = cx_pixels
        K[1,2] = cy_pixels
        print("Camera calibration (intrinsics, in pixels):\n", K)
        
        return K, w_pixels, h_pixels
