import os
import subprocess
from math import pi
from inspect import cleandoc
from typing import List, Tuple, Union, Dict, TYPE_CHECKING
from vtk import vtkPolyData

if TYPE_CHECKING:
    import random  # only for typing!

from .vascular_tree import VascularTree, CurvedTree
from .map_generator import MapGenerator
from . import model_generator
from utils.utils import trunc_norm
from utils.vtkutils import calc_volume
from core.objects.sceneobjects import Vasculature, VolumetricOrgan, PortalVein, HepaticVein, HepaticArtery
from core.log import Log


class VasculatureGenerator:
    """
    Generates input parameters for VascuSynth and calls it.

    Two different coordinate systems are used throughout the Code:
    1. The coordinate system of the input OBJ file ("object coordinates")
    2. The (discrete) coordinate system of the oxygen demand map ("ODM coordinates")

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    # pass vessel scene objects
    def __init__(
            self,
            VascuSynth_path: str,
            organ_scene_object: VolumetricOrgan,
            vessel_scene_objects: List[Vasculature],
            gamma_exponent: int = 3,
            lambda_exponent: float = 2.0,
            mu_exponent: float = 1.0,
            num_neighbours: int = 5,
            min_distance: int = 1,
            supply_map_parameters: List[float] = [0.65, 0.34, 0.01, 7],
            rng: 'random.Random' = None,
            viscosity_mu: float = 4.5 * 1e-3,  # cP -> Pa * s (SI unit)
            viscosity_sigma: float = 0.5 * 1e-3,  # cP -> Pa * s (SI unit)
            viscosity_min: float = 3.5 * 1e-3,  # cP -> Pa * s (SI unit)
            viscosity_max: float = 5.5 * 1e-3,  # cP -> Pa * s (SI unit)
    ) -> None:
        """
        Initializes VasculatureGenerator instance.

        Args:
            VascuSynth_path: Path to the VascuSynth executable.
            organ_scene_object: Scene object of the organ to generate vessel trees into.
            vessel_scene_objects: Scene objects describing the vessel trees. These will be
                used to create the parameter files and the call to VascuSynth.
            gamma_exponent: Bifurcation exponent
            lambda_exponent: Cost function exponent
            mu_exponent: Cost function exponent
            num_neighbours: Number of segments to test during optimization
                of the bifurcation location.
            min_distance: Mininum distance between new terminal node and
                existing segments in units of oxygen demand map voxels.
            supply_map_parameters: Parameters for the oxygenation map update function.
            rng: Random number generator of the DataSample. Under no circumstances
                create an own new rng here.
            viscosity_mu: Mean value for the truncated normal distribution of the blood
                viscosity in Pa * s (SI units).
            viscosity_sigma: Standard deviation for the truncated normal distribution of
                the blood viscosity in Pa * s (SI units).
            viscosity_min: Minimum truncation value for the truncated normal distribution
                 of the blood viscosity in Pa * s (SI units).
            viscosity_max: Maximum truncation value for the truncated normal distribution
                 of the blood viscosity in Pa * s (SI units).
        """

        # setup
        self.VascuSynth_path = VascuSynth_path
        self.organ_scene_object = organ_scene_object
        self.vessel_scene_objects = vessel_scene_objects

        # initialize info needed from the MapGenerator
        self._map_generator = None
        self._perf_points = None
        self._voxel_width_ODM = 1.0

        # Algorithm Parameters
        self.gamma_exponent = gamma_exponent
        self.lambda_exponent = lambda_exponent
        self.mu_exponent = mu_exponent
        self.num_neighbours = num_neighbours
        self.min_distance = min_distance
        self.supply_map_parameters = supply_map_parameters

        # physiological parameters
        # store the DataSample's random number generator for generation purposes
        msg = ("Random number generator of the DataSample needs to be passed to "
               "the LiverVasculatureGenerator to keep the pipeline deterministic!")
        assert rng, msg
        self.rng = rng
        # Sample blood viscosity
        self.viscosity = trunc_norm(self.rng,
                                    mu=viscosity_mu,
                                    sigma=viscosity_sigma,
                                    min=viscosity_min,
                                    max=viscosity_max)

    def generate_demand_maps(self, organ: vtkPolyData, **kwargs):
        """
        Generate the oxygen demand and supply map as VascuSynth inputs.

        Args:
            organ: Surface mesh representing the shape that the map should
                be generated for.
        """
        # Generate VascuSynth supply map and oxygen demand map
        self._map_generator = MapGenerator(organ, rng=self.rng, **kwargs)
        oxygenation_map, supply_map = self._map_generator.generate(self.supply_map_parameters)

        # Voxel width in ODM coordinates
        self._voxel_width_ODM = self.organ_scene_object.voxel_resolution / self._map_generator.scale_factor  # m

        return oxygenation_map, supply_map

    def create_tree_parameter_file(
            self,
            vessel: Vasculature,
            sample_directory: str = '',
            random_seed: int = -1
    ) -> Tuple[str, str]:
        """
        Create a parameter file as input to VascuSynth that specifies one vessel tree to be generated 
        into the organ volume described by the oxygen demand map.
        
        Args:
            vessel: Vasculature scene object holding all parameters that are used to generate 
                the paramater file as VascuSynth input.
            sample_directory: Directory that VascuSynth should generate the specified output files
                into. Usually the DataSample's directory: sample.path.
            random_seed: Random seed for VascuSynth to use, usually the sample's ID. Needs to be
                refactored to go into cmd line arguments of the VascuSynth call.
                
        Returns:
            filename, content: Name of the parameter file to be written to disk and contents of the text file.
        """

        # use all info and parameters from the scene object
        msg = f"Generating parameter file {vessel.filename_parameters}"
        Log.log("VasculatureGenerator", msg=msg, severity="INFO")
        if not vessel.perforation_point:
            msg = (f"Vasculature scene object {vessel.filename} "
                   f"cannot be parameterized without a perforation point. "
                   f"Skipping this vascular tree for the generation.")
            Log.log("VasculatureGenerator", severity='WARN', msg=msg)
            # so that it is not passed to VascuSynth later
            vessel.filename_parameters = ""
            return None, None

        if not vessel.perforation_flow:
            msg = (f"Vasculature scene object {vessel.filename} "
                   f"cannot be parameterized without a perforation flow. "
                   f"Skipping this vascular tree for the generation.")
            Log.log("VasculatureGenerator", severity='WARN', msg=msg)
            # so that it is not passed to VascuSynth later
            vessel.filename_parameters = ""
            return None, None

        # VascuSynth demands parameters for both the perfusion pressure and terminal pressure.
        # Only the pressure gradient is actually used for calculations,
        # so it's okay to use a terminal pressure of 0.0
        perforation_pressure = vessel.pressure_gradient
        terminal_pressure = 0.0

        output_filename = os.path.join(sample_directory, vessel.filename_tree_struct_intermediate)
        # Generate parameter file that will be read by VascuSynth
        # perforation point is in ODM coordinates
        parameter_file = cleandoc(
            f"""PERF_POINT: {" ".join(map(str, vessel.perforation_point))}
                PERF_PRESSURE: {perforation_pressure}
                TERM_PRESSURE: {terminal_pressure}
                PERF_FLOW: {vessel.perforation_flow}
                RHO: {self.viscosity}
                GAMMA: {self.gamma_exponent}
                LAMBDA: {self.lambda_exponent}
                MU: {self.mu_exponent}
                MIN_DISTANCE: {self.min_distance}
                NUM_NODES: {vessel.num_terminal_nodes}
                VOXEL_WIDTH: {self._voxel_width_ODM}
                CLOSEST_NEIGHBOURS: {self.num_neighbours}
                OUTPUT_FILENAME: {output_filename}
                RANDOM_SEED: {random_seed}""")

        return vessel.filename_parameters, parameter_file

    def parametrize_vascular_trees(
            self,
            **kwargs
    ) -> Dict[str, str]:
        """
        Generate parameter files for VascuSynth for each of the vascular trees specified
        in the generator's vasculature scene objects.

        Returns:
            {filename: file contents} Filename and contents of the VascuSynth parametrization
                text files for all vessel scene objects specified for the generator.
        """
        trees = {}

        # default: set random perforation points on the organ surface
        perf_points = self._map_generator.get_perf_points_random()

        # make sure all vessel trees get an own perforation point. Cannot use the existing ones
        # in order to avoid intersections
        msg = (f"Not enough random perforation points available from the MapGenerator!"
               f"Missing {len(self.vessel_scene_objects) - len(perf_points)} out of {len(self.vessel_scene_objects)}."
               f" Only vessel trees with a perforation point will be generated: "
               f"{[self.vessel_scene_objects[i].filename for i in range(len(perf_points))]}.")
        Log.log("VasculatureGenerator", severity='WARN', msg=msg)

        # default: set an equal perforation flow for each vessel tree that sums up to
        # blood flow from volume
        total_flow = self._calculate_total_flow(self._map_generator._organ)
        flow_percentage = 1/len(self.vessel_scene_objects)

        # add the vessel trees with this parametrization
        for i, vessel in enumerate(self.vessel_scene_objects):
            vessel.set_perforation_point(perf_points[i])
            vessel.set_perforation_flow(flow_percentage * total_flow)
            filename, parameter_file = self.create_tree_parameter_file(vessel, **kwargs)
            if filename:
                trees[filename] = parameter_file

        return trees

    def generate_structure(
            self,
            random_seed: int,
            sample_directory: str = ''
    ) -> Tuple[str, str]:
        """
        Call VascuSynth to generate the vessel tree graph GXL file.

        Args:
            random_seed: Random seed to initialize VascuSynth's random number generator. Should
                be set to the DataSample's ID for consistency.
            sample_directory: Directory that VascuSynth should generate the specified output files
                into. Usually the DataSample's directory: sample.path.

        Raises:
            subprocess.CalledProcessError if return code of VascuSynth call is != 0.

        Returns:
            (stdout, stderr) of the VascuSynth subprocess call as strings.
        """
        # Todo: random seed in VascuSynth's command line arguments
        command = [str(self.VascuSynth_path)]
        command += [os.path.join(sample_directory, str(self.organ_scene_object.filename_oxygen_demand_map))]
        command += [os.path.join(sample_directory, str(self.organ_scene_object.filename_supply_map))]
        command += [os.path.join(sample_directory, vessel.filename_parameters) for vessel in self.vessel_scene_objects]

        process = subprocess.run(command, capture_output=True, check=True, text=True)

        # throws an Exception if returncode != 0
        # on success, return stdout and stderr
        return process.stdout, process.stderr

    def generate_3D_representation(
            self,
            trees: List[Tuple[Vasculature, VascularTree]]
    ) -> Dict[str, vtkPolyData]:
        """
        Generate a 3D model for the passed vessel trees. This scales the VascularTrees
        first according to the scaling between the VascuSynth output and the original
        organ input file, which is saved in the generator instance, i.e. if vessels have
        been generated by another generator instance, the resulting 3D models will be wrong.

        The mapping between vessel scene objects and tree structure is used from the
        passed dictionary, no consistency with the generator's own vessel scene objects
        is enforced!

        Args:
            trees: List of vessel scene objects and corresponding VascularTree structures
                that have been read from VascuSynth output, but UNSCALED.

        Returns:
            tree_models: 3D models of the described vessel trees using parameters from the
                respective vessel scene objects.
        """
        tree_models = {}

        for vessel_obj, tree_structure in trees:
            # scale the tree according to the scaling between oxygen demand map and 3D model

            # curveHeight: Convert maximum extent of curved branches from ODM coordinates to object coordinates
            # radius_avg: Convert radii from SI units to units used in input volume
            # - A conversion to object coordinates is not necessary for branch radii
            #   because VascuSynth already stores them in object coordinates
            tree_structure.scale_edge_attributes(["curveHeight", "radius_avg"],
                                       [1 / self._map_generator.scale_factor,
                                        1 / self.organ_scene_object.voxel_resolution])

            # Convert node positions from ODM coordinates to object coordinates.
            # - This transformation is necessary because positions in VascuSynth GXL tree output
            #   use ODM coordinates (even though radii are output in object coordinates)
            tree_structure.transform_node_coordinates(self._map_generator.lower_corner,
                                                      1 / self._map_generator.scale_factor)

            # collect arguments to pass on to the branch factory
            # this can be used to unpack parameters from the scene objects
            branch_factory_args = ()

            # curved should come from vessel scene object
            if vessel_obj.curved:
                # create curved tree with information from general VascularTree object
                # this is in order to get the right branch factory below
                tree_structure = CurvedTree.create_from_tree(tree_structure)
                branch_factory_args += (vessel_obj.percentile_max_branch_length, vessel_obj.num_spline_points)

            # 3D model creation is needed first because tortuosity is calculated here
            # kind of makes sense: the CurvedTree is only a container, but the CurvedBranch knows everything about the
            # 3D object creation and the Factory is the one determining the exact shape of the branch (sine generated)
            # - this could also be some other curve in the future
            # need to call generate_model here directly to fix cyclic import
            # parameterize num_sides
            model = model_generator.generate_model(vessel_obj.num_cylinder_polygons,
                                                   tree_structure,
                                                   tree_structure.get_branch_factory(*branch_factory_args))

            # update lengths of curved branches according to the branch factory that has been used
            # this is a structural problem but not fixing now
            # only calling model_generator.generate
            tree_structure.calculate_lengths()

            tree_models[vessel_obj.filename] = model

        return tree_models

    def _calculate_total_flow(
            self,
            organ_model: vtkPolyData
    ) -> float:
        """
        Calculate the blood flow through the organ in m^3 / s.
        """
        # translate scale ignorant polydata info into real life scales using the voxel resolution
        organ_volume_SI = calc_volume(organ_model) * self.organ_scene_object.voxel_resolution ** 3  # m^3

        # mass = density * volume
        # flow = mass * flow/mass
        density = self.organ_scene_object.density  # kg / m^3
        blood_flow_per_mass = self.organ_scene_object.blood_flow_per_mass  # m^3 / (kg * s)
        flow_total = density * organ_volume_SI * blood_flow_per_mass  # m^3 / s
        return flow_total

    def scale_to_ODM_coordinates(self, value: float):
        """Scale a scalar value from object coordinates to oxygen demand map coordinates."""
        return value / self._voxel_width_ODM

    def scale_to_object_coordinates(self, value: float):
        """Scale a scalar value from oxygen demand map coordinates to object coordinates."""
        return value * self._voxel_width_ODM


class LiverVasculatureGenerator(VasculatureGenerator):
    """
    Adapts the VasculatureGenerator class
    to generation of the three major liver blood vessels.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    def __init__(self,
                 *args,
                 flow_percentage_HA_mu: float = 0.25,
                 flow_percentage_HA_sigma: float = 0.025,
                 flow_percentage_HA_min: float = 0.2,
                 flow_percentage_HA_max: float = 0.3,
                 radius_heuristic_scaling_param_c: float = 2.0,
                 root_segment_length_heuristic_scaling_param: float = 15.0,
                 tolerance_perforation_point_placement_x: float = 0.1,
                 PV_sup_inf_placing_mu: float = 0.2669,
                 PV_sup_inf_placing_sigma: float = 0.0304,
                 PV_sup_inf_placing_min: float = 0.2061,
                 PV_sup_inf_placing_max: float = 0.3277,
                 HV_sup_inf_placing_mu: float = 0.8804,
                 HV_sup_inf_placing_sigma: float = 0.0279,
                 HV_sup_inf_placing_min: float = 0.8246,
                 HV_sup_inf_placing_max: float = 0.9362,
                 **kwargs
    ) -> None:
        """
        Args:
            flow_percentage_HA_mu: Mean value for the truncated normal distribution to
                sample the percentage of blood flow coming in from the hepatic artery.
            flow_percentage_HA_sigma: Standard deviation for the truncated normal distribution
                to sample the percentage of blood flow coming in from the hepatic artery.
            flow_percentage_HA_min: Minimum truncation value for the truncated normal
                distribution to sample the percentage of blood flow coming in from the hepatic artery.
            flow_percentage_HA_max: Maximum truncation value for the truncated normal
                distribution to sample the percentage of blood flow coming in from the hepatic artery.
            radius_heuristic_scaling_param_c: Scaling parameter to compute a heuristic
                upper bound for the root segment radius from organ size, blood viscosity,
                perforation flow, pressure gradient and number of terminal nodes. Default
                determined by trial and error on liver data.
            root_segment_length_heuristic_scaling_param: Prefactor for estimating the length of the
                root segment from the diameter of the containing organ's bounding box and the
                desired number of terminal nodes. Default determined by trial and error.
            tolerance_perforation_point_placement_x: Fraction of the x extent of the
                liver that is not used for perforation point placement on either side (+x, -x).
            PV_sup_inf_placing_mu: Mean value of the truncated normal distribution
                to sample the position of the portal vein along the superior-posterior
                axis of the organ.
            PV_sup_inf_placing_sigma: Standard deviation of the truncated normal distribution
                to sample the position of the portal vein along the superior-posterior
                axis of the organ.
            PV_sup_inf_placing_min: Minimum value of the truncated normal distribution
                to sample the position of the portal vein along the superior-posterior
                axis of the organ.
            PV_sup_inf_placing_max: Maximum value of the truncated normal distribution
                to sample the position of the portal vein along the superior-posterior
                axis of the organ.
            HV_sup_inf_placing_mu: Mean value of the truncated normal distribution
                to sample the position of the hepatic vein along the superior-posterior
                axis of the organ.
            HV_sup_inf_placing_sigma: Standard deviation of the truncated normal distribution
                to sample the position of the hepatic vein along the superior-posterior
                axis of the organ.
            HV_sup_inf_placing_min: Minimum value of the truncated normal distribution
                to sample the position of the hepatic vein along the superior-posterior
                axis of the organ.
            HV_sup_inf_placing_max: Maximum value of the truncated normal distribution
                to sample the position of the hepatic vein along the superior-posterior
                axis of the organ.
        """

        super(LiverVasculatureGenerator, self).__init__(*args, **kwargs)

        # set liver-specific physiological parameters
        self.flow_percentage_HA_mu = flow_percentage_HA_mu
        self.flow_percentage_HA_sigma = flow_percentage_HA_sigma
        self.flow_percentage_HA_min = flow_percentage_HA_min
        self.flow_percentage_HA_max = flow_percentage_HA_max
        self.flow_percentage_HA = 0.0

        # algorithm parameters / heuristics
        self.radius_heuristic_scaling_param_c = radius_heuristic_scaling_param_c
        self.root_segment_length_heuristic_scaling_param = root_segment_length_heuristic_scaling_param

        # for perforation point determination
        self.tolerance_perforation_point_placement_x = tolerance_perforation_point_placement_x
        self.PV_sup_inf_placing_mu = PV_sup_inf_placing_mu
        self.PV_sup_inf_placing_sigma = PV_sup_inf_placing_sigma
        self.PV_sup_inf_placing_min = PV_sup_inf_placing_min
        self.PV_sup_inf_placing_max = PV_sup_inf_placing_max
        self.HV_sup_inf_placing_mu = HV_sup_inf_placing_mu
        self.HV_sup_inf_placing_sigma = HV_sup_inf_placing_sigma
        self.HV_sup_inf_placing_min = HV_sup_inf_placing_min
        self.HV_sup_inf_placing_max = HV_sup_inf_placing_max

        # check consistency of defined vasculature types for the liver
        vessel_types = [type(vessel) for vessel in self.vessel_scene_objects]
        named_types = [f"{vessel.filename} of type {type(vessel)}" for vessel in self.vessel_scene_objects]

        # check that every vasculature type is unique
        msg = (f"LiverVasculatureGenerator cannot process more than one instance of each vasculature type but these"
               f"were defined: {named_types}")
        assert len(list(set(vessel_types))) == len(vessel_types), msg

        # check that portal vein and hepatic vein are there
        msg = (f"LiverVasculatureGenerator needs a hepatic vein and a portal vein at minimum but was only provided "
               f"{named_types}")
        assert PortalVein in vessel_types and HepaticVein in vessel_types, msg

        # check if all requested vasculature types are supported
        msg = (f"LiverVasculatureGenerator only supports PortalVein, HepaticVein and HepaticArtery but was provided "
               f"{named_types}")
        assert set(vessel_types).issubset({PortalVein, HepaticVein, HepaticArtery}), msg

    def parametrize_vascular_trees(
            self,
            inferior_vena_cava_obj: vtkPolyData = None,
            **kwargs
    ) -> Dict[str, str]:
        """
        Args:
            inferior_vena_cava_obj: Surface mesh of the inferior vena cava for the liver mesh.
                If no 3D object is specified, a position for the inferior_vena_cava_obj is generated randomly.

        Returns:
            {filename: file contents} Filename and contents of the VascuSynth parametrization
                text files for all vessel scene objects specified for the generator.
        """
        trees = {}

        # calculate values
        # save them in the scene objects
        # map generation must have been called before this, some values needed from MapGenerator

        # update perforation flows in vasculature scene objects
        msg = "Calculating flows"
        Log.log("LiverVasculatureGenerator", msg=msg, severity="INFO")
        self._calculate_flows(self._map_generator._organ)  # m^3 / s

        # Calculate heuristic upper bound for root segment radii of all three trees based on the perforation flows
        msg = "Calculating radius heuristics"
        Log.log("LiverVasculatureGenerator", msg=msg, severity="INFO")
        radius_heuristics = dict()
        if self.has_hepatic_artery():
            radius_heuristics["hepatic_artery"] = self._radius_heuristic(self._get_vessel_instance_by_type(HepaticArtery))
        radius_heuristics["portal_vein"] = self._radius_heuristic(self._get_vessel_instance_by_type(PortalVein))
        radius_heuristics["hepatic_vein"] = self._radius_heuristic(self._get_vessel_instance_by_type(HepaticVein))

        # Get perforation point positions from MapGenerator based on oxygen demand map/containing organ
        # use radius heuristics to separate HA entry point from PV entry point and to move the perforation points
        # a little inside so that the 3D models will not penetrate the surrounding organ surface
        # optional inferior vena cava  object is used to determine superior-inferior axis of perforation points
        msg = "Determining perforation points"
        Log.log("LiverVasculatureGenerator", msg=msg, severity="INFO")
        liver_perf_points = self._map_generator.get_perf_points_liver(
            radius_heuristics,
            inferior_vena_cava_obj,
            self.tolerance_perforation_point_placement_x,
            self.PV_sup_inf_placing_mu,
            self.PV_sup_inf_placing_sigma,
            self.PV_sup_inf_placing_min,
            self.PV_sup_inf_placing_max,
            self.HV_sup_inf_placing_mu,
            self.HV_sup_inf_placing_sigma,
            self.HV_sup_inf_placing_min,
            self.HV_sup_inf_placing_max
        )
        if self.has_hepatic_artery():
            self._get_vessel_instance_by_type(HepaticArtery).set_perforation_point(liver_perf_points["hepatic_artery"])
        self._get_vessel_instance_by_type(PortalVein).set_perforation_point(liver_perf_points["portal_vein"])
        self._get_vessel_instance_by_type(HepaticVein).set_perforation_point(liver_perf_points["hepatic_vein"])

        # add the vessel trees with this parametrization
        for vessel in self.vessel_scene_objects:
            filename, parameter_file = self.create_tree_parameter_file(vessel, **kwargs)
            if filename:
                trees[filename] = parameter_file

        return trees

    def _get_vessel_instance_by_type(
            self,
            vasculature_type: type
    ) -> Union[Vasculature, None]:
        """Get the scene object of the right type from the self.vessel_scene_objects list."""
        potential_objects = [vessel for vessel in self.vessel_scene_objects if isinstance(vessel, vasculature_type)]
        if potential_objects:
            return potential_objects[0]
        else:
            return None

    def has_hepatic_artery(self):
        """Check if a hepatic artery has been requested in the generator's vessel scene objects."""
        return any(isinstance(vessel, HepaticArtery) for vessel in self.vessel_scene_objects)


    def _calculate_flows(self, organ):
        """
        Calculate the blood flow through each of the three blood vessels in m^3 / s.
        """

        flow_total = self._calculate_total_flow(organ)

        # calculate the proportion of the blood flow to and from the liver
        # by each of the vessel trees

        # blood supply by hepatic artery
        # blood to clean provided by portal vein
        self.flow_percentage_HA = trunc_norm(self.rng,
                                             mu=self.flow_percentage_HA_mu,
                                             sigma=self.flow_percentage_HA_sigma,
                                             min=self.flow_percentage_HA_min,
                                             max=self.flow_percentage_HA_max)
        flow_percentage_PV = 1.0 - self.flow_percentage_HA

        if self.has_hepatic_artery():
            hepatic_artery = self._get_vessel_instance_by_type(HepaticArtery)
            hepatic_artery.set_perforation_flow(self.flow_percentage_HA * flow_total)

        portal_vein = self._get_vessel_instance_by_type(PortalVein)
        portal_vein.set_perforation_flow(flow_percentage_PV * flow_total)

        # hepatic vein drains all blood from the liver
        hepatic_vein = self._get_vessel_instance_by_type(HepaticVein)
        hepatic_vein.set_perforation_flow(flow_total)


    def _radius_heuristic(
            self,
            vessel: Vasculature
    ) -> float:
        """
        Use a heuristic formula to calculate an upper bound for the radius of
        the root segment of a vessel tree. Heuristic scaling parameters have
        only been identified for the liver, thus the placement in this class
        instead of the superclass.

        This is used when determining perforation point positions.
        """

        # Calculate reasonable upper bound for segment length
        # think of demand map cuboid as bounding box of a sphere and get its diagonal
        # square root of number of voxels in x^2 + y + z
        diameter = (self._map_generator.nx ** 2 + self._map_generator.ny ** 2 + self._map_generator.nz ** 2) ** 0.5
        distance = self.root_segment_length_heuristic_scaling_param * diameter / vessel.num_terminal_nodes  # l_perf

        # Convert pressure, flow and distance to SI units
        distance_SI = self.scale_to_object_coordinates(distance)

        reduced_resistance = 8.0 * self.viscosity * distance_SI / pi  # _R*_perf
        # 8.0 comes from fixed reduced resistance for terminal segments
        radius_heuristic = self.radius_heuristic_scaling_param_c * \
                           (vessel.perforation_flow * reduced_resistance / vessel.pressure_gradient) ** 0.25  # r_perf

        # Convert to ODM coordinates before returning
        return self.scale_to_ODM_coordinates(radius_heuristic)

