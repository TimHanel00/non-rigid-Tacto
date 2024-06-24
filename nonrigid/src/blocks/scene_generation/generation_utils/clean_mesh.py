import sys
import os
import bpy

try:    # Wrap this in try block so that documentation can be built without bpy.data
    d = os.path.dirname(bpy.data.filepath)
    sys.path.append(d)
    sys.path.append(os.path.join(d, "..", "src", "utils"))
    sys.path.append(os.path.join(d, "src", "utils"))
except:
    print("WARNING: Could not add blender paths. Make sure you're running this from" +\
        "within blender!")

import blenderutils

if __name__ == "__main__":
    
    import argparse
    
    # Remove all arguments passed to Blender, only take those after the double dash '--' into account:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Generate a random mesh using Blender functionality.")
    parser.add_argument("--infile", type=str, default="surface.stl", help="Name of input file to use. Must be .stl, and must contain full path.")
    parser.add_argument("--outfile", type=str, default="surface_cleaned.stl", help="Output filename. Must be .stl!")
    parser.add_argument("--remesh", action="store_true")
    parser.add_argument("--target_verts", type=int, default=-1)
    args = parser.parse_args(argv)
    
    blenderutils.clear_scene()
    
    obj = blenderutils.import_mesh( args.infile )
    #obj = objs.pop()
    
    orig_verts = len(obj.data.vertices)
    
    blenderutils.remove_non_manifolds(obj)
    
    remaining_verts = len(obj.data.vertices)
    
    # print(f"Removed {orig_verts - remaining_verts} vertices. " + \
    #     f"Remaining: {remaining_verts} vertices.")
        
    if args.remesh:
        blenderutils.clean_mesh(obj, remesh_octree_depth=6, remesh_scale=0.9)

    if args.target_verts > 0:
        if args.target_verts < len(obj.data.vertices):
            blenderutils.decimate(obj, args.target_verts)
        else:
            print("Skipping decimation. Object has less than 'target_verts' vertices.")
    
    blenderutils.remove_non_manifolds(obj)
    
    outdir, outfile = os.path.split(args.outfile)
    blenderutils.export(obj, outdir=outdir, filename=outfile)


