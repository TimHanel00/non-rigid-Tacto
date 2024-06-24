import os
import time

from core.objects.sceneobjects import DeformableOrgan
from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
from utils.vtkutils import calc_mesh_size
from utils import meshutils
from utils import vtkutils
import sys
import core.io
import re
import sys

# Add the directory to the Python path
import Sofa.Simulation
import SofaRuntime, Sofa.Core,Sofa

# Pipeline block
class SimulationBlock(PipelineBlock):
    """Simulation block, launching the specified simulation class.
    """
    def __init__(self, 
        simulation_filename: str, 
        surface_filename: str, 
        output_filename: str,  
        simulation_class: Sofa.Core.Controller, # or other simulation classes that we will handle
        gravity: tuple = (0.0, 0.0, -9.81),
        dt: float = 0.01,
        export_time: float = -1,
        max_simulation_time: float = 5,
        launch_gui: bool = False,
        max_time_before_timeout: float = 600,
        min_allowed_surface_area: float = 0.0,   # 0.0006 in old pipeline
        max_area_change_ratio: float = 1.5,
        min_allowed_deformation: float = 0.0,  # 0.01 in old pipeline
        max_allowed_deformation: float = 0.1,
        max_volume_change_ratio: float = 1.5,
        **kwargs
    ) ->None:
        """ 
        Args:
            simulation_filename: Name of the file with the mesh to be used for the simulation, either surface or volume.
            surface_filename: Name of the surface mesh.
            output_filename: Name of the output filename.
                If multiple deformed states will be saved (i.e., export_time is different from -1), 
                the specified output_filename will be complemented with an ID to name an output file for each deformed
                state. The construction of the filename from output_filename and ID is controlled by the sample.
            simulation_class: Simulation classes defining the simulation.
            gravity: gravity force.
            dt: simulation time step.
            export_time: Interval of time after which a new deformed state is saved. Defaults to -1 which indicates that only the last deformed state will be saved.
            max_simulation_time: Maximum allowed time for simulation. If the simulation does not converge within this time, the sample is unstable and marked as invalid. Note that this is not real time, but simulation time. Also see simulation_timeout for a real time timeout
            max_time_before_timeout: Maximum allowed time this block may run on a single sample. Note that using this will make the system less deterministic, because in a given run, this block may receive less computational recourses and thus time out when in other runs, it doesn't.
            min_allowed_surface_area: Minimum allowed surface area for mesh after the simulation.  If area is below,
                simulation is considered to have failed due to excessive compression.
            max_area_change_ratio: Maximum allowed ratio of deformed surface area over initial surface area. If ratio is
                above, simulation is considered to have failed due to excessive expansion of the mesh.
            min_allowed_deformation: Discard sample if none of the points in the mesh have moved this far or more in the
                deformation. Only checked for mesh saved at the end of the simulation.
            max_allowed_deformation: Discard sample if any point in the mesh has moved farther than this in the
                simulation. Checked for all intermediate saved meshes.
            max_volume_change_ratio: Maximum allowed ratio of deformed volume over initial volume. If ratio is above,
                simulation is considered to have failed due to excessive expansion of the mesh.

        """
        self.simulation_class = simulation_class
        self.gravity          = gravity
        self.dt               = dt
        self.export_time      = export_time
        self.max_simulation_time = max_simulation_time
        self.launch_gui       = launch_gui
        self.min_allowed_surface_area = min_allowed_surface_area
        self.max_area_change_ratio = max_area_change_ratio
        self.min_allowed_deformation = min_allowed_deformation
        self.max_allowed_deformation = max_allowed_deformation
        self.max_volume_change_ratio = max_volume_change_ratio

        self.output_filename = output_filename
        self.max_time_before_timeout = max_time_before_timeout

        inputs  = [simulation_filename, surface_filename]
        outputs = [output_filename]

        super().__init__(inputs, outputs)

    def run(self, 
        sample
    ):

        try:            
            Log.log(module="SimulationBlock", severity="INFO", msg="Running simulation...")
            Log.log(module="SimulationBlock", msg="Loading input")

            # Set gravity and time step
            sample.set_config_value(self, "gravity", self.gravity)
            sample.set_config_value(self, "dt", self.dt)

            d = [d for d in sample.scene_objects if type(d) == DeformableOrgan]
            assert len(d) == 1, "To run SimulationBlock, exactly one DeformableOrgan " +\
                    "should be created for every DataSample!"
            sample.add_statistic(self, "young_modulus", d[0].young_modulus)
            sample.add_statistic(self, "poisson_ratio", d[0].poisson_ratio)
            
            # Create scene graph
            if issubclass(self.simulation_class, Sofa.Core.Controller):
                root = Sofa.Core.Node("root")
                #plugins = "SofaImplicitOdeSolver SofaLoader SofaOpenglVisual SofaBoundaryCondition SofaGeneralLoader SofaGeneralSimpleFem CImgPlugin"
                plugins = "SofaImplicitOdeSolver SofaLoader SofaOpenglVisual SofaBoundaryCondition SofaGeneralLoader CImgPlugin"
                root.addObject("RequiredPlugin", pluginName=plugins)
                #urdfNode.addObject('TriangleCollisionModel')
                #urdfNode.addObject('LineCollisionModel')
                #urdfNode.addObject('PointCollisionModel')
                #root.addObject('BruteForceDetection', name='detection')
                #root.addObject('DefaultContactManager', name='response', response='default')
                #root.addObject('MinProximityIntersection', alarmDistance='0.5', contactDistance='0.2')
                
            # Add collision and visualization components if needed
                #urdfNode.addObject('MeshSTLLoader', name='meshLoader', filename='path/to/your/robot_visual.obj')
                #urdfNode.addObject('OglModel', src='@meshLoader', name='visual')
                # Initialize simulation class
                simulation = self.simulation_class(
                    root, 
                    sample,  
                    self.inputs,
                    dt = self.dt,
                    gravity = self.gravity,
                    )
                root.addObject( simulation )
                Sofa.Simulation.init(root)
                # Simulation max time
                simulation_time = 0
                start_time = time.time()
                
                # Output setup
                id = 0
                prev_id = 0

                n_exported_frames = 1
                n_timesteps = 0

                # Launch Sofa GUI
                if self.launch_gui:
                    Log.log(module="SimulationBlock",
                            msg="You have to manually CLOSE SOFA GUI!", severity="WARN")
                    Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
                    Sofa.Gui.GUIManager.createGUI(root, __file__)
                    Sofa.Gui.GUIManager.MainLoop(root)
                    Sofa.Gui.GUIManager.closeGUI()

                else:
                    while root.animate.value == True:
                        Sofa.Simulation.animate(root, root.dt.value)
                        simulation_time += root.dt.value
                        n_timesteps += 1

                        if not self.export_time == -1:
                            id = (simulation_time + 1e-08) // self.export_time

                            # Save file
                            if not id == prev_id:
                                deformed = simulation.get_deformed_mesh()
                                sample.write(self.output_filename, deformed, frame=int(n_exported_frames)) # self.validate_sample depends on this
                                prev_id = id
                                n_exported_frames += 1
                        if simulation_time > self.max_simulation_time:
                            sample.add_statistic(self, "simulation_time", simulation_time)
                            sample.add_statistic(self, "simulation_frames", n_exported_frames)
                            raise SampleProcessingException(self, sample,
                                    f"Sample did not converge within maximum simulation time.")
                        if time.time() - start_time > self.max_time_before_timeout:
                            sample.add_statistic(self, "simulation_time", simulation_time)
                            sample.add_statistic(self, "simulation_frames", n_exported_frames)
                            raise SampleProcessingException(self, sample,
                                    f"Timeout, aborting. Increase 'max_time_before_timeout' if this happens too often.")


                Log.log(module="SimulationBlock", severity="INFO",
                        msg=f"Simulation done after {simulation_time:.3f} simulated seconds.")
                sample.add_statistic(self, "simulation_time", simulation_time)
                sample.add_statistic(self, "simulation_frames", n_exported_frames)

                if self.export_time > simulation_time:
                    msg = "Exported final mesh does not map to the export_time timestep! Simulation finished " + \
                        "faster. See sample.statistics[\"simulation_time\"] for the time point that it maps to."
                    Log.log(severity="WARN", module="SimulationBlock", msg=msg)

                # write out final result
                deformed = simulation.get_deformed_mesh()
                # either: write final mesh as single file
                # when no export time is set or when simulation finishes faster than first export
                write_final_mesh_only = (self.export_time == -1) or (self.export_time > simulation_time)
                if write_final_mesh_only:
                    sample.write(self.output_filename, deformed)
                # or: write final mesh as last part of time series
                # - if export_time < simulation_time: get final equilibrated mesh even between export steps
                elif simulation_time < (prev_id + 1) * self.export_time:
                    sample.write(self.output_filename, deformed, frame=int(prev_id+1))
                self._calc_statistics(sample, deformed)

                # Sofa.Simulation.reset(root)

            else:
                raise NotImplementedError("The provided simulation class has not been implemented yet")


        except AssertionError as e:
            raise SampleProcessingException(self, sample,
                    f"Simulation failed: {e}")

    def _calc_statistics(self, sample, deformed_mesh):
        # number of points on the intraoperative volume
        # we know from the current run() implementation that deformed_mesh will be a vtkUnstructuredGrid
        # -> don't do if isinstance(deformed_mesh, vtkPointSet) to not import vtk here
        num_points = deformed_mesh.GetNumberOfPoints()
        sample.add_statistic(self, "intraop_mesh_num_points", num_points)

        # dimensions (size) of intraoperative object
        size_x, size_y, size_z = calc_mesh_size(deformed_mesh)
        sample.add_statistic(self, "intraop_mesh_size_x", size_x)
        sample.add_statistic(self, "intraop_mesh_size_y", size_y)
        sample.add_statistic(self, "intraop_mesh_size_z", size_z)

    # Todo: remove all regex after merging sim-output-handling branch
    def validate_sample(self,
        sample: core.datasample.DataSample
    ) -> (bool, str):
        """Perform sample validation.

        Checks performed:
        - self intersection
        - surface area increase
        - surface area decrease
        - volume increase
        - maximum allowed deformation
        - minimum allowed deformation

        Returns:
            remains_processable, reason
                * remains_processable: True only if all validation checks are successful
                * reason: explanation for failed validation checks
        """
        # self intersection check
        # convert (potentially cached) meshes
        name, _ = os.path.splitext(self.output_filename)
        sample.convert_all(self.output_filename, ".stl")
        # write to disk so that meshlib can read the .stl files
        file_pattern = sample.get_formatted_filepattern(name+".stl", all_frames=True)
        sample.flush_data(regex=file_pattern) #f"^{name}.*\.stl$"
        # call to meshlib
        error_found, comment = meshutils.check_self_intersection_all_matches(sample.path, file_pattern)
        if error_found:
            return False, comment

        # surface area, volume and deformation check
        # load initial mesh for comparison
        # surface for surface area comparison
        if "preoperative_area" not in sample.statistics:
            try:
                _, init_surface, _, _, _ = next(sample.read_all(self.inputs[1]))
            except:
                return False, f"Could not load {self.inputs[1]}"
            preoperative_area = vtkutils.calc_surface_area(init_surface)
            # save computed value for future reference
            sample.add_statistic( self, "preoperative_area", preoperative_area)
        else:
            preoperative_area = sample.statistics["preoperative_area"]
        # volume for comparison to max/min allowed deformation
        try:
            _, init_mesh, _, _, _ = next(sample.read_all(self.inputs[0]))
        except:
            return False, f"Could not load {self.inputs[0]}"
        if "preoperative_volume" not in sample.statistics:
            preoperative_volume = vtkutils.calc_volume(init_mesh)
            # save computed value for future reference
            sample.add_statistic( self, "preoperative_volume", preoperative_volume)
        else:
            preoperative_volume = sample.statistics["preoperative_volume"]
        # load meshes after simulation
        deformed_meshes = {filename:mesh for filename,mesh,_,_,_ in sample.read_all(self.output_filename)}
        # it may be necessary at some point to exclude organs of the same type with different scene object IDs
        # check against min deformation only at final step -> find filename of last mesh
        if len(deformed_meshes) == 0:
            return False, (f"No deformed meshes matching {self.output_filename} (also with scene object ID or frame "
                           f"number) could be found!")
        else:
            # this is a filename
            last_file = sample.find_last_file(self.output_filename, deformed_meshes)

        # if block produced a time series, check all meshes
        for filename, mesh in deformed_meshes.items():
            surface = vtkutils.extract_surface(mesh)
            area = vtkutils.calc_surface_area(surface)
            area = area / 2  # quick fix because inner faces introduced by GMSH are counted as well, see issue #122
            # comparisons done here to save computation time of remaining meshes
            # compare to initial surface area
            if area > preoperative_area * self.max_area_change_ratio:
                return False, f"Surface area increased considerably during simulation, from {preoperative_area:.4f} to " +\
                              f"{area:.4f} in {filename}."
            # compare to minimum allowed area
            if area < self.min_allowed_surface_area:
                return False, f"Surface area is too small: {area:.4f}, something went wrong in {filename}."

            # compare to allowed volume increase
            volume = vtkutils.calc_volume(mesh)
            if volume > preoperative_volume * self.max_volume_change_ratio:
                return False, f"Volume increased considerably during simulation, from {preoperative_volume:.4f} to " + \
                       f"{volume:.4f} in {filename}."

            # compare to maximum allowed deformation
            max_deformation = vtkutils.calc_displacement(init_mesh, mesh).GetMaxNorm()
            if max_deformation > self.max_allowed_deformation:
                return False, f"Organ deformed too much during simulation, maximum deformation is {max_deformation:.4f}."
            # compare to minimum allowed deformation only at the end of the simulation
            if filename == last_file:
                if max_deformation < self.min_allowed_deformation:
                    return False, f"Organ did not deform enough during simulation, maximum deformation is {max_deformation:.4f}."

            # save computed values for future reference
            # format the names nicely
            _, frame = sample.extract_file_info(filename)  # extract frame id in time series
            postfix = sample.get_formatted_filename("", frame=frame)[0]
            sample.add_statistic( self, f"intraop_area{postfix}", area)
            sample.add_statistic( self, f"intraop_volume{postfix}", volume)
            sample.add_statistic( self, f"max_deformation{postfix}", max_deformation)

        # Todo: velocity calculation
        # use self.export_time of block
        # if it isn't set (and, if the writing is changed, at the final step) I need to save final simulation time

        return True, ""
