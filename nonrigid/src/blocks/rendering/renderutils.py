import os
import bpy

    
    
class CompositingSetup:
    
    def __init__( self, outdir = "/tmp" ):
        # Initialize a layer for the main scene (Standard) and one for objects such as labels
        # which should be displayed "on top of" the main scene (Overlay). Note: Currently, the
        # main purpose of "overlay" is to render meshes that are in this view layer to be slightly
        # closer to the camera (by slightly offsetting the depth) to avoid z-fighting issues.
        setup_view_layers( ["Standard", "Overlay"] )
        setup_collections( ["Organ Collection", "Overlay Collection", "Misc Collection"] )
        # Do not show the overlay collection on the standard view layer:
        exclude_collection_on_view_layer(
                        collection_name = "Overlay Collection",
                        view_layer_name = "Standard" )
        # Do not show the organs on the overlay layer:
        exclude_collection_on_view_layer(
                        collection_name = "Organ Collection",
                        view_layer_name = "Overlay" )
                        
        set_active_view_layer( "Standard" )
        
        ### Set up rendering settings:
        bpy.context.scene.render.engine = "BLENDER_EEVEE"   # EEVEE tends to be much faster
        bpy.context.scene.eevee.taa_render_samples = 2
        bpy.context.scene.eevee.use_volumetric_lights = False
        bpy.context.scene.eevee.gi_diffuse_bounces = 1
        # Note: When enabling soft shadows, increase taa_render_samples!
        bpy.context.scene.eevee.use_soft_shadows = False
        bpy.context.scene.eevee.shadow_cube_size = "512"
        bpy.context.scene.eevee.shadow_cascade_size = "128"
        
        ## Remove background color:
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0,0,0,1)
        
        self.added_objects = []
        self.cur_output = None
        self.cur_overlay_output = None
        self.outdir = outdir
        
        print("Saving rendered images to:", self.outdir)
    
    def setup_composition_nodes( self ):
        
        # Enable nodes
        bpy.context.scene.use_nodes = True
        
        # Find standard view layer
        vl = bpy.context.scene.view_layers["Standard"]

        # Enable depth
        vl.use_pass_z = True

        # Enable normals
        vl.use_pass_normal = True
        
        # Get reference to the composition node tree:
        tree = bpy.context.scene.node_tree
        
        for node in tree.nodes:
            tree.nodes.remove( node )
            
        # Add a Render Layer node:
        render_layers = tree.nodes.new("CompositorNodeRLayers")
        self.render_layers = render_layers
        # Set it to use the output of the Standard layer:
        render_layers.layer = "Standard"
        render_layers.name = "RenderLayers_Standard"
        
        # Add a Render Layer node:
        render_layers_overlay = tree.nodes.new("CompositorNodeRLayers")
        self.render_layers_overlay = render_layers_overlay
        # Set it to use the output of the Standard layer:
        render_layers_overlay.layer = "Overlay"
        render_layers_overlay.name = "RenderLayers_Overlay"
        render_layers_overlay.location.y -= 500
        
        # Enable usage of cryptomatte (for segmentation layers)
        vl.use_pass_cryptomatte_object = True
    
        # Find standard view layer
        vl_overlay = bpy.context.scene.view_layers["Overlay"]
        # Enable usage of cryptomatte (for segmentation layers)
        vl_overlay.use_pass_cryptomatte_object = True
        
        #############################
        ## Create a combination of the two render layer results.
        ## This is done by combining them according to their depth maps, however,
        ## The overlay is offset by a low value to "move it closer" to the camera.
        ## This is done so that regions which are exactly at the same depth in the
        ## two renders don't z-fight and instead the object in the overlay ends up
        ## in the image in those areas.
        ## Note: This value is configurable, but I found that the value here works
        ## well for the current camera's near and far values. If those change, the
        ## threshold here should probably also be changed!
        
        # Math node to slightly lower depth value for overlay render layer:
        z_subtract = tree.nodes.new("CompositorNodeMath")
        self.z_subtract = z_subtract
        z_subtract.operation = "SUBTRACT"
        z_subtract.inputs[1].default_value = 0.001
        z_subtract.location.x += 300
        z_subtract.location.y -= 300
        
        # Combine by Z value node:
        z_combine = tree.nodes.new("CompositorNodeZcombine")
        z_combine.location.x += 450
        
        tree.links.new(render_layers.outputs["Image"], z_combine.inputs[0])
        tree.links.new(render_layers.outputs["Depth"], z_combine.inputs[1])
        tree.links.new(render_layers_overlay.outputs["Image"], z_combine.inputs[2])
        tree.links.new(render_layers_overlay.outputs["Depth"], z_subtract.inputs[0])
        tree.links.new(z_subtract.outputs[0], z_combine.inputs[3])
        
        
        #############################
        
        # Create node which saves the rendered color images:
        color_output = tree.nodes.new("CompositorNodeOutputFile")
        color_output.format.file_format = "PNG"
        color_output.base_path = self.outdir
        color_output.file_slots.remove(color_output.inputs[0])  # Remove default input
        color_output.file_slots.new("color")
        color_output.location.x += 700
        tree.links.new(render_layers.outputs["Image"], color_output.inputs["color"])
        
        # Create node which saves the rendered depth:
        depth_output = tree.nodes.new("CompositorNodeOutputFile")
        depth_output.format.file_format = "OPEN_EXR"
        depth_output.base_path = self.outdir
        depth_output.file_slots.remove(depth_output.inputs[0])  # Remove default input
        depth_output.file_slots.new("depth")
        depth_output.location.x += 700
        depth_output.location.y -= 110
        tree.links.new(render_layers.outputs["Depth"], depth_output.inputs["depth"])
        
        # Create node which saves the rendered normals:
        normal_output = tree.nodes.new("CompositorNodeOutputFile")
        normal_output.format.file_format = "PNG"
        normal_output.base_path = self.outdir
        normal_output.file_slots.remove(normal_output.inputs[0])  # Remove default input
        normal_output.file_slots.new("normal")
        normal_output.location.x += 700
        normal_output.location.y -= 220
        tree.links.new(render_layers.outputs["Normal"], normal_output.inputs["normal"])
        
        # Create node which saves the rendered color images combined with the overlay:
        combined_color_output = tree.nodes.new("CompositorNodeOutputFile")
        combined_color_output.format.file_format = "PNG"
        combined_color_output.base_path = self.outdir
        combined_color_output.file_slots.remove(combined_color_output.inputs[0])  # Remove default input
        combined_color_output.file_slots.new("color_with_overlay")
        combined_color_output.location.x += 700
        tree.links.new(z_combine.outputs["Image"], combined_color_output.inputs["color_with_overlay"])
    
    def setup_object_mask( self, obj, color, overlay=False ):
        
        # Get reference to the composition node tree:
        tree = bpy.context.scene.node_tree
        
        if not overlay:
            render_layers = tree.nodes["RenderLayers_Standard"]
        else:
            render_layers = tree.nodes["RenderLayers_Overlay"]
            
            
        # Only output masks for meshes (not cameras, lights etc.):
        if not obj.type == "MESH":
            return
        
        # Masks only make sense for object which actually have faces:
        if len(obj.data.polygons) == 0:
            return
        
        # Get main color from the material:
        col = obj.data.materials[0].diffuse_color
        print("mat col:", col)
        
        obj_name, ext = os.path.splitext( obj.name )
        output_obj_name = f"mask_{obj_name}"
        
        i = len(self.added_objects)
        y_loc = -(330 + 300*i)
        
        # Add a cryptomatte node:
        matte = tree.nodes.new("CompositorNodeCryptomatteV2")
        if overlay:
            matte.layer_name = "Overlay.CryptoObject"
        else:
            matte.layer_name = "Standard.CryptoObject"
        matte.location.x += 900
        matte.location.y = y_loc
        matte.matte_id = obj.name
        # Input to the matte 
        tree.links.new(render_layers.outputs["Image"], matte.inputs["Image"])
        
        mix = tree.nodes.new("CompositorNodeMixRGB")
        mix.location.x += 1200
        mix.location.y = y_loc
        mix.inputs[1].default_value = (0,0,0,0)
        mix.inputs[2].default_value = color
        tree.links.new(matte.outputs["Matte"], mix.inputs["Fac"])
        
#        # Create node which saves the rendered mask:
#        mask_output = tree.nodes.new("CompositorNodeOutputFile")
#        mask_output.format.file_format = "PNG"
#        mask_output.base_path = "/tmp/"
#        mask_output.file_slots.remove(mask_output.inputs[0])  # Remove default input
#        mask_output.file_slots.new(output_obj_name)
#        mask_output.location.x += 600
#        mask_output.location.y = y_loc
#        # Save the generated matte as an image:
#        tree.links.new(matte.outputs["Matte"], mask_output.inputs[output_obj_name])
        
        self.added_objects.append( obj )
        
        if overlay:
            if self.cur_overlay_output:
                alpha_over = tree.nodes.new("CompositorNodeAlphaOver")
                alpha_over.location.x = 1500 + i*200
                alpha_over.location.y = y_loc
                tree.links.new(self.cur_overlay_output, alpha_over.inputs[1])
                tree.links.new(mix.outputs[0], alpha_over.inputs[2])
                self.cur_overlay_output = alpha_over.outputs[0]
            else:
                self.cur_overlay_output = mix.outputs[0]
        else:
            if self.cur_output:
                alpha_over = tree.nodes.new("CompositorNodeAlphaOver")
                alpha_over.location.x = 1500 + i*200
                alpha_over.location.y = y_loc
                tree.links.new(self.cur_output, alpha_over.inputs[1])
                tree.links.new(mix.outputs[0], alpha_over.inputs[2])
                self.cur_output = alpha_over.outputs[0]
            else:
                self.cur_output = mix.outputs[0]
            
    def combine( self, render_color_image_with_overlay = False ):
        """ Set up nodes to render a combined version of scene and overlay.

        By default, this renders only the segmentation map in this mode. If render_color_image_with_overlay is
        set to True, it will also render the normal color image with the overlay.
        The reason is that the overlay markings usually simulate some sort of (manual or automatic) landmark
        extraction process, so we assume that the (2D) positions of these landmarks are known in the downstream
        task. Thus, they must be easy to extract also from the rendered images.
        It's relatively easy to extract the 2d pixels which are part of the various overlay
        pieces (i.e. the overlay marked regions) from the (combined) segmentation map, but more difficult to
        extract them from the normal color image (where lighting effects make this extraction harder).
        """
        
        # Get reference to the composition node tree:
        tree = bpy.context.scene.node_tree
       
        if render_color_image_with_overlay:
            # Create node which saves the combined masks:
            segmentation_output = tree.nodes.new("CompositorNodeOutputFile")
            segmentation_output.format.file_format = "PNG"
            segmentation_output.base_path = self.outdir
            segmentation_output.file_slots.remove(segmentation_output.inputs[0])  # Remove default input
            segmentation_output.file_slots.new("segmentation")
            segmentation_output.file_slots["segmentation"].use_node_format = True
            segmentation_output.format.color_mode = "RGB"
            segmentation_output.location.x += 1700 + len(self.added_objects)*200
            tree.links.new(self.cur_output, segmentation_output.inputs["segmentation"])
        
        # If there is an overlay, then render a combined mask that holds both the original
        # mask and (overlayed) the overlay elements.
        if self.cur_overlay_output:
            # Combine by Z value node:
            z_combine = tree.nodes.new("CompositorNodeZcombine")
            z_combine.location.x += 1500 + len(self.added_objects)*200
            z_combine.location.y -= 300
            
            tree.links.new(self.cur_output, z_combine.inputs[0])
            tree.links.new(self.render_layers.outputs["Depth"], z_combine.inputs[1])
            tree.links.new(self.cur_overlay_output, z_combine.inputs[2])
            tree.links.new(self.z_subtract.outputs[0], z_combine.inputs[3])
            
            # Create node which saves the combined masks:
            combined_segmentation_output = tree.nodes.new("CompositorNodeOutputFile")
            combined_segmentation_output.format.file_format = "PNG"
            combined_segmentation_output.base_path = self.outdir
            combined_segmentation_output.file_slots.remove(combined_segmentation_output.inputs[0])  # Remove default input
            combined_segmentation_output.file_slots.new("segmentation_with_overlay")
            combined_segmentation_output.file_slots["segmentation_with_overlay"].use_node_format = True        
            combined_segmentation_output.format.color_mode = "RGB"
            combined_segmentation_output.location.x += 1700 + len(self.added_objects)*200
            combined_segmentation_output.location.y -= 300
            tree.links.new(z_combine.outputs["Image"], combined_segmentation_output.inputs["segmentation_with_overlay"])

    
def setup_view_layers( layer_names ):
    
    for name in layer_names:
        if name in bpy.context.scene.view_layers:
            print( f"View layer '{name}' already exists, not re-creating" )
        else:
            print( f"Creating new view layer: {name}" )
            bpy.context.scene.view_layers.new( name )
        view_layer = bpy.context.scene.view_layers[name]
        view_layer.use_pass_z = True    # Enable depth rendering
        
        collection_name = f"{name} Collection"
                
def setup_collections( collection_names ):
    for collection_name in collection_names:
        if collection_name in bpy.data.collections:
            print( f"Collection '{collection_name}' already exists, not re-creating" )
        else:
            print( f"Creating new view layer: {collection_name}" )
            bpy.data.collections.new( collection_name )    
        collection = bpy.data.collections[collection_name]
        if not collection_name in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(collection)
        collection.hide_viewport = False
        
def exclude_collection_on_view_layer( collection_name, view_layer_name ):
    
    # Get the layer we're interested in:
    layer = bpy.context.scene.view_layers[view_layer_name]
    layer_collection = layer.layer_collection.children[collection_name]
    layer_collection.exclude = True
    
#    for layer in bpy.context.scene.view_layers:
#        # Set view layer active:
#        bpy.context.window.view_layer = layer
#        print("View Layer:", layer, layer.active_layer_collection)
#        
#        for name in layer_names:
#            
#            collection_name = f"{name} Collection"
#            print("\t", collection_name)
#            layer_collection = layer.layer_collection.children[collection_name]
#            bpy.context.view_layer.active_layer_collection = layer_collection
#            print("\tActive", layer.active_layer_collection)
#            if name != layer.name:
#                layer_collection.exclude = True
                
def set_active_view_layer( name ):
    
    for layer in bpy.context.scene.view_layers:
        if layer.name == name:
            bpy.context.window.view_layer = layer
            return
            
