###################################################
## This script is intended for testing the scene generation from within blender's GUI. Load
## This script in blender's text editor, modify to your needs, then press "Run Script"
##############################
import os
import sys
import bpy
import importlib
import pprint
import random
import traceback

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
        
import generate_laparoscopic_scene

importlib.reload(generate_laparoscopic_scene)


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
    parser.add_argument("--random_seed", type=int, default=3)
    parser.add_argument("--add_abdominal_wall", type=json.loads, help="Adds surrounding organs")
    parser.add_argument("--add_fill_fat", type=json.loads, help="Fill abdominal wall (partially) with fat tissue")
    parser.add_argument("--add_deformable_organ", type=json.loads, help="Adds a random surface")
    parser.add_argument("--add_ligament", action="append", type=json.loads, help="Adds ligaments")
    parser.add_argument("--add_rigid_organ", action="append", type=json.loads, help="Adds surrounding organs")
    parser.add_argument("--add_fixed_attachments", action="append", type=json.loads, help="Adds fixed attachment points")
    parser.add_argument("--add_nodal_force", action="append", type=json.loads, help="Adds force to surface node of deformable organ")
    parser.add_argument("--add_camera", type=json.loads, help="Add a camera to the scene")
    parser.add_argument("--add_tumor", type=json.loads, help="Add a tumor to the scene")
    args = parser.parse_args(argv)

    args.add_abdominal_wall = {'filename': 'abdominal_wall_A.obj',  \
                            'outset_amplitude': 0.0468228632332338,  \
                            'outset_frequency': 4.812417252050743}
    args.add_camera = None
    args.add_deformable_organ = {'add_concavity': True,  \
                              'cut_to_fit': True,  \
                              'filename': 'surface_A.stl',  \
                              'predeform_noise': True,  \
                              'predeform_twist': True,  \
                              'size': [0.3, 0.3, 0.3]}
    args.add_fill_fat = {'fat_amount': 0.6045098885474435,  \
                      'fat_up_vector': [0, 0, 1],  \
                      'filename': 'abdominal_wall_fat_A.obj'}
    args.add_fixed_attachments = [{'filename': 'fixed_attachments_A.obj',  \
                                'surface_amount': 0.034091892219985195}]
    args.add_ligament = [{'filename': 'ligament_A.obj'},  \
                      {'filename': 'ligament_B.obj'}]
    args.add_nodal_force = None
    args.add_rigid_organ = [{'filename': 'attached_organ_A.obj',  \
                          'rigid_transform': True},  \
                         {'filename': 'attached_organ_B.obj',  \
                          'rigid_transform': True}]
    args.add_tumor = [{'filename': 'tumor_A.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.02045922491688329,  \
                             0.011262658534061012,  \
                             0.027743656399206]},  \
                   {'filename': 'tumor_B.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.029569636900941325,  \
                             0.02525543089991474,  \
                             0.027554148760989567]},  \
                   {'filename': 'tumor_C.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.012753689232983315,  \
                             0.023245793706503214,  \
                             0.027470957199199834]},  \
                   {'filename': 'tumor_D.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.02209959829788603,  \
                             0.016803567886317834,  \
                             0.007517530201709145]},  \
                   {'filename': 'tumor_E.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.015854295886344592,  \
                             0.020272174336095038,  \
                             0.027825276330947453]},  \
                   {'filename': 'tumor_F.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.02916515919426897,  \
                             0.016925244413817923,  \
                             0.026632748194291]},  \
                   {'filename': 'tumor_G.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.011512307759798985,  \
                             0.02512569567532556,  \
                             0.01871748259588973]},  \
                   {'filename': 'tumor_H.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.005351042504100474,  \
                             0.022992617160098854,  \
                             0.014970588555606717]},  \
                   {'filename': 'tumor_I.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.025621124428705826,  \
                             0.021703830030796272,  \
                             0.005028570482860707]},  \
                   {'filename': 'tumor_J.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.017339446661633114,  \
                             0.02669006938731952,  \
                             0.011097771922178298]},  \
                   {'filename': 'tumor_K.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.01313010906868475,  \
                             0.026761780802716365,  \
                             0.009776677287559763]},  \
                   {'filename': 'tumor_L.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.019187768515516797,  \
                             0.010965398215380505,  \
                             0.029188506257253582]},  \
                   {'filename': 'tumor_M.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.02507948673199675,  \
                             0.016199239285889257,  \
                             0.007011145463813385]},  \
                   {'filename': 'tumor_N.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.013001365116813643,  \
                             0.017698516063014348,  \
                             0.02832084560567267]},  \
                   {'filename': 'tumor_O.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.007726446148277591,  \
                             0.01878168115226378,  \
                             0.02266403524667224]},  \
                   {'filename': 'tumor_P.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.018686022783210594,  \
                             0.0253616715822834,  \
                             0.018507090174258098]},  \
                   {'filename': 'tumor_Q.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.02909596364934502,  \
                             0.020079640699034573,  \
                             0.019690426604385906]},  \
                   {'filename': 'tumor_R.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.016124725656887905,  \
                             0.019907171539577655,  \
                             0.01462252864931651]},  \
                   {'filename': 'tumor_S.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.01939127535412221,  \
                             0.01225823756006895,  \
                             0.009734783213858903]},  \
                   {'filename': 'tumor_T.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.009668238206388877,  \
                             0.020319329496715166,  \
                             0.021416484724740722]},  \
                   {'filename': 'tumor_U.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.016913274800234517,  \
                             0.0072456090298898415,  \
                             0.02394009804916092]},  \
                   {'filename': 'tumor_V.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.026919259270569366,  \
                             0.028084525398657016,  \
                             0.02606150557850456]},  \
                   {'filename': 'tumor_W.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.027454328033946974,  \
                             0.02807706099550442,  \
                             0.01851499812370136]},  \
                   {'filename': 'tumor_X.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.014782401255865621,  \
                             0.022632084996360154,  \
                             0.011890853032803178]},  \
                   {'filename': 'tumor_Y.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.02529071771269696,  \
                             0.026237149129659177,  \
                             0.02737597418566688]},  \
                   {'filename': 'tumor_AZ.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.019745029588278996,  \
                             0.028744121830803014,  \
                             0.019492375268640148]},  \
                   {'filename': 'tumor_AA.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.016264077665778878,  \
                             0.021506134465559722,  \
                             0.029906445983839316]},  \
                   {'filename': 'tumor_AB.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.027923530448686402,  \
                             0.024833127103255605,  \
                             0.007059324704916185]},  \
                   {'filename': 'tumor_AC.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.020319577626017805,  \
                             0.01716110504922917,  \
                             0.020753683510286818]},  \
                   {'filename': 'tumor_AD.obj',  \
                    'organ_file': 'surface_A.stl',  \
                    'size': [0.026126939391787878,  \
                             0.011075890551546405,  \
                             0.023287230519771194]}]
    args.outdir = 'data/many_tumors_2/000000'
    args.random_seed = 1


    print("Running scene generation with arguments:")
    p = pprint.PrettyPrinter(depth=4)
    p.pprint(vars(args))
    
    rnd = random.Random()
    rnd.seed(args.random_seed)
    
    try:
        generate_laparoscopic_scene.generate_scene(args, rnd, outdir=args.outdir)
    except Exception as e:
        print(e)
        print(traceback.format_exc())