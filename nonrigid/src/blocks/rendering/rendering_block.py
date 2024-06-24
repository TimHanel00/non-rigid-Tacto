import subprocess
import os
import shutil
import json
import yaml
from typing import Optional, List

from numpy import isin

from core.pipeline_block import PipelineBlock
from blocks.scene_objects.scene_object_generator_block import SceneObjectGeneratorBlock
from core.log import Log
from core.exceptions import SampleProcessingException
from core.objects.sceneobjects import *


class RenderingBlock(PipelineBlock):
    """ Renders the scene via Blender
    """

    def __init__(
        self,
        target_object,
        objects_to_render,
        save_blend_file: bool = False,           # Save blender file for debugging purposes, TODO!
        max_time_before_timeout: int = 300,       # in seconds
        use_cpu: bool = False,
        max_num_frames: int = 15,
        simulation_block: PipelineBlock = None
    ) ->None:
        """
        Args:
        """

        if use_cpu:
            self.blender_exec = "blender-softwaregl"
            Log.log(module="RenderingBlock", msg="Rendering on CPU only. If you have access to a GPU, consider passing 'use_cpu = False' to the RenderingBlock. This is likely to speed up rendering by a large factor!" )
        else:
            self.blender_exec = "blender"

        blender_found = shutil.which(self.blender_exec)
        if not blender_found:
            raise RuntimeError(f"Cannot find '{self.blender_exec}', " +\
                    "make sure it is installed and on $PATH!")

        self.max_num_frames = max_num_frames
        self.simulation_block = simulation_block

        inputs = []

        # These images should always be created:
        outputs = ["color.*.png", "depth.*.exr", "normal.*.png"]
        optional_outputs = []

        # Not all objects will always be created, so treat the masks as optional outputs:
        for obj in [target_object] + objects_to_render:
            base,_ = os.path.splitext( obj["filepattern"] )
            filename = f"mask_{base}.*.png"
            optional_outputs.append( filename )

        self.target_object = target_object
        self.objects_to_render = objects_to_render
        self.max_time_before_timeout = max_time_before_timeout   # in seconds

        super().__init__(inputs, outputs, optional_outputs=optional_outputs)

    def run(
        self, 
        sample,
    ):

        num_frames = self.max_num_frames    # Per default, run the maximum number of frames
        # If we know there's a simulation block, then check how many frames this block created for this
        # particular sample, and don't render more than that:
        if self.simulation_block:
            sim_frames = int(sample.get_statistic( self.simulation_block, "simulation_frames" ))
            num_frames = min( sim_frames, num_frames )

        a = [self.blender_exec]
        a += ["--background"]
        a += ["-noaudio"]
        a += ["--threads"]
        a += ["1"]
        a += ["--python-exit-code"]
        a += ["1"]
        a += ["--python"]
        a += ["src/blocks/rendering/render.py"]
        a += ["--"]
        a += ["--random_seed"]
        a += [str(sample.id)]
        a += ["--num_frames"]
        a += [str(num_frames)]
        a += ["--outdir"]
        a += [sample.path]
        #a += ["--filename"]
        #a += [self.output_filename]

        # Add the main target object:
        pattern = sample.get_formatted_filepattern( self.target_object["filepattern"], all_frames = True )
        sample.flush_data( regex = pattern )
        a += ["--object_of_interest", json.dumps(self.target_object)]
        
        # Let each scene object add a parameter telling blender to load and render it.
        for o in self.objects_to_render:
            pattern = sample.get_formatted_filepattern( o["filepattern"], all_frames = True )
            sample.flush_data( regex = pattern )
            a += ["--other_object", json.dumps(o)]

        #msg = "Running blender:\n\t" + " ".join(a).replace("{","'{").replace("}", "}'")
        msg = "Running blender"#)\n\t" + " ".join(a).replace("{","'{").replace("}", "}'")
        Log.log(module="RenderingBlock", msg=msg)
        Log.log(module="RenderingBlock", msg=" ".join(a))
        try:
            p = subprocess.run(a, capture_output=True, text=True, timeout=self.max_time_before_timeout)
            Log.log(module="RenderingBlock", msg=p.stdout)
            if p.stderr != None and len(p.stderr.strip()) > 0:
                Log.log(module="RenderingBlock", severity="ERROR", msg=p.stderr.strip())
        except subprocess.TimeoutExpired as e:
            msg = f"Timeout of {self.max_time_before_timeout} seconds expired."
            if e.stdout:
                out_msg = f"\n\t{e.stdout.strip()}"
                out_msg = out_msg.replace( "\n", "\n\t" )
                msg += out_msg
            if e.stderr:
                err_msg = f"\n\t{e.stderr.strip()}"
                err_msg = err_msg.replace( "\n", "\n\t" )
                msg += err_msg
            raise SampleProcessingException(
                    pipeline_block=self, data_sample=sample, message=msg)

        # Add the log to this sample's output:
        sample.write_log(p.stdout)
        if p.stderr != None and len(p.stderr.strip()) > 0:
            sample.write_log(p.stderr)

        if p.returncode != 0:
            msg = f"Could not render. Blender exit code was {p.returncode}"
            if p.stderr != None and len(p.stderr.strip()) > 0:
                err_msg = f"\n\t{p.stderr.strip()}"
                #err_msg = err_msg.replace( "\\t", "\t" )
                #err_msg = err_msg.replace( "\\n", "\n" )
                err_msg = err_msg.replace( "\n", "\n\t" )
                msg += err_msg
            raise SampleProcessingException(
                    pipeline_block=self, data_sample=sample, message=msg)
        #elif hasattr(p, "stderr") and len(p.stderr) > 0:
            #raise SampleProcessingException(
                    #pipeline_block=self, data_sample=sample, message=p.stderr)


