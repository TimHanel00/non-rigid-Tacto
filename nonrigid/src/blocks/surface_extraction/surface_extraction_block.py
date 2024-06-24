import os

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
from utils import vtkutils
from .extract_surface import random_surface

class SurfaceExtractionBlock(PipelineBlock):
    """ Extract a partial surface from the given mesh. """

    def __init__(
        self, 
        input_filename: str = "intraop_volume.vtu", 
        output_filename: str = "partial_intraop_surface.stl",
        surface_amount: tuple = (0.0, 1.0),
        w_distance: tuple = (1, 1),
        w_normal: tuple = (1, 1),
        w_noise: tuple = (1, 1),
    ) ->None:
        """  
        Args:
            input_filename: Name of the file with the mesh where a partial surface must be extracted. 
                If the previous block produced multiple input files with this name and an ID, multiple matching
                output files will be created.
            output_filename: Name of the file with the extracted surface. If multiple files are generated,
                filenames will carry on the ID of the files they were generated from.
            surface_amount: tuple with min and max allowed surface amount (as percentage of the total surface area,
                between 0 and 1). If multiple partial surfaces are extracted in the same sample (i.e., multiple
                input files are given), then a different percentage of surface is extracted for each input mesh.
            w_distance (tuple(float)):
                Influence of the geodesic distance of a point to the center point c.
                If this value is > 0 and the other weights are == 0, only the distance will be
                taken into account. Tuple must contain exactly two values: min and may
            w_normal (tuple(float)):
                Influence of the angle between normals.
                If this value is > 0 and the other weights are == 0, only points with a similar
                normal as the center point will be selected.
                Tuple must contain exactly two values: min and may
            w_noise (tuple(float)):
                Influence of the highest noise.
                If this value is > 0 and the other weights are == 0, entirely random parts of the
                surface will be selected.
                Tuple must contain exactly two values: min and may
        """
        self.surface_amount = surface_amount
        self.extracted_indices = []

        self.input_filename = input_filename
        self.output_filename = output_filename

        assert len(w_distance) == 2
        assert len(w_normal) == 2
        assert len(w_noise) == 2

        self.w_distance = w_distance
        self.w_normal = w_normal
        self.w_noise = w_noise

        inputs = [input_filename]
        outputs = [output_filename]

        super().__init__(inputs, outputs)

    def run(
        self, 
        sample
    ):
        found_files = False

        for initial_name, initial_mesh, id, frame, _ in sample.read_all(self.inputs[0]):
            found_files = True

            if initial_mesh.GetNumberOfPoints() <= 0:
                raise SampleProcessingException(self, sample, 
                        f"Found no points in {initial_name}")

            # Setup output filename and partial surface array name
            target_surface_name = "target_surface_amount"
            partial_surface_name = "partial_surface_area"  # self.validate_sample() depends on this

            partial_surface_name, _, _ = sample.get_formatted_filename(partial_surface_name, id=id, frame=frame)
            target_surface_name, _, _ = sample.get_formatted_filename(target_surface_name, id=id, frame=frame)

            target_surface_amount = sample.random.uniform(self.surface_amount[0], self.surface_amount[1])
            sample.set_config_value(self, target_surface_name, target_surface_amount)
            w_distance = sample.random.uniform(self.w_distance[0], self.w_distance[1])
            sample.set_config_value(self, "w_distance", w_distance)
            w_noise = sample.random.uniform(self.w_noise[0], self.w_noise[1])
            sample.set_config_value(self, "w_noise", w_noise)
            w_normal = sample.random.uniform(self.w_normal[0], self.w_normal[1])
            sample.set_config_value(self, "w_normal", w_normal)

            full_surface = vtkutils.extract_surface(initial_mesh)

            if full_surface.GetNumberOfPoints() < 3:
                raise SampleProcessingException(self, sample, 
                    f"Surface empty for mesh {self.inputs[0]}")

            if target_surface_amount < 1.0:
                surface = random_surface(full_surface, surface_amount=target_surface_amount,
                        rnd=sample.random,
                        w_distance = w_distance,
                        w_noise = w_noise,
                        w_normal = w_normal )
            else:
                surface = full_surface

            if surface.GetNumberOfPoints() < 3:
                raise SampleProcessingException(self, sample, 
                    f"Surface empty for mesh {self.inputs[0]}")
       
            surface_points = vtkutils.vtk2numpy(surface)
            current_extracted_indices = vtkutils.find_corresponding_indices(initial_mesh, surface_points)
            self.extracted_indices.append(current_extracted_indices)

            # store statistics
            # format the names nicely
            postfix = sample.get_formatted_filename("", id=id, frame=frame)[0]
            # surface ratio
            # Calculate how much area we've actually selected:
            # (might differ slightly from the target_surface_amount!)
            partial_area = vtkutils.calc_surface_area(surface)
            if surface == full_surface:
                # quick fix because inner faces introduced by GMSH are counted as well, see issue #122
                # not used for selected surface because hopefully it's not affected due to selection
                partial_area = partial_area / 2
            # print("partial:", surface.GetNumberOfPoints())
            
            full_area = vtkutils.calc_surface_area( full_surface )
            # quick fix because inner faces introduced by GMSH are counted as well, see issue #122
            full_area = full_area / 2
            sample.add_statistic( self, partial_surface_name, partial_area/full_area )  # self.validate_sample() depends on this

            # number of points on the intraoperative surface
            num_points = surface.GetNumberOfPoints()
            sample.add_statistic( self, f"intraop_surface_num_points{postfix}", num_points)
            # dimensions (size) of intraoperative object
            size_x, size_y, size_z = vtkutils.calc_mesh_size(surface)
            sample.add_statistic( self, f"intraop_surface_size_x{postfix}", size_x)
            sample.add_statistic( self, f"intraop_surface_size_y{postfix}", size_y)
            sample.add_statistic( self, f"intraop_surface_size_z{postfix}", size_z)

            fname = sample.write(self.output_filename, surface, id=id, frame=frame)

            Log.log(module="SurfaceExtractionBlock",
                    msg=f"Saved surface mesh as {fname}")

        if not found_files:
            raise SampleProcessingException(self, sample,
                    f"Could not load any mesh from file {self.inputs[0]}")

    def validate_sample(self,
        sample
    ) -> (bool, str):
        """Perform sample validation.

        Check if the randomized surface extraction process of run() produced a surface area within the
        specified min and max percentages. The extracted area is rounded to the decimal
        places of the respective boundary (e.g. if self.surface_amount[0] is 0.18, a partial surface area
        of 0.179 will be allowed) for tolerance.

        Returns:
            remains_processable, reason
                * remains_processable: True only if all validation checks are successful
                * reason: explanation for failed validation checks
        """
        stats = sample.statistics
        max_amount_decimal_places = str(self.surface_amount[1])[::-1].find('.')
        min_amount_decimal_places = str(self.surface_amount[0])[::-1].find('.')
        # partial surface area is already calculated and saved by self.run()
        # make sure to check all values in the time series
        for stat_name, stat_val in stats.items():
            if "partial_surface_area" in stat_name:
                print(f"Checking statistic {stat_name}")
                if round(stat_val, min_amount_decimal_places) < self.surface_amount[0]:
                    return False, f"Extracted surface area {stat_name} is too small: {stat_val}*initial surface" \
                                  f" instead of {self.surface_amount[0]}."
                elif round(stat_val, max_amount_decimal_places) > self.surface_amount[1]:
                    return False, f"Extracted surface area {stat_name} is too big: {stat_val}*initial surface" \
                                  f" instead of {self.surface_amount[1]}."

        return True, ""
