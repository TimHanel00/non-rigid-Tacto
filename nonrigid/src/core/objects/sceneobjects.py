from typing import Optional, Dict, Any, List, Tuple
from core.objects.baseobject import BaseObject
from enum import Enum
import argparse

# multiple inheritance: left base class searched for methods first
class VolumetricOrgan(BaseObject):

    default_filename_oxygen_demand_map = "oxygenation_map.txt"
    default_filename_supply_map = "supply_map.txt"

    def __init__(
            self,
            *args,
            filename_oxygen_demand_map: str = "",
            filename_supply_map: str = "",
            voxel_resolution: float = 1.0,
            density: float = 1.05 * 1e3,
            blood_flow_per_mass: float = 1 * 1e-3 / 60,
            perforation_placement_aid_file: str = None,
            **kwargs
    ) -> None:
        """
        Base class for all objects that have a volume.

        Used to define the interface that lets an organ be vascularized with Vasculature scene objects.

        Args:
            filename_oxygen_demand_map: File name of the oxygen demand map to be generated from
                this organ's volume for VascuSynth
            filename_supply_map: File name of the oxygen supply map to be generated from
                this organ's volume for VascuSynth
            voxel_resolution: Width of one unit cube in the described 3D object
                given in meters. If source_file is given, resolution of this input file.
                For organ-like meshes this value will usually be 1.
            density: Physical density of the organ in kg/m^3 (SI units). Default is a literature
                value for the liver, 1.05 g/ml.
            blood_flow_per_mass: Blood flow though the organ per unit of mass in m^3 / (kg * s) (SI units).
                Default is a literature value for the liver, 100 ml / (100 g * min).
            perforation_placement_aid_file: Filename of a mesh that belongs to the same organ set
                and that can be used to help place perforation points on this organ.
        """
        self.filename_oxygen_demand_map = filename_oxygen_demand_map
        self.filename_supply_map = filename_supply_map
        self.voxel_resolution = voxel_resolution
        self.density = density
        self.blood_flow_per_mass = blood_flow_per_mass
        self.perforation_placement_aid_file = perforation_placement_aid_file

        super().__init__(
            *args,
            **kwargs
            )

    @staticmethod
    def update_parameters_from_templates(
            **kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        is_referenced = False
        # find out if this volumetric organ is referenced by Vasculature to be generated inside of it
        for template in kwargs["scene_object_templates"]:
            if "tag" in kwargs:
                if issubclass(template["obj_class"], Vasculature) and template["params"]["structure_tag"] == kwargs["tag"]:
                    is_referenced = True

        # if it is referenced, make sure the object receives proper default values
        if is_referenced:
            if not "filename_oxygen_demand_map" in kwargs:
                kwargs["filename_oxygen_demand_map"] = VolumetricOrgan.default_filename_oxygen_demand_map
            if not "filename_supply_map" in kwargs:
                kwargs["filename_supply_map"] = VolumetricOrgan.default_filename_supply_map

        # otherwise this value will be ignored anyway, one could remove the value altogether,
        # but it doesn't really matter
        return kwargs


class AbdominalWall(BaseObject):
    """ Scene object defining the AbdominalWall.
    """
    file_basename = "abdominal_wall"
    file_extension = "obj"

    def __init__(
        self,
        obj_id,
        fill_with_fat: bool = False,
        fat_amount: float = 0.5,
        fat_up_vector: tuple = (0,0,1),
        outset_amplitude: float = 0.01,
        outset_frequency: float = 5,
        **kwargs
    ) ->None:
        """  
        Args:
            fill_with_fat: Set to True if the AbdominalWall should be filled with fat
            fat_amount: The amount of DeformableOrgan that is covered with fat (0..1)
            fat_up_vector: The normal direction of the fat plane
                (TODO: how to sample vectors in the BaseObjectFactory?)
            outset_amplitude: Max amount each vertex is offset along its normal
            outset_frequency: Frequency of noise used for normal offset of each vertex
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file, tag
        """

        self.id = obj_id
        self.fill_with_fat = fill_with_fat
        self.fat_amount = fat_amount
        self.fat_up_vector = fat_up_vector
        self.outset_amplitude = outset_amplitude
        self.outset_frequency = outset_frequency

        super().__init__(
            self.id,
            file_basename = AbdominalWall.file_basename,
            file_extension = AbdominalWall.file_extension,
            **kwargs
            )

class FillFat(BaseObject):
    """ Scene object which fills the abdominal cavity (partially) with fat
    """
    file_basename = "abdominal_wall_fat"
    file_extension = "obj"

    def __init__(
        self,
        obj_id,
        fat_amount: float = 0.5,
        fat_up_vector: tuple = (0,0,1),
        source_file: str = "",
    ) ->None:
        """  
        Args:
            fat_amount: The amount of DeformableOrgan that is covered with fat (0..1)
            fat_up_vector: The normal direction of the fat plane
                (TODO: how to sample vectors in the BaseObjectFactory?)
        """

        self.id = obj_id
        self.fat_amount = fat_amount
        self.fat_up_vector = fat_up_vector

        super().__init__(
            self.id, 
            file_basename = FillFat.file_basename,
            file_extension = FillFat.file_extension,
            source_file = source_file
            )


class Ligament(BaseObject):
    """ Scene object defining a ligament.
    """
    file_basename = "ligament"
    file_extension = "obj"

    def __init__(
        self,
        obj_id,
        stiffness: float = 210,
        rest_length_factor: float = 1,
        **kwargs
    ) ->None:
        """  
        Args:
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file, tag
        """

        self.stiffness = stiffness
        self.rest_length_factor = rest_length_factor

        self.id = obj_id
        super().__init__(
            self.id,
            file_basename = Ligament.file_basename,
            file_extension = Ligament.file_extension,
            **kwargs
            )

class FixedAttachments(BaseObject):
    """ Scene object defining fixed attachment points (fixed constraint).
    """
    file_basename = "fixed_attachments"
    file_extension = "obj"

    def __init__(
        self,
        obj_id,
        surface_amount: float = 0.2,#tuple=(0.05, 0.5),
        **kwargs
    ) ->None:
        """  
        Args:
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file, tag
        """

        self.surface_amount = surface_amount

        self.id = obj_id
        super().__init__(
            self.id,
            file_basename = FixedAttachments.file_basename,
            file_extension = FixedAttachments.file_extension,
            **kwargs
            )
    
class RigidOrgan(VolumetricOrgan):
    """ Scene object defining a rigid object.
    """
    file_basename = "attached_organ"
    file_extension = "obj"

    def __init__(
        self,
        obj_id,
        rigid_transform: bool = True,
        **kwargs
    ) ->None:
        """  
        Args:
            obj_id: ID of the object as an uppercase character
            rigid_transform: If True, object will be moved randomly such that it does
                not intersect with the deformable organ. Set to False if position from
                source file should be maintained.
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file, tag
        """
        self.id = obj_id
        self.rigid_transform = rigid_transform

        super().__init__(
            self.id,
            file_basename = RigidOrgan.file_basename,
            file_extension = RigidOrgan.file_extension,
            **kwargs
            )

class DeformableOrgan(VolumetricOrgan):
    """ Scene object defining a deformable object.
    """

    file_basename = "surface"
    file_extension = "stl"

    def __init__(
        self,
        obj_id,
        young_modulus: float = 3000,# tuple = (3000, 3000),
        poisson_ratio: float = 0.45,# tuple = (0.4, 0.45),
        mass_density: float = 1, #tuple = (1.0, 1.0), 
        size_x: float = 0.3,
        size_y: float = 0.3,
        size_z: float = 0.3,
        add_concavity: bool = True,
        predeform_twist: bool = True,
        predeform_noise: bool = True,
        cut_to_fit: bool = True,
        **kwargs
    ) ->None:
        """  
        Args:
            young_modulus:
            poisson_ratio:
            mass_density:
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file, tag
        """

        self.young_modulus = young_modulus
        self.poisson_ratio = poisson_ratio
        self.mass_density = mass_density

        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z
        self.add_concavity = add_concavity
        self.predeform_twist = predeform_twist
        self.predeform_noise = predeform_noise
        self.cut_to_fit = cut_to_fit
        
        self.id = obj_id
        super().__init__(
            self.id,
            file_basename = DeformableOrgan.file_basename,
            file_extension = DeformableOrgan.file_extension,
            **kwargs
            )

class Force(BaseObject):
    """ Scene object defining a force to apply to a subset of surface nodes.
    """
    file_basename = "force"
    file_extension = "obj"

    def __init__(
        self, 
        obj_id,
        magnitude: float=0.1, 
        roi_radius: Optional[float] = None, 
        pull_only: bool=False,
        incremental: bool=False,
        ang_from_normal: Optional[float] = None,
        **kwargs
    ) ->None:
        """  
        Args:
            magnitude:
            roi_radius:
            pull_only:
            incremental:
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file, tag
        """

        self.magnitude = magnitude
        self.roi_radius = roi_radius
        self.pull_only = pull_only
        self.incremental = incremental
        self.ang_from_normal = ang_from_normal

        self.id = obj_id
        super().__init__(
            self.id,
            file_basename = Force.file_basename,
            file_extension = Force.file_extension,
            **kwargs
        )


class Vasculature(BaseObject):
    """ Scene object defining a vascular tree inside an object.
    """
    file_basename = "vasculature"
    file_extension = "obj"

    def __init__(
        self,
        obj_id,
        structure_tag: str = "",
        num_terminal_nodes: int = 90,
        pressure_gradient: float = 2.0 * 101325/760,
        curved: bool = False,
        num_cylinder_polygons: int = 20,
        num_spline_points: int = 20,
        percentile_max_branch_length: float = 75.0,
        **kwargs
    ) -> None:
        """
        Args:
            num_terminal_nodes: Number of terminal nodes to generate as the drainage of the
                vascular tree (at the smallest radius level).
            pressure_gradient: Difference in blood pressure from perforation point to desired finest level
                of detail in the vascular tree in N / m^2. Default is the value for the hepatic vein.
            curved: If 3D model should have curved branches for this vessel tree.
            num_cylinder_polygons: The number of sides for the 3D cylinder representation of each
                branch in the vascular tree.
            num_spline_points: Number of support points to use for the spline describing the 3D
                representation of the branch if it is curved.
            percentile_max_branch_length: Percentile of branch lengths which is considered the
                maximum branch length in the vascular tree. Used for 3D model creation. The
                maximum branch length is then used to decide which branches get a higher curvature
                (the longer, the curvier) -> the lower the percentile, the curvier the tree.
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file
        """

        self.id = obj_id
        self.structure_tag = structure_tag
        self.num_terminal_nodes = num_terminal_nodes
        self.pressure_gradient = pressure_gradient
        self.curved = curved
        self.num_cylinder_polygons = num_cylinder_polygons
        self.num_spline_points = num_spline_points
        self.percentile_max_branch_length = percentile_max_branch_length

        # pass on overriding arguments of subclasses
        file_basename = Vasculature.file_basename
        file_extension = Vasculature.file_extension
        if 'file_basename' in kwargs:
            file_basename = kwargs['file_basename']
            kwargs.pop('file_basename')
        if 'file_extension' in kwargs:
            file_extension = kwargs['file_extension']
            kwargs.pop('file_extension')

        super().__init__(
            self.id,
            file_basename=file_basename,
            file_extension=file_extension,
            **kwargs
        )

        # construct actual names for the additional files, not file patterns
        base_name, str_id = self.get_filename_elements()
        # file for the parametrisation of VascuSynth
        self.filename_parameters = self.construct_filename(filename=base_name + "_parameters",
                                                           postfix=str_id,
                                                           extension="txt")
        # vessel tree output of VascuSynth with node positions, edge radii etc.
        # do not use this after vessel tree creation has finished!
        self.filename_tree_struct_intermediate = self.construct_filename(filename=base_name + "_tree_intermediate",
                                                                         postfix=str_id,
                                                                         extension="gxl")
        # vessel tree information extended from VascuSynth output by edge length/curved branch arc length,
        # tortuosities etc.
        # only use this after vessel tree creation!
        self.filename_structure = self.construct_filename(filename=base_name + "_tree_structure",
                                                          postfix=str_id,
                                                          extension="graphml")

        # initialize values that can only be set later
        # Tuple[int, int, int] specifying the perforation point position in oxygen demand map coordinates
        self.perforation_point = None
        # blood flow through perforation point of the vessel tree in SI units (m^3 / s)
        self.perforation_flow = 0.0

    @classmethod
    def name_additional_files(cls) -> List[str]:
        # construct file patterns to match additional files that this scene object definition
        # will cause in the run of the program
        # file for the parametrisation of VascuSynth
        param_file = cls.construct_filename(postfix="_parameters", extension="txt")
        # vessel tree output of VascuSynth with node positions, edge radii etc.
        # do not use this after vessel tree creation has finished!
        struct_intermediate_file = cls.construct_filename(postfix="_tree_intermediate", extension="gxl")
        # vessel tree information extended from VascuSynth output by length/curved branch arc length,
        # tortuosities etc.
        # only use this after vessel tree creation!
        structure_file = cls.construct_filename(postfix="_tree_structure", extension="graphml")
        return [param_file, struct_intermediate_file, structure_file]

    @staticmethod
    def check_parameters(**kwargs) -> None:
        if "structure_tag" not in kwargs:
            raise RuntimeError("Vasculature scene object requires a valid organ tag "
                               "in the parameters! That is the target organ the vascular "
                               "tree should be generated into. Aborting.")

    @staticmethod
    def update_parameters_from_instances(
            **kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Read out information from containing organ scene object: File name, voxel resolution.
        """
        # raising AssertionErrors here so that they can be transformed into SampleProcessingExceptions
        # at a level where the sample is known
        assert 'referenced_structure' in kwargs, ("Structure tag got lost after generation parameter "
                                                  "checking but before the creation of the vascular tree "
                                                  "object!")

        assert len(kwargs["referenced_structure"]) == 1, (f"Only one structure tag should match the tag given to the " 
                                                          f"Vasculature scene object, but "
                                                          f"{len(kwargs['referenced_structure'])} match!")

        return kwargs

    def set_perforation_point(
            self,
            perforation_point: Tuple[int, int, int]
    ) -> None:
        """
        Args:
            perforation_point: Perforation point position in oxygen demand map coordinates.
        """
        self.perforation_point = perforation_point

    def set_perforation_flow(
            self,
            perf_flow: float
    ) -> None:
        """
        Args:
            perf_flow: Blood flow through perforation point of the vessel tree in SI units (m^3 / s).
        """
        self.perforation_flow = perf_flow


class PortalVein(Vasculature):
    """ Scene object defining defaults for the portal vein in the liver."""
    file_basename = "vasculature_portal_vein"
    file_extension = "obj"

    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        """
        Args:
            pressure_gradient: Difference in blood pressure from perforation point to desired finest level
                of detail in the vascular tree in N / m^2. Default is the value for the hepatic vein.
        """

        super().__init__(
            *args,
            file_basename=PortalVein.file_basename,
            file_extension=PortalVein.file_extension,
            **kwargs
        )

        # vessel specific defaults
        if "pressure_gradient" not in kwargs:
            self.pressure_gradient = 2.0 * 101325/760  # mmHg -> N/m^2



class HepaticVein(Vasculature):
    """ Scene object defining defaults for the hepatic vein in the liver."""

    file_basename = "vasculature_hepatic_vein"
    file_extension = "obj"

    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        """
        Args:
            pressure_gradient: Difference in blood pressure from perforation point to desired finest level
                of detail in the vascular tree in N / m^2. Default is the value for the hepatic vein.
        """

        super().__init__(
            *args,
            file_basename=HepaticVein.file_basename,
            file_extension=HepaticVein.file_extension,
            **kwargs
        )

        # vessel specific defaults
        if "pressure_gradient" not in kwargs:
            self.pressure_gradient = 2.0 * 101325/760  # mmHg -> N/m^2


class HepaticArtery(Vasculature):
    """ Scene object defining defaults for the hepatic artery in the liver."""

    file_basename = "vasculature_hepatic_artery"
    file_extension = "obj"

    # default values for sampling the pressure gradient
    # use {'pressure_gradient': (HepaticArtery.pressure_gradient_mu
    #                            HepaticArtery.pressure_gradient_sigma,
    #                            HepaticArtery.pressure_gradient_min,
    #                            HepaticArtery.pressure_gradient_max)}
    # as parameters for this scene object in order to sample from this default
    # truncated normal - the scene object generator block will take care of it
    pressure_gradient_mu = 42.5 * 101325 / 760  # mmHg -> N/m^2
    pressure_gradient_sigma = 8.75 * 101325 / 760  # mmHg -> N/m^2
    pressure_gradient_min = 25.0 * 101325 / 760  # mmHg -> N/m^2
    pressure_gradient_max = 60 * 101325 / 760  # mmHg -> N/m^2

    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        """
        Args:
            pressure_gradient: Difference in blood pressure from perforation point to desired finest level
                of detail in the vascular tree in N / m^2. Default is the value for the hepatic vein.
        """

        super().__init__(
            *args,
            file_basename=HepaticArtery.file_basename,
            file_extension=HepaticArtery.file_extension,
            **kwargs
        )

        # vessel specific defaults
        if "pressure_gradient" not in kwargs:
            # if nothing is sampled, use the mean
            self.pressure_gradient = 42.5 * 101325 / 760  # mmHg -> N/m^2

class Tumor(BaseObject):
    """ Scene object defining a tumor inside another object.
    """
    file_basename = "tumor"
    file_extension = "obj"

    def __init__(
        self,
        obj_id,
        size_x: float = 0.01,
        size_y: float = 0.01,
        size_z: float = 0.01,
        organ_file: str = "",
        structure_tag: str = "",
        **kwargs
    ) -> None:
        """
        Args:
            **kwargs: Keyword arguments to be passed on to BaseObject: source_file
        """

        self.id = obj_id
        self.organ_file = organ_file
        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z

        print("ORGAN FILE:", self.organ_file)

        super().__init__(
            self.id,
            file_basename=Tumor.file_basename,
            file_extension=Tumor.file_extension,
            **kwargs
        )

    @staticmethod
    def check_parameters(**kwargs) -> None:
        if "structure_tag" not in kwargs:
            raise RuntimeError("Tumor scene object requires a valid organ tag "
                               "in the parameters! That is the target organ the tumor "
                               "should be generated into. Aborting.")

    #@staticmethod
    #def update_parameters_from_instances(**kwargs):

    #    # raising AssertionErrors here so I can transform them into SampleProcessingExceptions
    #    # at a level where the sample is known
    #    assert 'structure_tag' in kwargs, ("Structure tag got lost after generation parameter "
    #                                   "checking but before the creation of the tumor object!" )

    #    assert len(kwargs["structure_tag"]) == 1, (f"Only one structure tag should match the tag given to the " 
    #                           f"tumor scene object, but {len(kwargs['structure_tag'])} match!")

    #    # what is passed to the structure tag here is a list of scene objects that
    #    # match the query tag. Now, extract the respective file name

    #    # TODO: Fix referencing!!
    #    kwargs["organ_file"] = kwargs["structure_tag"][0].filename
    #    return kwargs
    @staticmethod
    def update_parameters_from_instances(
            **kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Read out information from containing organ scene object: File name, voxel resolution.
        """
        # raising AssertionErrors here so that they can be transformed into SampleProcessingExceptions
        # at a level where the sample is known
        assert 'referenced_structure' in kwargs, ("Structure tag got lost after generation parameter "
                                                  "checking but before the creation of the vascular tree "
                                                  "object!")

        assert len(kwargs["referenced_structure"]) == 1, (f"Only one structure tag should match the tag given to the " 
                                                          f"Tumor scene object, but "
                                                          f"{len(kwargs['referenced_structure'])} match!")

        kwargs["organ_file"] = kwargs["referenced_structure"][0].filename
        return kwargs



