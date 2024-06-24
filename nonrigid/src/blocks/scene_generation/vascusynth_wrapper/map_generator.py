import numpy as np
from typing import Tuple, List, Union, TYPE_CHECKING, Dict
from scipy.ndimage import (
    binary_erosion,
    binary_fill_holes,
    distance_transform_cdt
)
from vtk import (
    vtkVoxelModeller,
    vtkPolyData,
    vtkCenterOfMass
)

if TYPE_CHECKING:
    import random  # only for typing!

from core.log import Log
from utils.utils import trunc_norm

def join(tup: tuple) -> str:
    """
    Concatenates the entries of a tuple into a string
    """

    return " ".join(map(str, tup))

class MapGenerator:
    """
    Generates oxygen demand and supply map for VascuSynth.

    VascuSynth oxygen demand maps are made up of boxes with a demand in the interval [0, 1]
    This class rasterizes the organ volume and sets oxygen demand to 1 for voxels inside
    the organ, and oxygen demand to zero for voxels outside.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    def __init__(
            self,
            organ: vtkPolyData,
            ODM_width: int = 110,
            voxelizer_max_distance: float = 0.03,
            voxel_content_threshold: float = 0.5,
            oxygen_demand_voxel_value: float = 1.0,
            erosion_stencil_fraction: float = 20,
            rng: 'random.Random' = None
    ) -> None:
        """
        Args:
            organ: Surface mesh representing the shape that the map should
                be generated for.
            ODM_width: Extent of the oxygen demand map in the x direction
                in units of voxels. Extents in the y and z direction are
                calculated based on this value.
            voxelizer_max_distance: Distance away from surface of input
                geometry for the vtkVoxelModeller to sample.
            voxel_content_threshold: Threshold from which occupancy value [0 ... 1]
                a voxel counts as inside or outside of the organ.
            oxygen_demand_voxel_value: Value between 0 (no oxygen demand) and 1
                (highest possible oxygen demand) to assign to a voxel in the
                oxygenation map that lies inside the input volume.
            erosion_stencil_fraction: Fraction of the number of voxels
                of the oxygenation map in x, y, z direction that will be used as
                cuboid stencil in the binary erosion step.
            rng: Random number generator of the DataSample. Under no circumstances
                create an own new rng here.
        """

        self._organ = organ
        # parameters for processing the input volume
        self._ODM_width = ODM_width
        self._voxelizer_max_distance = voxelizer_max_distance
        self._voxel_content_threshold = voxel_content_threshold
        self._oxygen_demand_voxel_value = oxygen_demand_voxel_value
        self._erosion_stencil_fraction = erosion_stencil_fraction

        msg = ("Random number generator of the DataSample needs to be passed to "
               "the MapGenerator to keep the pipeline deterministic!")
        assert rng, msg
        self.rng = rng

        # Set up discrete coordinate system for the oxygen demand map
        self._compute_coords()

        # initialize empty map, to be filled later by self._generate_oxygenation_map
        self._oxygenation_map = None

    def _compute_coords(self) -> None:
        """
        Set up discrete coordinate system for the oxygen demand map
        from the continuous coordinate system in the OBJ file.
        """

        bounds = 6 * [0.0]
        self._organ.GetBounds(bounds)
        x_min, x_max, y_min, y_max, z_min, z_max = bounds
        self.lower_corner = x_min, y_min, z_min
        self.upper_corner = x_max, y_max, z_max

        # compute x coordinates xs and save step size in x direction dx
        xs, dx = np.linspace(x_min, x_max, self._ODM_width, retstep=True)
        ys = np.arange(y_min, y_max, dx)
        zs = np.arange(z_min, z_max, dx)

        self.nx = xs.shape[0]
        self.ny = ys.shape[0]
        self.nz = zs.shape[0]

        # Upper corner of organ bounding box in ODM coordinates
        self.upper_corner_voxel = join((self.nx, self.ny, self.nz))
        self.scale_factor = 1.0 / dx

    def _voxelize_input(
            self
    ) -> np.ndarray:
        """
        Rasterize space occupied by input surface mesh and label voxels that
        are occupied by the surface.
        """
        # from vtk bound calculation of input organ
        x_min, y_min, z_min = self.lower_corner
        x_max, y_max, z_max = self.upper_corner
        bounds = [x_min, x_max, y_min, y_max, z_min, z_max]

        # Rasterize the organ volume
        voxelizer = vtkVoxelModeller()
        voxelizer.SetSampleDimensions(self.nx, self.ny, self.nz)
        voxelizer.SetModelBounds(bounds)
        voxelizer.SetScalarTypeToChar()
        voxelizer.SetMaximumDistance(self._voxelizer_max_distance)
        voxelizer.SetInputData(self._organ)
        voxelizer.Update()

        scalars = voxelizer.GetOutput().GetPointData().GetScalars()

        # Ideally, this line should be replaced by a call to vtk_to_numpy.
        # However, vtk_to_numpy seems to be broken for certain combinations
        # of vtk and numpy package versions.
        oxygenation_map = np.frombuffer(scalars, dtype=np.int8).reshape(self.nz, self.ny, self.nx).T
        # self._oxygenation_map = vtk_to_numpy(scalars).reshape(self.nz, self.ny, self.nx).T

        # not written to attribute yet because it's only a surface, not a volume
        # needs further processing
        return oxygenation_map

    def _generate_supply_map(
            self,
            supply_map_parameters: List[float]
    ) -> str:
        """
        Compile a valid supply map file for VascuSynth describing the
        area of this rule and the parameters for the supply reduction stencil.

        Args:
            supply_map_parameters: Parameters for the oxygenation map update function.
        """
        supply_map = f"{self.upper_corner_voxel} {len(supply_map_parameters)}\n"
        supply_map += f"0 0 0 {self.upper_corner_voxel}\n"
        param_string = map(str, supply_map_parameters)
        supply_map += " ".join(param_string)

        return supply_map

    def _voxel_to_str(self, i: int, j: int, k: int) -> str:
        """
        Create a string representation of the contents of a voxel
        for the oxygenation map consisting of lower and upper corner
        voxel indices and a filling value of 1 if it is occupied by
        more than _voxel_content_threshold of the input volume.
        """
        value = int(self._oxygenation_map[i, j, k])
        if value < self._voxel_content_threshold:
            return ""

        lower_corner = join((i, j, k))
        upper_corner = join((i + 1, j + 1, k + 1))
        # the value self._oxygen_demand_voxel_value is read into VascuSynth as
        # a double value using <cstdlib> double atof (const char* str);
        return f"{lower_corner} {upper_corner}\n{self._oxygen_demand_voxel_value}\n"

    def _generate_oxygenation_map(self) -> str:
        """
        Generates the oxygen demand map.
        This function is not intended to be called more than once for each instance.
        """

        oxygenation_map = self._voxelize_input()

        # _voxelize_input() stores labels for the surface of the organ in oxygenation_map
        # Use hole filling to also label the volume of the organ
        self._oxygenation_map = binary_fill_holes(oxygenation_map)

        # Erode part of the organ volume to account for discretization errors.
        # VascuSynth does not exhaustively verify that generated branches lie entirely
        # within the perfusion volume. Hence, a larger tolerance may be necessary
        # when generating very thick branches.
        r = (self.nx // self._erosion_stencil_fraction,
             self.ny // self._erosion_stencil_fraction,
             self.nz // self._erosion_stencil_fraction)
        self._oxygenation_map = binary_erosion(self._oxygenation_map, structure=np.ones(r, int))

        # Generate string representation of the oxygen demand map
        oxygenation_map_string = f"{self.upper_corner_voxel}\n0 0 0 "
        oxygenation_map_string += f"{self.upper_corner_voxel}\n0\n"
        oxygenation_map_string += "".join(self._voxel_to_str(i, j, k) for i in range(self.nx)
                                          for j in range(self.ny) for k in range(self.nz))

        return oxygenation_map_string

    def generate(
            self,
            supply_map_parameters: List[float]
    ) -> Tuple[str, str]:
        """
        Generate the oxygen demand and supply map.
        This function should not be called more than once for a single instance.

        Args:
            supply_map_parameters: Parameters for the oxygenation map update function.
        """

        oxygenation_map = self._generate_oxygenation_map()
        supply_map = self._generate_supply_map(supply_map_parameters)

        return oxygenation_map, supply_map

    def _add_tolerance(self, perf: Tuple[float, float, float],
                       radius_heuristic: float) -> Tuple[float, float, float]:
        """
        Shifts a perforation point farther into the organ volume
        to ensure that the resulting vessel segments are confined to the organ. 
        """

        x, y, z = perf
        r = round(radius_heuristic)
        # If the shifted perforation point would be located outside of the organ,
        # do not shift it
        if self._oxygenation_map[x, y, z - r] > 0:
            return x, y, z - r
        return perf

    def _get_perf_point_HA(self, perf_PV: Tuple[float, float, float],
                           radius_heuristics: dict) -> Tuple[float, float, float]:
        """
        Calculates a suitable perforation point for the hepatic artery
        based on the perforation point position for the portal vein

        Args:
            perf_PV: perforation point position for the portal vein
            radius_heuristics: heuristic upper bounds for the root segment radii
                of all trees
        """

        r = round(radius_heuristics["hepatic_artery"] + radius_heuristics["portal_vein"])
        r = max(r, 1)
        x_PV, y_PV, z_PV = perf_PV

        # Generate square of candidate points
        candidate_points = [(x_PV + ri, y_PV + rj, z_PV) for ri in range(-r, r + 1) for rj in (-r, r)]
        candidate_points += [(x_PV + rj, y_PV + ri, z_PV) for ri in range(-r, r + 1) for rj in (-r, r)]

        # Discard candidate points which are located outside of the liver
        in_liver = lambda p: p[0] < self.nx and p[1] < self.ny and p[2] < self.nz
        candidate_points = list(filter(in_liver, candidate_points))
        # Discard candidate point which do not project onto the liver along the z-axis
        has_projection = lambda p: np.nonzero(self._oxygenation_map[p[0], p[1], :])[0].shape[0] > 0
        candidate_points = list(filter(has_projection, candidate_points))

        if len(candidate_points) == 0:
            msg = "Warning: No HA perforation point found, using random perforation point"
            Log.log(module="MapGenerator (vessel generation)", msg=msg)
            return self.get_perf_points_random()[0]
        
        x_HA, y_HA, _ = self.rng.choice(candidate_points)
        # Find projection onto the liver surface
        z_HA = np.max(np.nonzero(self._oxygenation_map[x_HA, y_HA, :]))
        return x_HA, y_HA, z_HA

    def get_perf_points_random(self) -> Union[List[Tuple[int, int, int]], None]:
        """
        Returns a list of possible perforation points
        (i.e. points on the organs surface) in random order, or
        None if the oxygen demand map has not yet been generated.

        Returns:
            List of points close to the oxygenation map boundary, points given
            in ODM (discrete) coordinates/indices.
        """

        # Make sure the oxygen demand map has been generated
        if self._oxygenation_map is None:
            return None

        distance_map = distance_transform_cdt(self._oxygenation_map)
        organ_boundary = np.logical_and(distance_map > 0.5, distance_map < 1.5)
        perf_points_x, perf_points_y, perf_points_z = np.nonzero(organ_boundary)
        perf_points = list(zip(perf_points_x, perf_points_y, perf_points_z))
        self.rng.shuffle(perf_points)

        return perf_points

    def get_perf_points_liver(
            self,
            radius_heuristics: dict,
            IVC: vtkPolyData,
            tolerance_perforation_point_placement_x: float,
            *args
    ) -> Dict[str, Tuple[int, int, int]]:
        """
        Generate three perforation points for liver blood vessels with
        the help of a 3D model of the inferior vena cava (IVC) for the patient.

        If an IVC_path is specified, liver meshes must be oriented such that the
        IVC lies along the y-axis and the hepatic portal faces the negative z direction.
        Otherwise, an IVC position is randomly generated.

        Args:
            radius_heuristics: heuristic upper bounds for the root segment radii
                of all trees
            IVC: Surface mesh of the inferior vena cava for the liver mesh.
                If no path is specified, a position for the IVC is generated randomly.
            tolerance_perforation_point_placement_x: Fraction of the x extent of the
                liver that is not used for perforation point placement on either side (+x, -x).

        Returns:
            Calculated perforation points in oxygen demand map coordinates or None if
                the oxygen demand map has not yet been generated.
        """

        if IVC is None:

            x_min, _, _ = self.lower_corner
            x_max, _, _ = self.upper_corner
            IVC_x = x_min + self.rng.random() * (x_max - x_min)

            threshold = tolerance_perforation_point_placement_x * (x_max - x_min)
            IVC_x = np.clip(IVC_x, x_min + threshold, x_max - threshold)

        else: 
            center_of_mass_calculator = vtkCenterOfMass()
            center_of_mass_calculator.SetInputData(IVC)
            center_of_mass_calculator.Update()
            IVC_pos = center_of_mass_calculator.GetCenter()
            IVC_x = IVC_pos[0]

        msg = f"get_perf_points_liver finished, x: {IVC_x}"
        Log.log(module="MapGenerator (vessel generation)", msg=msg)

        return self._perf_points_dispatcher(radius_heuristics, IVC_x, *args)

    def _perf_points_dispatcher(
            self,
            radius_heuristics: dict,
            IVC_x: float,
            PV_sup_inf_placing_mu: float,
            PV_sup_inf_placing_sigma: float,
            PV_sup_inf_placing_min: float,
            PV_sup_inf_placing_max: float,
            HV_sup_inf_placing_mu: float,
            HV_sup_inf_placing_sigma: float,
            HV_sup_inf_placing_min: float,
            HV_sup_inf_placing_max: float,
    ) -> Dict[str, Tuple[int, int, int]]:
        """
        Executes the perforation point computation.

        Args:
            radius_heuristics: heuristic upper bounds for the root segment radii
                of all trees
            IVC_x: x coordinate of the center of mass of the inferior vena cava.
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

        Returns:
            Calculated perforation points in oxygen demand map coordinates or None if
                the oxygen demand map has not yet been generated.
        """

        # Make sure the oxygen demand map has been generated
        if self._oxygenation_map is None:
            msg = "Generating oxygenation map again"
            Log.log(module="MapGenerator (vessel generation)", msg=msg)
            self.generate()

        # transform IVC position to map (voxel) coordinates
        x_min_liver = self.lower_corner[0]
        IVC_x_transformed = round(self.scale_factor * (IVC_x - x_min_liver))

        # y line that runs along liver at IVC x position
        msg = "Determining y line"
        Log.log(module="MapGenerator (vessel generation)", msg=msg)
        IVC_slice = self._oxygenation_map[IVC_x_transformed, :, :]
        nonzero_y_values = np.nonzero(IVC_slice)[0]
        y_min, y_max = np.min(nonzero_y_values), np.max(nonzero_y_values)

        # Generate perforation points for PV and HV
        msg = "Sampling relative positions"
        Log.log(module="MapGenerator (vessel generation)", msg=msg)
        y_PV_percentage = trunc_norm(self.rng,
                                     mu=PV_sup_inf_placing_mu,
                                     sigma=PV_sup_inf_placing_sigma,
                                     min=PV_sup_inf_placing_min,
                                     max=PV_sup_inf_placing_max)
        y_HV_percentage = trunc_norm(self.rng,
                                     mu=HV_sup_inf_placing_mu,
                                     sigma=HV_sup_inf_placing_sigma,
                                     min=HV_sup_inf_placing_min,
                                     max=HV_sup_inf_placing_max)
        y_PV = y_min + int(y_PV_percentage * (y_max - y_min))
        y_HV = y_min + int(y_HV_percentage * (y_max - y_min))

        # If all points with the generated y coordinate lie outside of the organ,
        # assign the closest y value with points inside
        msg = "Validating y positions inside organ"
        Log.log(module="MapGenerator (vessel generation)", msg=msg)
        validate_y = lambda y: sorted(nonzero_y_values, key=lambda y0: abs(y0 - y))[0]
        y_PV = validate_y(y_PV)
        y_HV = validate_y(y_HV)

        # Computes z coordinate for projection of a point onto the liver surface
        msg = "Computing z coordinates"
        Log.log(module="MapGenerator (vessel generation)", msg=msg)
        get_z = lambda y: np.max(np.nonzero(IVC_slice[y, :]))

        perf_PV = IVC_x_transformed, y_PV, get_z(y_PV)
        perf_HV = IVC_x_transformed, y_HV, get_z(y_HV)

        if "hepatic_artery" in radius_heuristics:
            msg = "Adding HA perforation point"
            Log.log(module="MapGenerator (vessel generation)", msg=msg)
            perf_HA = self._get_perf_point_HA(perf_PV, radius_heuristics)
            perf_HA = self._add_tolerance(perf_HA, radius_heuristics["hepatic_artery"])
        else:
            perf_HA = None

        msg = "Adding tolerances"
        Log.log(module="MapGenerator (vessel generation)", msg=msg)
        perf_PV = self._add_tolerance(perf_PV, radius_heuristics["portal_vein"])
        perf_HV = self._add_tolerance(perf_HV, radius_heuristics["hepatic_vein"])

        return {"hepatic_artery": perf_HA,
                "portal_vein": perf_PV,
                "hepatic_vein": perf_HV}
