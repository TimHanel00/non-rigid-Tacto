import os
from typing import Tuple

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
from utils import vtkutils
from .add_surface_noise import add_gauss_noise_to_surface

class AddSurfaceNoiseBlock(PipelineBlock):
    """ 
    Adds noise to surface points.
    """

    def __init__(
        self, 
        input_filename: str = "volume.vtu", 
        output_filename: str = "surface.stl",
        sigma_range: Tuple[float, float] = (0.001, 0.02)
    ) -> None:
        """ 
        Args:
            input_filename: Name of the file with the mesh where noise has to be added. 
                If the previous block produced multiple input files with this name and an ID, multiple matching
                output files will be created.
            output_filename: Name of the file with the noisy surface. If multiple files are generated,
                filenames will carry on the ID of the files they were generated from.
            sigma_range: Range of the possible values for sigma. Will be sampled (uniformly) individually for each sample.
        """
        self.sigma_range = sigma_range

        self.input_filename = input_filename
        self.output_filename = output_filename
        inputs = [input_filename]
        outputs = [output_filename]
        super().__init__(inputs, outputs)

    def run(
        self, 
        sample
    ):

        found_files = False

        s = sample.random.uniform( self.sigma_range[0], self.sigma_range[1] )
        
        for initial_name, initial_mesh, id, frame, _ in sample.read_all(self.inputs[0]):
            found_files = True

            if initial_mesh.GetNumberOfPoints() <= 0:
                raise SampleProcessingException(self, sample, 
                        f"Found no points in {initial_name}")

            surface = add_gauss_noise_to_surface(initial_mesh, sigma=s, rnd=sample.random)

            fname = sample.write(self.output_filename, surface, id=id, frame=frame)

            Log.log(module="AddSurfaceNoiseBlock",
                    msg=f"Saved surface mesh as {fname}")

            # store statistics
            # dimensions (size) of intraoperative object
            size_x, size_y, size_z = vtkutils.calc_mesh_size(surface)
            # format the names nicely
            postfix = sample.get_formatted_filename("", id=id, frame=frame)[0]
            sample.add_statistic( self, f"intraop_noisy_surface_size_x{postfix}", size_x)
            sample.add_statistic( self, f"intraop_noisy_surface_size_y{postfix}", size_y)
            sample.add_statistic( self, f"intraop_noisy_surface_size_z{postfix}", size_z)
            # number of points doesn't change: saved as "intraop_surface_num_points"

        if not found_files:
            raise SampleProcessingException(self, sample,
                                            f"Could not load any mesh from file {self.inputs[0]}")
        # standard deviation for surface noise
        name, _ = os.path.splitext(self.output_filename)
        # TODO: Maybe use a prettier key?
        sample.set_config_value(
                block = self,
                key = f"{name}_sigma",
                value = s )

