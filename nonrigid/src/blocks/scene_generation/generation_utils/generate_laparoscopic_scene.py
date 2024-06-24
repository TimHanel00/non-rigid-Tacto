import random
import os
import sys
import bpy
import importlib
import mathutils
import pprint

try:    # Wrap this in try block so that documentation can be built without bpy.data
    d = os.path.dirname(bpy.data.filepath)
    sys.path.append(d)
    sys.path.append(os.path.join(d, "..", "src", "utils"))
    sys.path.append(os.path.join(d, "..", "..", "utils"))
    sys.path.append(os.path.join(d, "src", "utils"))
    sys.path.append(os.path.join(d, "generation_utils"))
except:
    print("WARNING: Could not add blender paths. Make sure you're running this from" +\
        " within blender!")

d2 = os.getcwd()
sys.path.append(os.path.join(d2, "src", "blocks", "scene_generation", "generation_utils"))
sys.path.append(os.path.abspath(os.path.join(d2, "..", "src", "blocks", "scene_generation", "generation_utils")))

print("d2", d2)
for e in sys.path:
    print("\t", e)

#from vtkutils import *
#from generalutils import *
import blenderutils
import generate_random_organ
import generate_fat
import generate_ligament
import generate_force
import generate_hull

importlib.reload(generate_random_organ)
importlib.reload(generate_fat)
importlib.reload(generate_ligament)
importlib.reload(generate_force)
importlib.reload(generate_hull)
importlib.reload(blenderutils)

def load_from_source( object_config, directory ):
    if "source_file" in object_config.keys():
        if len(object_config["source_file"]) > 0:
            path = os.path.join( directory, object_config["source_file"] )
            obj = blenderutils.import_mesh( path )
            name = object_config["filename"]
            obj.name = name
            return obj
    return None

def generate_scene(args, rnd=random.Random(), outdir="."):

    # Remove standard cube etc:
    blenderutils.clear_scene()
    
    # All organs:
    all_organs = []
    # All internal organs:
    internal_organs = []
    # Objects to which we can attach the liver:
    attached_organs = []
    #for i in range(3):
    #    o = generate_random_organ.create(rnd=rnd, bounds=blenderutils.BoundingBox(0.3),
    #            add_concavity=False, name=f"attached_organ{i}")
    #    attached_organs.append(o)
    
    # Create the liver:
    if args.add_deformable_organ:
        #bounds = blenderutils.BoundingBox(bound_box=abdominal_wall.bound_box)
        #liver = generate_random_organ.create(rnd=rnd, bounds=bounds)
        
        # Try to load from source. Returns None if no source file is given:
        deformable = load_from_source( args.add_deformable_organ, outdir )
        
        if deformable == None:
            name = args.add_deformable_organ["filename"]
            
            if "size" in args.add_deformable_organ.keys():
                size = mathutils.Vector( args.add_deformable_organ["size"] )
            else:
                size = mathutils.Vector( (0.3, 0.3, 0.3) )
            vec_min = -size*0.5
            vec_max = size*0.5
            bounds=blenderutils.BoundingBox(vec_min=vec_min, vec_max=vec_max)
            
            add_concavity = True
            if "add_concavity" in args.add_deformable_organ.keys():
                add_concavity = args.add_deformable_organ["add_concavity"]
                
            predeform_twist = False
            if "predeform_twist" in args.add_deformable_organ.keys():
                predeform_twist = args.add_deformable_organ["predeform_twist"]
                
            predeform_noise = False
            if "predeform_noise" in args.add_deformable_organ.keys():
                predeform_noise = args.add_deformable_organ["predeform_noise"]
                
            cut_to_fit = False
            if "cut_to_fit" in args.add_deformable_organ.keys():
                cut_to_fit = args.add_deformable_organ["cut_to_fit"]
           
            deformable = generate_random_organ.create(
                        rnd=rnd,
                        bounds=bounds,
                        name=name,
                        add_concavity=add_concavity,
                        predeform_twist=predeform_twist,
                        predeform_noise=predeform_noise,
                        cut_to_fit=cut_to_fit
            )
        internal_organs.append( deformable )
        all_organs.append( deformable )
    
    if args.add_rigid_organ:
        for org in args.add_rigid_organ:
            rigid = load_from_source( org, outdir )
            if rigid == None:
                name = org["filename"]
                
                if "size" in args.add_deformable_organ.keys():
                    size = mathutils.Vector( args.add_deformable_organ["size"] )
                else:
                    size = mathutils.Vector( (0.3, 0.3, 0.3) )
                vec_min = -size*0.5
                vec_max = size*0.5
                bounds=blenderutils.BoundingBox(vec_min=vec_min, vec_max=vec_max)
                
                add_concavity = False
                if "add_concavity" in args.add_deformable_organ.keys():
                    add_concavity = args.add_deformable_organ["add_concavity"]
            
                rigid = generate_random_organ.create(
                            rnd=rnd, bounds=bounds,
                            name=name, add_concavity=add_concavity)
            rigid.select_set(True)
            # don't move the loaded or generated rigid organ if rigid_organ parameter is unset
            if org["rigid_transform"]:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                if args.add_deformable_organ:
                    blenderutils.push_outside( rigid, deformable, offset=0, rnd=rnd )

            attached_organs.append( rigid )
            internal_organs.append( rigid )
            all_organs.append( rigid )
    
    # Apply any transforms, so that objects all have the world origin as their origin:
    for o in all_organs:
        o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    if args.add_abdominal_wall:        
        name = args.add_abdominal_wall["filename"]
        
        outset_amplitude = 0.01
        if "outset_amplitude" in args.add_abdominal_wall:
            outset_amplitude = args.add_abdominal_wall["outset_amplitude"]
        outset_frequency = 5
        if "outset_frequency" in args.add_abdominal_wall:
            outset_frequency = args.add_abdominal_wall["outset_frequency"]
        
        abdominal_wall = load_from_source( args.add_abdominal_wall, outdir )
        if abdominal_wall == None:
            abdominal_wall = generate_hull.create(
                            internal_organs,
                            obj_name = name,
                            outset_amplitude = outset_amplitude,
                            outset_frequency = outset_frequency
                            )
        attached_organs.append( abdominal_wall )
        all_organs.append( abdominal_wall )
    
    if args.add_fill_fat:
        
        assert args.add_abdominal_wall, "--add_fill_fat requires --add_abdominal_wall!"
        
        amount = args.add_fill_fat["fat_amount"]
        up_vector = mathutils.Vector(args.add_fill_fat["fat_up_vector"])
        filename = args.add_fill_fat["filename"]
        fat = load_from_source( args.add_fill_fat, outdir )
        if fat == None:
            fat = generate_fat.fill_with_fat(abdominal_wall, deformable, up_vector, amount,
                    obj_name=filename,
            )
        all_organs.append( fat )
        
    
    # Create attachments between the liver and the surrounding organs:
    ligaments = []
    if args.add_ligament is not None and args.add_deformable_organ is not None and args.add_abdominal_wall is not None:
        for l in args.add_ligament:
            lig = load_from_source( l, outdir )
            if lig == None:
                # For now, choose a random organ to attach to:
                #attached = rnd.choice( attached_organs )
                name = l["filename"]
                lig = generate_ligament.connect(source_obj=deformable, target_obj=abdominal_wall, rnd=rnd, obj_name=name)
            ligaments.append(lig)
        
    
    nodal_forces = []
    if args.add_nodal_force is not None and args.add_deformable_organ is not None:
        for f in args.add_nodal_force:
            force = load_from_source( f, outdir )
            if force == None:
                base_on_normal = False
                ang_from_normal = 0
                if "ang_from_normal" in f.keys():
                    base_on_normal = True
                    ang_from_normal = f["ang_from_normal"]
                
                force = generate_force.create(
                        deformable,
                        obj_name = f["filename"],
                        rnd = rnd,
                        magnitude = f["magnitude"],
                        base_on_normal = base_on_normal,
                        ang_from_normal = ang_from_normal
                        )
            nodal_forces.append( force )
        
    fixed_attachments = []
    if args.add_fixed_attachments is not None and args.add_deformable_organ is not None:
        for f in args.add_fixed_attachments:
            fixed_attachment_points = load_from_source( f, outdir )
            if fixed_attachment_points == None:
                fixed_attachment_points = blenderutils.select_random_partial_surface(
                        deformable,
                        f["surface_amount"],
                        name = f["filename"],
                        rnd = rnd
                        )
            fixed_attachments.append( fixed_attachment_points )
    
    tumors = []
    if args.add_tumor:
        for tu in args.add_tumor:
            tumor = load_from_source( tu, outdir )
            if tumor == None:
                name = tu["filename"]
                
                if "size" in tu.keys():
                    size = mathutils.Vector( tu["size"] )
                else:
                    size = mathutils.Vector( (0.01, 0.01, 0.01) )
                vec_min = -size*0.5
                vec_max = size*0.5
                bounds=blenderutils.BoundingBox(vec_min=vec_min, vec_max=vec_max)
                
                organ = next(o for o in all_organs if o.name == tu["organ_file"])
            
                tumor = generate_random_organ.create(
                            rnd=rnd, bounds=bounds,
                            name=name, add_concavity=False,
                            cut_to_fit = True,
                            extrusion_size = 0.3,
                            containing_obj = organ,

                            target_minimum_voxel_size = 0.003 )
            tumor.select_set(True)
            # don't move the loaded or generated rigid organ if rigid_organ parameter is unset
#            if org["rigid_transform"]:
#                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
#                if args.add_deformable_organ:
#                    blenderutils.push_outside( tumor, deformable, offset=0, rnd=rnd )

            tumors.append( tumor )
            all_organs.append( tumor )


    # Export everything:
    for i, organ in enumerate(all_organs):
        blenderutils.export(organ, outdir=args.outdir, filename=organ.name)
        
    for i, lig in enumerate(ligaments):
        # Export as .obj, because that can hold points + edges without any faces:
        blenderutils.export(lig, outdir=args.outdir, filename=lig.name)
        
    for i, force in enumerate(nodal_forces):
        # Export as .obj, because that can hold points + edges without any faces:
        blenderutils.export(force, outdir=args.outdir, filename=force.name)
        
    for i, fa in enumerate(fixed_attachments):
        # Export as .obj, because that can hold points + edges without any faces:
        blenderutils.export(fa, outdir=args.outdir, filename=fa.name)
        
        
    for i, tu in enumerate(tumors):
        # Export as .obj, because that can hold points + edges without any faces:
        blenderutils.export(tu, outdir=args.outdir, filename=tu.name)

if __name__ == "__main__":
    
    import argparse
    import json
    
    # Remove all arguments passed to Blender, only take those after the double dash '--' into account:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Generate a random mesh using Blender functionality.")
    parser.add_argument("--outdir", type=str, default=".", help="Folder in which to save the random mesh.")
    #parser.add_argument("--bounds", type=float, default=0.3, help="Edge of the cube defining the volume where the object must lie.")
    parser.add_argument("--random_seed", type=int, default=8)
    parser.add_argument("--add_abdominal_wall", type=json.loads, help="Adds surrounding organs")
    parser.add_argument("--add_fill_fat", type=json.loads, help="Fill abdominal wall (partially) with fat tissue")
    parser.add_argument("--add_deformable_organ", type=json.loads, help="Adds a random surface")
    parser.add_argument("--add_ligament", action="append", type=json.loads, help="Adds ligaments")
    parser.add_argument("--add_rigid_organ", action="append", type=json.loads, help="Adds surrounding organs")
    parser.add_argument("--add_fixed_attachments", action="append", type=json.loads, help="Adds fixed attachment points")
    parser.add_argument("--add_nodal_force", action="append", type=json.loads, help="Adds force to surface node of deformable organ")
    parser.add_argument("--add_camera", type=json.loads, help="Add a camera to the scene")
    parser.add_argument("--add_tumor", action="append", type=json.loads, help="Adds tumor")
    args = parser.parse_args(argv)

    if args.add_ligament is not None and (args.add_abdominal_wall is None or args.add_deformable_organ is None):
        raise ArgumentError( "To add a ligament, both --add_abdominal_wall and --add_deformable_organ must be given!")

    print("Running scene generation with arguments:")
    p = pprint.PrettyPrinter(depth=4)
    p.pprint(vars(args))
    
    rnd = random.Random()
    rnd.seed(args.random_seed)
    
    generate_scene(args, rnd, outdir=args.outdir)
