import os

from vtk import vtkPointInterpolator, vtkGaussianKernel, vtkWarpVector

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
from utils import vtkutils

class ApplyDisplacementBlock(PipelineBlock):
    """ Given a mesh A and another mesh B apply the displacement in B to the mesh A

    This Block assumes that mesh B has at least one vtkPointArray that has a name starting with "dispalcement".
    This array should contain a displacement vector for every point in mesh B. (Note: These kind of arrays can
    be created via the CalcDisplacementBlock).
    A point P from mesh A is then displaced by sampling these displacement field arrays at the position of P.
    Note that for this to work, all points in mesh A should lie inside (or very close to) mesh B.

    Internally, we use the vtkPointInterpolator class. Please see the vtk documentation for details.
        """

    def __init__(
        self, 
        input_filename: str = "surface_patch.stl",
        input_displacement_filename: str = "preop_volume_with_displacement.vtu", 
        output_filename: str = "surface_patch_displaced.stl",
        radius: float = 0.01,
        sharpness: float = 10,
    ) ->None:
        """  
        Args:
        """
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.input_displacement_filename = input_displacement_filename
        self.radius = radius
        self.sharpness = sharpness

        _, ext = os.path.splitext( input_displacement_filename )
        assert ext == ".vtu" or ext == ".vtk" or ext == ".vts" or ext == ".vtp", \
                "Supported file types for input_displacement_filename are: .vtu, .vtk, .vts, .vtp"

        self.output_basename, self.output_extension = os.path.splitext( self.output_filename )

        inputs = [input_filename, input_displacement_filename]
        outputs = [f"{self.output_basename}.*{self.output_extension}"]

        super().__init__(inputs, outputs)

    def run(
        self, 
        sample
    ):
        found_displacement_fields = False
        found_files = False

        for displacement_mesh_name, displacement_mesh, id, _, _ in sample.read_all(
                                                                        self.input_displacement_filename):

            # Displacement field arrays:
            displacement_fields = []
            for i in range( displacement_mesh.GetPointData().GetNumberOfArrays() ):
                array_name = displacement_mesh.GetPointData().GetArray(i).GetName()
                if array_name.startswith( "displacement" ):
                    displacement_fields.append( array_name )
            Log.log(module=self, msg=f"Loaded: {displacement_mesh_name}")
            Log.log(module=self, msg=f"\tFound displacement fields: {displacement_fields}")
            if len(displacement_fields) > 0:
                found_displacement_fields = True

            interpolator = vtkPointInterpolator()
            gaussian_kernel = vtkGaussianKernel()
            gaussian_kernel.SetRadius( self.radius )
            gaussian_kernel.SetSharpness( self.sharpness )
            interpolator.SetSourceData( displacement_mesh )
            interpolator.SetKernel( gaussian_kernel )
            # If a point falls outside the mesh, we can't "interpolate" the displacement field at this point.
            # The NullPointsStrategy tells vtk how to handle this case:
            interpolator.SetNullPointsStrategy(vtkPointInterpolator.CLOSEST_POINT)

            # Iterate over all the meshes we want to displace and calculate the interpolated displacement field for them
            for initial_name, initial_mesh, id, frame, _ in sample.read_all(self.input_filename):
                found_files = True

                if initial_mesh.GetNumberOfPoints() <= 0:
                    raise SampleProcessingException(self, sample, 
                            f"Found no points in {initial_name}")
           
                n_points = initial_mesh.GetNumberOfPoints()
                Log.log(module=self, msg=f"\tMorphing {initial_name} ({n_points} points)")

                interpolator.SetInputData( initial_mesh )
                interpolator.Update()
                interpolated = interpolator.GetOutput()
                
                # Apply the displacement:
                warp = vtkWarpVector()
                warp.SetInputData( interpolated )
                warp.SetScaleFactor( 1 )
               

                # Apply every displacement field to the input, save every result:
                for displacement_field in displacement_fields:
                    Log.log(module=self,
                            msg=f"Warping input mesh {initial_name} by displacement field {displacement_field}")
                    max_displ = displacement_mesh.GetPointData().GetArray(displacement_field).GetMaxNorm()
                    max_displ_tgt = interpolated.GetPointData().GetArray(displacement_field).GetMaxNorm()
                    Log.log(module=self, msg=f"Displacement: {max_displ} tgt: {max_displ_tgt}")

                    interpolated.GetPointData().SetActiveVectors( displacement_field )
                    warp.Update()

                    displaced = warp.GetOutput()

                    points = initial_mesh.GetPoints()
                    points_all = 0
                    for i in range(points.GetNumberOfPoints()):
                        pt = points.GetPoint(i)
                        points_all += sum(pt)
                    points = displaced.GetPoints()
                    points_all_tgt = 0
                    for i in range(points.GetNumberOfPoints()):
                        pt = points.GetPoint(i)
                        points_all_tgt += sum(pt)
                    
                    Log.log(module=self, msg=f"Pos: {points_all} tgt: {points_all_tgt}")

                    # Write output:
                    _, displacement_frame = sample.extract_file_info( displacement_field )
                    output_filename = f"{self.output_basename}{self.output_extension}"
                    # displacemnt_frame may be None, but the following function should be able to deal with this:
                    full_output_filename = sample.write( output_filename, displaced, frame=displacement_frame )
                    n_points = displaced.GetNumberOfPoints()
                    Log.log(module=self, msg=f"\tMorphed: {output_filename} ({n_points} points)")

                    Log.log(module=self,
                            msg=f"\tSaved surface mesh as {full_output_filename}")

        # TODO: Unlike other blocks, this block does _not_ fail if the input files are not found, because
        # it needs to be usable also on objects which may not exist for a particular sample.
        # This is inconsistent. Once we have a better reference system between scene objects, we might be able
        # to clean this up by passing in scene object tags and then checking whether the scene object has
        # been created for this particular sample
        if not found_displacement_fields:
            Log.log(module=self, severity="WARN",
                msg = f"{self} skipped, displacement fields {self.input_displacement_filename} found for sample {sample.id}")

        if not found_files:
            Log.log(module=self, severity="WARN",
                msg = f"{self} skipped, no files matching {self.input_filename} found for sample {sample.id}")
            #raise SampleProcessingException(self, sample,
            #        f"Could not load any mesh from file {self.inputs[0]}")

    def interpolate():
        if not radius:
            radius = cellSize * 5
        
        # Perform the interpolation

        #output = interpolator.GetOutput()
        output = vtkStructuredGrid()
        output.DeepCopy(interpolator.GetOutput())
        del interpolator, gaussianKernel
        return output
     

