import math
from enum import Enum
import vtk

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
import utils.vtkutils as vtkutils

class RigidDisplacementMode(Enum):
    center = 0
    from_memory = 1
    random = 2
    constant = 3

class RotationMode(Enum):
    mean = 0
    bb_center = 1
    random = 2
    origin = 3

class RigidDisplacementBlock(PipelineBlock):
    """ Apply a rigid displacement to the sample (i.e., translation and/or rotation).

    Three possible rigid displacements can be applied:
    1. random (combination of translation and rotation)
    2. centering 
    3. applying a transform from a given file.
    """

    def __init__(
            self,
            input_filename: str,
            output_filename: str,
            mode: RigidDisplacementMode = RigidDisplacementMode.random,
            max_translate: float = 0,
            max_rotate: float = 0,
            rotation_center: RotationMode = RotationMode.mean,
            transform_name: str = "rigid_transform",
            transform:vtk.vtkMatrix4x4 = None
    ) ->None:
        """ Rigid displacement is added to input_filename and output saved as output_filename.

        Args:
            input_filename: Name of the file with the mesh to be rigidly displaced. 
                If the previous block produced multiple input files with this name and an ID, multiple matching
                output files will be created.
            output_filename: Name of the file with the output mesh. If multiple files are generated,
                filenames will carry on the ID of the files they were generated from.
            mode: The type of rigid displacement to be applied, from RigidDisplacementMode.
            max_translate: The maximum allowed, randomly sampled translation.
            max_rotate: The maximum allowed rotation about an arbitrary axis (in radians).
            rotation_center: The center to consider for rotation, from RotationMode.
                'mean': use mean position as rotation center
                'bb_center': use the center of the bounding box as rotation center
                'random': use a random position within the bounding box as rotation center
                'origin': rotate around (0,0,0) 
            transform_name: The name of the transform to read from/write to config.
                Note: This will be written if mode is 'random' or 'center'. If mode is
                'from_memory', this value will be read and re-used from a previous file.
        """
        assert rotation_center == RotationMode.mean or \
                rotation_center == RotationMode.origin,\
                "Only ORIGIN and MEAN rotation modes currently implemented"

        self.input_filename = input_filename 
        self.rotation_center = rotation_center
        self.max_translate = max_translate
        self.max_rotate = max_rotate
        self.transform_name = transform_name
        self.output_filename = output_filename
        self.transform = transform
        self.mode = mode

        if self.mode == RigidDisplacementMode.constant:
            assert self.transform != None, \
                "Must supply a transform if displacement mode is 'constant'!"

        inputs = [self.input_filename]
        outputs = [self.output_filename]
        super().__init__(inputs, outputs)

    def run(
        self, 
        sample
    ):

        Log.log(module="RigidDisplacementBlock", msg="Loading input")
        found_files = False

        for initial_name, initial_mesh, id, frame, _ in sample.read_all(self.inputs[0]):
            found_files = True

            if initial_mesh.GetNumberOfPoints() <= 0:
                raise SampleProcessingException(self, sample, 
                        f"Found no points in {initial_name}")

            #initial_mesh = vtkutils.polyDataToUnstructuredGrid(initial_mesh)

            if self.mode == RigidDisplacementMode.random:

                rot_center = [0,0,0]       # Default: rotate around origin
                if self.rotation_center == RotationMode.mean:
                    rot_center = vtkutils.calc_mean_position(initial_mesh)
                # Create a random rigid transformation, using the given rotation center
                # for any rotation:
                tf = vtkutils.create_random_rigid_transform(
                        max_rotation = self.max_rotate/math.pi*180,
                        max_translation = self.max_translate,
                        rot_center = rot_center,
                        rnd = sample.random )
            elif self.mode == RigidDisplacementMode.center:
                # Calculate how this mesh would be centered:
                tf = vtkutils.calc_center_transform(initial_mesh)
            elif self.mode == RigidDisplacementMode.from_memory:
                # Get a previously stored transform:
                tf_str = sample.get_config_value(self, self.transform_name)
                tf = vtkutils.transform_from_str(tf_str)
            elif self.mode == RigidDisplacementMode.constant:
                tf = vtkutils.transform_from_str(self.transform)
        
            # Apply the transform to the mesh:
            displaced_mesh = vtkutils.apply_transform(initial_mesh, tf)

            sample.write(self.output_filename, displaced_mesh, id=id, frame=frame)

            if not self.mode == RigidDisplacementMode.from_memory:
                # Store the transform for later use:
                sample.set_config_value(self, self.transform_name,
                        vtkutils.transform_to_str(tf))

            # store statistics
            # dimensions (size) of intraoperative object
            size_x, size_y, size_z = vtkutils.calc_mesh_size(displaced_mesh)
            # format the names nicely
            postfix = sample.get_formatted_filename("", id=id, frame=frame)[0]
            sample.add_statistic(self, f"intraop_volume_displaced_size_x{postfix}", size_x)
            sample.add_statistic(self, f"intraop_volume_displaced_size_y{postfix}", size_y)
            sample.add_statistic(self, f"intraop_volume_displaced_size_z{postfix}", size_z)
            # number of points doesn't change: saved as "intraop_volume_num_points"

        if not found_files:
            raise SampleProcessingException(self, sample,
                    f"Could not load any mesh from file {self.inputs[0]}")


