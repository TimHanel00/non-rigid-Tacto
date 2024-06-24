import os
import subprocess
import shutil

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException

class CleanMeshBlock(PipelineBlock):

    def __init__(self,
            input_filename:str="surface.stl",
            output_filename:str="surface_cleaned.stl",
            target_verts:int=2000
    ):


        blender_found = shutil.which("blender")
        if not blender_found:
            raise RuntimeError("Cannot find 'blender', " +\
                    "make sure it is installed and on $PATH!")


        self.input_filename = input_filename
        self.output_filename = output_filename
        self.target_verts = target_verts

        inputs = [input_filename]
        outputs = [output_filename]
        super().__init__(inputs, outputs)

    def run(self, sample):

        # Because we want blender to open the file, make sure it's saved to disk:
        sample.flush_data(filenames=[self.input_filename])

        infile = os.path.join(sample.path, self.input_filename)
        outfile = os.path.join(sample.path, self.output_filename)

        a = ["blender"]
        a += ["--background"]
        a += ["-noaudio"]
        a += ["--threads"]
        a += ["1"]
        a += ["--python"]
        a += ["src/blocks/scene_generation/generation_utils/clean_mesh.py"]
        a += ["--"]
        a += ["--infile"]
        a += [infile]
        a += ["--outfile"]
        a += [outfile]
        a += ["--remesh"]
        a += ["--target_verts"]
        a += [str(self.target_verts)]
        msg = "Running mesh cleaning in Blender:\n\t" + " ".join(a)
        Log.log(module="CleanMeshBlock", msg=msg)
        p = subprocess.run(a, capture_output=True, text=True)
        Log.log(module="CleanMeshBlock", msg=p.stdout)

        # Check if running was successful:
        # Note that the returncode is only != 0 because --python-exit-code 1 was set above, otherwise we
        # would not be notified about any issues.
        if p.returncode != 0:
            # Pass on the error.
            # (Note: The error ends up in stdout rather than stderr. This is somewhat ugly, but better then
            # nothing...)
            msg = f"Could not clean mesh. Blender exit code was {p.returncode}"
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
            raise SampleProcessingException(
                    pipeline_block=self, data_sample=sample, message=p.stderr)

        # Add the log to this sample's output:
        sample.write_log(p.stdout)

