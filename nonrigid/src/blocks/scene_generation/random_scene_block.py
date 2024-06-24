import subprocess
import os
import shutil
from typing import Optional, List
from subprocess import CalledProcessError
import json

##from numpy import isin

from core.pipeline_block import PipelineBlock
from blocks.scene_objects.scene_object_generator_block import SceneObjectGeneratorBlock
from core.log import Log
from core.exceptions import SampleProcessingException
from core.objects.sceneobjects import *
from .vascusynth_wrapper.vasculature_generator import LiverVasculatureGenerator


class RandomSceneBlock(PipelineBlock):
    """ Generates a random scene
    """

    def __init__(
        self,
        blocks: List[PipelineBlock],
        max_time_before_timeout: int = 300,       # in seconds
        vascusynth_algorithm_params: dict = {},
        vascusynth_map_generation_params: dict = {},
        max_trials_vessel_generation = 10,
    ) ->None:
        """
        Args:
            vascusynth_algorithm_params: Parameters to customise the VasculatureGenerator,
                including algorithm parameters like the cost function exponent and
                physiological parameters like the mean blood viscosity.
            vascusynth_map_generation_params: Parameters to customise the MapGenerator.
            max_trials_vessel_generation: How often VascuSynth is called with the same parameter
                files before quitting.
        """
        # object generation with blender
        blender_found = shutil.which("blender")
        if not blender_found:
            raise RuntimeError("Cannot find 'blender', " +\
                    "make sure it is installed and on $PATH!")

        inputs = []

        outputs = []
        optional_outputs = []

        for block in blocks:
            if isinstance( block, SceneObjectGeneratorBlock ):
                for obj in block.templates:
                    obj_class = obj["obj_class"]
                    params = obj["params"]

                    filename = obj_class.construct_filepattern()
                    if params["ex_likelyhood"] < 1:
                        optional_outputs.append( filename )
                    else:
                        outputs.append( filename )

                    # this will give the same file pattern for all objects
                    # of the same type, but it's the best I can do
                    additional_files = obj_class.name_additional_files()
                    for filename in additional_files:
                        outputs.append(filename)

        self.max_time_before_timeout = max_time_before_timeout   # in seconds

        # vessel tree generation with VascuSynth
        vascusynth_path = os.environ.get("VASCUSYNTH_PATH")
        if not vascusynth_path:
            raise KeyError(r"VASCUSYNTH_PATH environment variable cannot be found! "
                           r"Please set it to specify the path to the VascuSynth executable "
                           r"including the executable name, e.g. "
                           r"'\home\user1\software\vascusynth\VascuSynth'.")
        self.vascusynth_path = vascusynth_path
        self.vascusynth_algorithm_params = vascusynth_algorithm_params
        self.vascusynth_map_generation_params = vascusynth_map_generation_params
        self.max_trials_vessel_generation = max_trials_vessel_generation

        super().__init__(inputs, outputs, optional_outputs=optional_outputs)

    def run(
        self, 
        sample,
    ):

        #####################################################################################
        # Blender scene generation

        a = ["blender"]
        a += ["--background"]
        a += ["-noaudio"]
        a += ["--threads"]
        a += ["1"]
        a += ["--python-exit-code"]
        a += ["1"]
        a += ["--python"]
        a += ["src/blocks/scene_generation/generation_utils/generate_laparoscopic_scene.py"]
        a += ["--"]
        a += ["--random_seed"]
        a += [str(sample.id)]
        a += ["--outdir"]
        a += [sample.path]
        #a += ["--filename"]
        #a += [self.output_filename]

        # Let each scene object add a parameter describing how to build it.
        # This may contain a dictionary including multiple parameters:
        for s in sample.scene_objects:
            args = {"filename":s.filename}
            if len( s.source_file ) > 0:
                # Let blender know to load this source file rather than
                # creating one for this object:
                args["source_file"] = s.source_file
                # Make sure the source file is actually written to disk so
                # blender can read it:
                sample.flush_data( [s.source_file] )

            if type(s) == DeformableOrgan:
                args["size"] = (s.size_x, s.size_y, s.size_z)
                args["add_concavity"] = s.add_concavity
                args["predeform_twist"] = s.predeform_twist
                args["predeform_noise"] = s.predeform_noise
                args["cut_to_fit"] = s.cut_to_fit
                a += ["--add_deformable_organ", json.dumps(args)]
            elif type(s) == AbdominalWall:
                args["outset_amplitude"] = s.outset_amplitude
                args["outset_frequency"] = s.outset_frequency
                a += ["--add_abdominal_wall", json.dumps(args)]
            elif type(s) == FillFat:        # Note: Requires abdominal wall to be present!
                args["fat_amount"] = s.fat_amount
                args["fat_up_vector"] = s.fat_up_vector
                a += ["--add_fill_fat", json.dumps(args)]
            elif type(s) == Ligament:
                a += ["--add_ligament", json.dumps(args)]
            elif type(s) == FixedAttachments:
                args["surface_amount"] = s.surface_amount
                a += ["--add_fixed_attachments", json.dumps(args)]
            elif type(s) == RigidOrgan:
                args["rigid_transform"] = s.rigid_transform
                a += ["--add_rigid_organ", json.dumps(args)]
            elif type(s) == Force:
                args["magnitude"] = s.magnitude
                if not s.ang_from_normal is None:
                    args["ang_from_normal"] = s.ang_from_normal
                a += ["--add_nodal_force", json.dumps(args)]
            elif type(s) == Tumor:
                args["organ_file"] = s.organ_file
                args["size"] = (s.size_x, s.size_y, s.size_z)
                a += ["--add_tumor", json.dumps(args)]

        #msg = "Running blender:\n\t" + " ".join(a).replace("{","'{").replace("}", "}'")
        msg = "Running blender"#)\n\t" + " ".join(a).replace("{","'{").replace("}", "}'")
        Log.log(module="RandomSceneBlock", msg=msg)
        sample.write_log_new_subsection("blender")
        try:
            p = subprocess.run(a, capture_output=True, text=True, timeout=self.max_time_before_timeout)
            # Check if running was successful:
            # Note that the returncode is only != 0 because --python-exit-code 1 was set above, otherwise we
            # would not be notified about any issues.
            if p.returncode != 0:
                # Pass on the error.
                # (Note: The error ends up in stdout rather than stderr. This is somewhat ugly, but better then
                # nothing...)
                msg = f"Could not create scene. Blender exit code was {p.returncode}"
                print(p.stderr)
                print(p.stdout)
                if p.stderr != None:
                    err_msg = f"\n\t{p.stdout}"
                    err_msg += f"\n\t{p.stderr}"
                    err_msg = err_msg.replace( "\n", "\n\t" )
                    msg += err_msg
                    print(p.stderr)
                    print(p.stdout)
                    print('')
                    print('')
         
                raise SampleProcessingException(
                        pipeline_block=self, data_sample=sample, message=msg)

            Log.log(module="RandomSceneBlock", msg=p.stdout)
        except subprocess.TimeoutExpired:
            msg = f"Timeout of {self.max_time_before_timeout} seconds expired."
            raise SampleProcessingException(
                    pipeline_block=self, data_sample=sample, message=msg)

        # Add the log to this sample's output:
        sample.write_log(p.stdout)

        if p.returncode != 0:
            msg = f"Could not generate surface mesh. Blender exit code was {p.returncode}"
            if p.stderr != None:
                err_msg = f"\n\t{p.stdout}"
                err_msg += f"\n\t{p.stderr}"
                #err_msg = err_msg.replace( "\\t", "\t" )
                #err_msg = err_msg.replace( "\\n", "\n" )
                err_msg = err_msg.replace( "\n", "\n\t" )
                msg += err_msg
            raise SampleProcessingException(
                    pipeline_block=self, data_sample=sample, message=msg)
        elif hasattr(p, "stderr") and len(p.stderr) > 0:
            # TODO: remove when Blender on ceph is working as expected, quick and dirty fix
            if '/run/user' not in p.stderr and 'gvfs' not in p.stderr:
                # end TODO
                raise SampleProcessingException(
                    pipeline_block=self, data_sample=sample, message=p.stderr)


        #####################################################################################
        # Vasculature generation
        msg = "Setting up vasculature generation"
        Log.log("RandomSceneBlock", msg=msg, severity="INFO")

        # if the type of one of the scene objects or several is vessel:
        # collect them and pass to generation (VascuSynth generates >1 vessel trees in parallel)
        vessel_scene_objects = []
        for s in sample.scene_objects:
            if isinstance(s, Vasculature):
                vessel_scene_objects.append(s)
        Log.log("RandomSceneBlock", "here"+str(len(vessel_scene_objects)), severity="INFO")
        # find organ scene object that vasculature should be generated into, make sure there is only one
        if len(vessel_scene_objects)!=0:
            referenced_organs = []
            for vessel in vessel_scene_objects:
                containing_organs = sample.find_scene_object(tag=vessel.structure_tag)
                if containing_organs is not None:
                    # function is written such that only one organ is given back if invoked with tag kwarg
                    referenced_organs.append(containing_organs[0])
                else:
                    msg = (f"Organ tag {vessel.structure_tag} referenced by vessel {vessel.filename}"
                        f" (tag: {vessel.tag}) could not be found in sample {sample.id}.")
                    raise SampleProcessingException(self, sample, msg)
            Log.log("RandomSceneBlock", "here1", severity="INFO")
            # currently, all vessels have to be generated into the same organ
            if len(set(referenced_organs)) > 1:
                organ_filenames = [organ.filename for organ in referenced_organs]
                msg = (f"Vessels can only be generated into one organ at this point but several files are "
                    f"specified: {organ_filenames}")
                raise SampleProcessingException(self, sample, msg)
            Log.log("RandomSceneBlock", "here2", severity="INFO")
            try:
                self.generate_vessels(sample, referenced_organs[0], vessel_scene_objects)
            except Exception as e:
                #raise SampleProcessingException(self, sample, e.args[0])
                msg = f"Unexpected error, not handled yet: {str(e)}"
                raise SampleProcessingException(self, sample, message=msg)
            Log.log("RandomSceneBlock", "here3", severity="INFO")
    def generate_vessels(self, sample, organ_scene_object, vessel_scene_objects):

        msg = "Initializing VasculatureGenerator"
        Log.log("RandomSceneBlock", msg=msg, severity="INFO")

        # set up algorithm parameters
        generator = LiverVasculatureGenerator(self.vascusynth_path,
                                              organ_scene_object,
                                              vessel_scene_objects,
                                              rng=sample.random,
                                              **self.vascusynth_algorithm_params,
                                              )

        # generate oxygen demand map and supply map from the containing organ object
        containing_organ = sample._read(organ_scene_object.filename)
        msg = "Generating demand maps"
        Log.log("RandomSceneBlock", msg=msg, severity="INFO")
        demand_map, supply_map = generator.generate_demand_maps(containing_organ,
                                                                **self.vascusynth_map_generation_params)
        sample.write(organ_scene_object.filename_oxygen_demand_map, demand_map)
        sample.write(organ_scene_object.filename_supply_map, supply_map)
        files_to_be_flushed = [organ_scene_object.filename_oxygen_demand_map,
                               organ_scene_object.filename_supply_map]

        # parameterize the vessel trees
        # if applicable, read an inferior vena cava object that can be used to place
        # perforation points
        msg = "Parametrizing vascular trees"
        Log.log("RandomSceneBlock", msg=msg, severity="INFO")
        if organ_scene_object.perforation_placement_aid_file:
            perforation_placement_aid = sample._read(organ_scene_object.perforation_placement_aid_file)
            parameter_files = generator.parametrize_vascular_trees(inferior_vena_cava_obj=perforation_placement_aid,
                                                                   sample_directory=sample.path,
                                                                   random_seed=sample.id)
        else:
            parameter_files = generator.parametrize_vascular_trees(sample_directory=sample.path,
                                                                   random_seed=sample.id)

        for filename, param_file in parameter_files.items():
            sample.write(filename, param_file)
            files_to_be_flushed.append(filename)

        # flush all those files so VascuSynth can read them
        msg = f"Flushing: {files_to_be_flushed}"
        Log.log("RandomSceneBlock", msg=msg, severity="INFO")
        sample.flush_data(files_to_be_flushed)

        # call VascuSynth
        sample.write_log_new_subsection("VascuSynth")
        for i in range(self.max_trials_vessel_generation):
            try:
                msg = f"VascuSynth call trial {i}"
                Log.log(module="RandomSceneBlock", msg=msg, severity="INFO")
                stdout, stderr = generator.generate_structure(sample.id, sample_directory=sample.path)

                output = f"Subprocess stdout:\n{stdout}\n"
                output += f"Subprocess stderr:\n{stderr}\n"
                sample.write_log(msg + '\n' + output)
                break
            except CalledProcessError as err:
                stdout = err.stdout
                stderr = err.stderr


                output = f"Subprocess stdout:\n{stdout}\n"
                output += f"Subprocess stderr:\n{stderr}\n"
                sample.write_log(msg + '\n' + output)

                # log and try again until max number of trials is reached, then:
                if i + 1 == self.max_trials_vessel_generation:
                    err_msg = (f"Could not generate vasculature into the organ {organ_scene_object.filename}. "
                           f"Vascusynth did not provide a result within the specified "
                           f"{self.max_trials_vessel_generation} trials. See log file for subprocess "
                               f"stdout and stderr.\n")

                    raise SampleProcessingException(pipeline_block=self, data_sample=sample,
                                                    message=err_msg)

            #except Exception as err:
            #    err_msg = f"Could not generate vascula"
            #    raise SampleProcessingException(pipeline_block=self, data_sample=sample,
            #                                    message=err_msg)


        # 3D model construction from VascuSynth's XML structural information
        msg = "Reading in generated tree structures"
        Log.log("RandomSceneBlock", msg=msg, severity="INFO")
        trees = []
        for vessel in vessel_scene_objects:
            tree = sample._read(vessel.filename_tree_struct_intermediate)
            trees.append((vessel, tree))

        msg = "Generating 3D models"
        Log.log("RandomSceneBlock", msg=msg, severity="INFO")
        tree_models = generator.generate_3D_representation(trees)

        # save 3D models
        for filename, tree in tree_models.items():
            sample.write(filename, tree)

        # save structure information
        # trees are updated by generator.generate_3D_representation()!
        # -> need to store all info
        for vessel, tree in trees:
            sample.write(vessel.filename_structure, tree)

        # todo for validation
        # save root positions for future reference (as boundary condition)
        # can sample.statistics have root positions (tuple of 3 floats)?
        # or should they be saved in the scene objects?



