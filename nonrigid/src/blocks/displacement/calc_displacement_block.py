import os
from typing import Optional

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
import utils.vtkutils as vtkutils


class CalcDisplacementBlock(PipelineBlock):
    """
    After (rigid or non-rigid) displacement, this block calculates the resulting displacement between two meshes. 
    """

    def __init__(
        self, 
        initial_mesh_filename: str, 
        displaced_mesh_filename: str,
        corresponding_indices: Optional[list]=None,
        output_filename: str = "displacement.vtu",
    ) ->None:
        """  
        The block take a single input mesh and up to N displaced meshes. It computes the displacement between the displaced
        mesh/es and the input mesh. The output is a single mesh with all the computed displacement arrays.
        In case multiple displacement arrays are computed, saved statistics are relative to the last sample.

        Args:
            initial_mesh_filename: Name of the file with the mesh in its initial state. A single initial mesh is supported
                (no multiple files).
            displaced_mesh_filename: Name of the file with the displaced mesh. If multiple displaced meshes are given
                - i.e. the previous block produced multiple input files with this name and an ID -
                a displacement array will be created for each displaced mesh that computes its displacement with
                respect to the provided initial mesh. In this case the IDs are carried on to the name of the displacement
                arrays.
            corresponding_indices: For each point in displaced_mesh_filename, it contains the index of the corresponding
                point in initial_mesh_filename, that will be used for displacement calculation. This input allows to calculate
                displacement in case of displaced surfaces which are a portion of the initial surface. If multiple displaced meshes
                are present, corresponding_indices must be a list of lists. 
                If None, it is assumed that initial_mesh has the same number of points as displaced_mesh. Thus, it assumes 
                correspondence between the points in the initial and displaced meshes, i.e. point 1 corresponds to point 1, point 2 to point 2 and so on.
            output_filename: Name of the output file. It will contain the input mesh with an associated "displacement" array. 
                Note that a single file will be created also in case multiple displaced mesh are provided. In this case, the file will
                include all the displacement arrays, saved as "displacement{postfix}", where different ids and frame
                indices in the postfix correspond to different displaced_mesh.
        """

        self.initial_mesh_filename = initial_mesh_filename
        self.displaced_mesh_filename = displaced_mesh_filename
        self.corresponding_indices = corresponding_indices
        self.output_filename = output_filename

        inputs = [self.initial_mesh_filename, self.displaced_mesh_filename]
        outputs = [output_filename]
        super().__init__(inputs, outputs)

    def run(
        self, 
        sample
    ):
        # Load the initial mesh
        initial_mesh_list = list(sample.read_all(self.initial_mesh_filename))

        if len(initial_mesh_list) == 0:
            raise SampleProcessingException(self, sample,
                                            f"Could not load mesh from file {self.initial_mesh_filename}")
        elif len(initial_mesh_list) > 1:
            raise SampleProcessingException(self, sample,
                                            f"Expected one file matching {self.initial_mesh_filename},"
                                            f" found {len(initial_mesh_list)}")
        initial_mesh = initial_mesh_list[0][1]

        if initial_mesh.GetNumberOfPoints() <= 0:
            raise SampleProcessingException(self, sample, 
                    f"Found no points in {self.initial_mesh_filename}")

        initial_mesh = vtkutils.polyDataToUnstructuredGrid(initial_mesh)

        # Load the displaced meshes
        files_found = False

        for displaced_name, displaced_mesh, id, frame, _ in sample.read_all(self.displaced_mesh_filename):
            files_found = True
            if displaced_mesh.GetNumberOfPoints() <= 0:
                raise SampleProcessingException(self, sample, 
                        f"Found no points in {displaced_name}")

            # Setup displacement array name
            displacement_array      = "displacement"
            displacement_array, _, _ = sample.get_formatted_filename(displacement_array, id=id, frame=frame)
            if frame is None:
                frame = 1  # still needed for corresponding indices array indexing

            displaced_mesh = vtkutils.polyDataToUnstructuredGrid(displaced_mesh)

            # Todo raise issue for this: only works if frames are 1 apart
            indices = self.corresponding_indices[int(frame)-1] if self.corresponding_indices is not None else None
            displacement_arr = vtkutils.calc_displacement(initial_mesh, displaced_mesh, indices)
            displacement_arr.SetName(displacement_array)
            
            initial_mesh.GetPointData().AddArray(displacement_arr)

        if not files_found:
            raise SampleProcessingException(self, sample,
                        f"Could not load any mesh from file {self.displaced_mesh_filename}")

        mean_displacement_name = "mean_displacement"
        max_displacement_name  = "max_displacement"
        _, maximum, mean = vtkutils.calc_array_stats( displacement_arr )
        sample.add_statistic( self, mean_displacement_name, mean )
        sample.add_statistic( self, max_displacement_name, maximum )
        
        sample.write(self.output_filename, initial_mesh)

        Log.log(module="CalcDisplacementBlock",
                msg=f"Saved displacement as {self.output_filename}")


