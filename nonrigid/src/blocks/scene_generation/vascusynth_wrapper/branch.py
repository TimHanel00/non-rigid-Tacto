import numpy as np
from math import dist
from abc import ABC, abstractmethod
from vtk import (
    vtkDataObject,
    vtkPoints,
    vtkLineSource,
    vtkParametricSpline,
    vtkParametricFunctionSource
)
from typing import Tuple

# edge structure needs to be kept in sync with VascularTree class.
# Edge and node should be defined as dataclass and NamedTuple,
# need to think about here or in vascular_tree.py.
# Not great, but not fixing. Structure may change anyway
# in order to get rid of python for.

class Branch(ABC):
    """
    Abstract interface for all potential branch shapes
    used in the VascularTree class.

    A branch is described by a centerline and a radius.
    The centerline is a curve in R^3 that is parametrized
    by some curve parameter t in [0, 1].

    To avoid intersections between consecutive branches,
    the curve parameter can be restricted to some interval
    [t_min, t_max], with t_min > 0 and t_max < 1.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    def __init__(self, edge: dict):
        """
        Args:
            edge: A dict that describes the underlying edge.
                Edges are assumed to be stored using
                the same convention as in the VascularTree class.
        """

        self.t_min = 0.0
        self.t_max = 1.0
        self.radius = edge["radius_avg"]

        self.source_id = edge["source_id"]
        self.target_id = edge["target_id"]

    @abstractmethod
    def evaluate(self, t: float) -> np.array:
        """
        Evaluates the centerline curve at a given curve parameter.

        Args:
            t: the curve parameter at which to evaluate the curve
        """

        pass

    @abstractmethod
    def get_source(self) -> vtkDataObject:
        """
        Produces a vtkDataObject that makes the centerline curve available
        for use with VTK.
        The curve is evaluated for values of the curve parameter t between
        t_min and t_max.
        """

        pass

    def swap_orientation(self) -> None:

        self.source_id, self.target_id = self.target_id, self.source_id
        self.t_min, self.t_max = 1.0 - self.t_max, 1.0 - self.t_min

    def get_min_endpoint(self) -> np.array:
        
        return self.evaluate(self.t_min)

    def get_max_endpoint(self) -> np.array:
        
        return self.evaluate(self.t_max)

    def __str__(self):
        return(f"{self.__class__} from node {self.source_id} to node {self.target_id}")


class StraightBranch(Branch):
    """
    Generates VTK source for straight vessel centerlines.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    def __init__(self, edge: dict, p1: np.array, p2: np.array) -> None:
        
        super(StraightBranch, self).__init__(edge)
        self.p1 = p1
        self.diff = p2 - p1

    def evaluate(self, t: float) -> np.array:

        return self.p1 + t * self.diff

    def get_source(self) -> vtkDataObject:

        line_source = vtkLineSource()
        line_source.SetPoint1(self.evaluate(self.t_min))
        line_source.SetPoint2(self.evaluate(self.t_max))
        return line_source


class CurvedBranch(Branch):
    """
    Generates a VTK source for vessel centerlines
    in the shape of sine-generated curves.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    def __init__(self, edge: dict, spline_points: np.array) -> None:

        super(CurvedBranch, self).__init__(edge)

        # Interpolate the evaluated points using a parametric spline
        self.spline = self._get_spline(spline_points)
        self.spline_points = spline_points
        self.n_points = spline_points.shape[0]

    def _get_spline(self, spline_points: np.array) -> vtkParametricSpline:
        """
        Helper method that generates a vtkParametricSpline
        from spline points.

        Args:
            spline_points: an array of spline points to interpolate
        """

        points_vtk = vtkPoints()

        for point in spline_points:
            points_vtk.InsertNextPoint(point)

        spline = vtkParametricSpline()
        spline.SetPoints(points_vtk)

        return spline

    def evaluate(self, t: float) -> np.array:

        t = np.array([t, 0.0, 0.0])
        Pt = np.array([0.0, 0.0, 0.0])
        Du = np.ndarray((9, ))
        self.spline.Evaluate(t, Pt, Du)
        return Pt

    def get_source(self) -> vtkDataObject:
        ts = np.linspace(self.t_min, self.t_max, len(self.spline_points))
        points_restricted = np.array([self.evaluate(t) for t in ts])

        spline = self._get_spline(points_restricted)
        function_source = vtkParametricFunctionSource()
        function_source.SetUResolution(len(points_restricted))
        function_source.SetParametricFunction(spline)
        function_source.Update()

        return function_source


class BranchFactory(ABC):
    """
    Abstract interface for all potential branch factories
    used in the VascularTree class.
    Branch factories generate Branch instances
    based on edges in a vessel tree.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    @abstractmethod
    def produce(
            self,
            source_node: Tuple[float, float, float],
            target_node: Tuple[float, float, float],
            edge: dict,
    ) -> Branch:
        """
        Returns a Branch instance corresponding to the
        vessel branch described by the edge parameter.
        Tubes of the correct radii are generated
        based on this branch by the VascularTree class.

        This method assumes edges to be stored as a dict, using
        the same convention as in the VascularTree class.

        Args:
            source_node: Position of the source node of the branch as (x, y, z)
            target_node: Position of the target node of the branch as (x, y, z)
            edge: the edge for which to generate a centerline
        """

        pass


class StraightFactory(BranchFactory):
    """
    Generates Branch instances that represent vessel branches
    with straight centerlines.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    def produce(
            self,
            source_node: Tuple[float, float, float],
            target_node: Tuple[float, float, float],
            edge: dict,
    ) -> Branch:

        return StraightBranch(edge, np.array(source_node), np.array(target_node))


class SineGeneratedFactory(BranchFactory):
    """
    Generates Branch instances that represent vessel branches
    with sine-generated curves as centerlines.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    # mathematical constraint of definin the branch shape like this:
    # if omega_max becomes bigger than this the branch will fold
    # do not increase this value
    min_omega_max = 2.1

    def __init__(self, max_length: float, num_spline_points: int) -> None:
        """
        Args:
            max_length: The maximum branch length that
                occurs in the vascular tree
        """

        self.max_length = max_length
        self.num_spline_points = num_spline_points

    def _get_parameters(self, distance: float, height: float) -> Tuple[float, float]:
        """
        Computes the arc length and a suitable curve angle omega
        for a sine-generated curve.

        Args:
            distance: distance of the endpoints of an edge
            height: the maximum possible height that the curved branch can take
                on before intersecting other vessel trees

        Returns:
            L: the arc length for the sine-generated curve
            omega: the maximum angle of the curve's tangent and the x-axis
        """

        # Use an approximate formula to compute the maximum possible value
        # of omega given the height and length of a branch bounding box
        # not parametrized in constructor because values come from math. derivation
        a = 0.48680767
        b = 0.65082038
        omega_max = 1 / b * np.arctan(height / (distance * a))
        # if omega_max becomes bigger the branch will fold
        omega_max = min(omega_max, self.min_omega_max)

        # Determine a suitable value of omega from omega_max
        weight = min(distance / self.max_length, 1.0)
        omega = omega_max * weight * np.random.uniform(0.0, 1.0)

        # Taylor expansion around omega = 0 of int_0^2pi cos(omega * sin(u)) du
        # not parametrized in constructor because values come from math. derivation
        taylor_polynomial = np.pi * (2 - omega**2 / 2.0 + omega**4 / 32.0 - omega**6 / 1152.0)
        L = 2.0 * np.pi * distance / taylor_polynomial
        return L, omega

    def produce(
            self,
            source_node: Tuple[float, float, float],
            target_node: Tuple[float, float, float],
            edge: dict,
    ) -> Branch:

        dir_x = edge["curveDirection_X"]
        dir_y = edge["curveDirection_Y"]
        dir_z = edge["curveDirection_Z"]
        curve_dir = np.array((dir_x, dir_y, dir_z))

        # Find source and target position, as well as their distance
        p1 = np.array(source_node)
        p2 = np.array(target_node)
        distance = dist(p1, p2)
        branch_dir = (p2 - p1) / distance  # unit vector in branch direction

        # Compute curve parameters
        L, omega = self._get_parameters(distance, edge["curveHeight"])
        edge["tortuosity"] = L / distance

        # Number of spline points, excluding p1 and p2.
        # Due to the limited precision of the integration procedure,
        # it is best to add the endpoints explicitly.
        points = np.zeros((self.num_spline_points + 2, 3))

        # Iteratively evaluate the integral representation
        # of a sine-generated curve (x(t), y(t))
        ts, dt = np.linspace(0.0, L, self.num_spline_points, retstep=True, endpoint=False)
        x_t, y_t = 0.0, 0.0

        points[0] = p1  # Start the curve at source point
        points[-1] = p2  # End the curve at target point

        for i, t in enumerate(ts):

            x_t += np.cos(omega * np.sin(2.0 * np.pi * t / L)) * dt
            y_t += np.sin(omega * np.sin(2.0 * np.pi * t / L)) * dt
            # Compute 3D coordinates from x_t, y_t and add the 3D point
            points[i + 1] = p1 + x_t * branch_dir + y_t * curve_dir

        return CurvedBranch(edge, points)

