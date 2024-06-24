import os, math
from typing import List
import vtk
import numpy

from core.pipeline_block import PipelineBlock
from core.datasample import DataSample
from core.log import Log
from core.exceptions import SampleProcessingException
import utils.vtkutils as vtkutils


class SimpleUSSimulationBlock(PipelineBlock):
    """ Extract partial view of internal structures by intersecting them with a slice
    """

    def __init__(
        self, 
        internal_filenames: List[str],
        surface_filename: str, 
        output_filename: str = "us.obj",
        output_all_internals_filename: str = None,#"preop_internals.obj",
        max_angle: float = math.pi*0.4,
        scan_depth: float = 0.1,
        frames: str = "LAST",
        simulation_block: PipelineBlock = None,
    ) ->None:
        """  
        This block slices through internal_filename from a random position on surface_filename.
        surface_filename can be a partial surface, or the full surface of the object containing internal_filename

        Output is a mesh representing the intersection between the internal_filenames and a plane.
        (In the future, this could be turned into a monochrome image instead)

        TODO: If multiple timestamps exist for internal_filename, the same timestamps will be used to find
        corresponding versions of the surface_filename file. (TODO)

        Args:
            internal_filenames: List of internal files, i.e. tumors/vessels that will be part of the 
            surface_filename: Points from this file will be used to position the simulatec US probe. Note:
                By default, this file itself will _not_ show up in the US scan output. If you want it to show up,
                add it to internal_filenames list as well.
            output_filename: Output mesh file, will contain interesections of internal_filenames and a plane.
            output_all_internals_filename: All internal structures
            angle: Opening angle of the US probe, in radians
            scan_depth: US scan depth, i.e. how deep into the organ the US probe can look (in m)
            frames: Indicates for which frames to calculate the ultrasound. Options: "ALL" to export every
                frame, "LAST" to export only the last frame, "NONE" to ignore any frame info and just use the 
                given file names as they are.
            simulation_block: Must be given in order to figure out the last frame if frames == "LAST".
        """

        parsed_filenames = []
        for filename in internal_filenames:
            id, frame = DataSample.extract_file_info( filename )

            if frame != None:
                msg = f"SimpleUSSimulation Block received '{name}' as input argument, " \
                        "which contains a frame index. Please try without frame!"
                raise ValueError( msg )

            # TODO: Maybe move this extraction to extract_file_info when we've merged with 'main'?
            #base_name, ext = os.path.splitext(filename)
            #if id is not None:
            #    suffix = f"_{id}"
            #else:
            #    suffix = ""

            #base_name = base_name[0:-len(suffix)]        # Strip the suffix
            ## Add the extension:
            #full_filename_without_id = f"{base_name}{ext}"
            #print(full_filename_without_id)
            
            #parsed_filenames.append( {"filename":full_filename_without_id, "id":id} )
            parsed_filenames.append( filename )

        assert len(parsed_filenames) > 0

        self.internal_filenames = parsed_filenames
        self.surface_filename = surface_filename
        self.output_filename = output_filename
        self.output_all_internals_filename = output_all_internals_filename
        self.scan_depth = scan_depth

        self.frames_mode = frames
        if self.frames_mode == "LAST":
            assert simulation_block is not None, "simulation_block must be given when frames == 'LAST'!"
        self.simulation_block = simulation_block

        if frames != "LAST" and frames != "NONE":
            msg = f"Only the 'LAST' and 'NONE' method is currently implemented for 'frames', but received '{frames}'!"
            raise NotImplementedError( msg )

        inputs = parsed_filenames + [surface_filename]
        outputs = [output_filename]
        if self.output_all_internals_filename is not None:
            outputs.append(self.output_all_internals_filename)
        super().__init__(inputs, outputs)

        #print(self.output_all_internals_filename)

    def run(
        self, 
        sample
    ):
        # First, figure out for which frames we want to create US images:
        # ---------------------------------------------------------------

        # If we know there's a simulation block, then check how many frames this block created for this
        # particular sample, and don't render more than that:
        frames = []
        if self.simulation_block and self.frames_mode == "LAST":
            last_frame = int(sample.get_statistic( self.simulation_block, "simulation_frames" ))
            frames.append( last_frame )
        elif self.frames_mode == "NONE":
            frames = [None]

        written_at_least_one_frame = False

        for frame in frames:

            append = vtk.vtkAppendPolyData()

            # Load the current frame version for all of the given datasets:
            for fn in self.internal_filenames:
                #id, f = DataSample.extract_file_info( fn )
                try:
                    _, data, _, _, _ = next( sample.read_all( fn, frame = frame, all_ids=False ) )
                    append.AddInputData( data )
                except StopIteration:
                    pass
            append.Update()
            combined = append.GetOutput()

            if combined.GetNumberOfPoints() > 3:

                # Choose 3 points to build a plane:
                p_id_0 = sample.random.randint( 0, combined.GetNumberOfPoints()-1 )
                p_id_1 = sample.random.randint( 0, combined.GetNumberOfPoints()-1 )
                p_id_2 = sample.random.randint( 0, combined.GetNumberOfPoints()-1 )
                pt_0 = combined.GetPoints().GetPoint( p_id_0 )
                pt_1 = combined.GetPoints().GetPoint( p_id_1 )
                pt_2 = combined.GetPoints().GetPoint( p_id_2 )

                diff_1 = numpy.array( pt_0 ) - numpy.array( pt_1 )
                diff_2 = numpy.array( pt_0 ) - numpy.array( pt_2 )
                normal = numpy.cross( diff_1, diff_2 )
                normal = normal / numpy.linalg.norm( normal )

                plane = vtk.vtkPlane()
                plane.SetOrigin( pt_0 )
                plane.SetNormal( normal )

                cut = vtk.vtkCutter()
                #cut.SetMergePoints( True )
                cut.SetCutFunction( plane )
                cut.SetInputData( combined )
                cut.Update()
                clipped = cut.GetOutput()
                
                
                out_file, _, _ = DataSample.get_formatted_filename( self.output_filename, frame=frame )
                sample.write( out_file, clipped, cache = False )            


                if self.output_all_internals_filename:
                    out_file, _, _ = DataSample.get_formatted_filename( self.output_all_internals_filename,
                            frame=frame )
                    sample.write( out_file, combined, cache = False )            
                written_at_least_one_frame = True

        # Also output a copy of the full preoperative initial state internals:
        append = vtk.vtkAppendPolyData()

        # Load the current frame version for all of the given datasets:
        for fn in self.internal_filenames:
            # TODO: This is hardcoded because I don't have the time to fix it right now.
            # Ideally, I'd much rather remove the "intraop" in the file names, or pass the preop file names
            # to this module
            fn = fn.replace("_intraop","")
            #Log.log(module=self, severity="WARN", msg="reading: " + fn)
            #id, f = DataSample.extract_file_info( fn )
            try:
                # Read exactly one file:
                name, data, _, _, _ = next( sample.read_all( fn, frame = None, all_frames=False, all_ids=False ) )
                #Log.log(module=self, severity="WARN", msg="read: " + str(data.GetNumberOfPoints()))
                append.AddInputData( data )
                #Log.log(module=self, severity="WARN", msg="read: " + name)
            except StopIteration:
                #Log.log(module=self, severity="WARN", msg="not found")
                pass
        append.Update()
        combined = append.GetOutput()
        #Log.log(module=self, severity="WARN",msg="POINTS: "+str(combined.GetNumberOfPoints()))
        if self.output_all_internals_filename is not None:
            out_file, _, _ = DataSample.get_formatted_filename( self.output_all_internals_filename,
                    frame=None )
            sample.write( out_file, combined, cache = False )
            Log.log(module=self, severity="DETAIL",msg="WRITING:"+out_file +" to " + sample.path)

 
        if not written_at_least_one_frame:
            raise SampleProcessingException( self, sample, f"No data found for frames: {frames}!" )



