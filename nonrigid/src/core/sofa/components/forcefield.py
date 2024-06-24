import Sofa.Core
from enum import Enum

from core.sofa.components.topology import Topology

class ConstitutiveModel(Enum):
    """ 
    Class to define a constitutive model. 

    Available models: linear elastic, corotated, St Venant Kirchhoff, NeoHookean.
    """
    LINEAR = "Linear"
    COROTATED = "Corotated"
    STVENANTKIRCHHOFF = "SaintVenantKirchhoff"
    NEOHOOKEAN = "NeoHookean"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def member_from_value(cls, value):
        return cls._value2member_map_[value]

class Material: 
    """ 
    Class defining a material, composed of a constitutive model and its parameters.
    """
    def __init__(
        self, 
        constitutive_model: ConstitutiveModel = ConstitutiveModel.LINEAR, 
        poisson_ratio: float = 0.3, 
        young_modulus: float = 4000, 
        mass_density: float = 2.5
    ):
        """ 
        Args:
            constitutive_model: An instance of constitutive model.
            poisson_ratio: Poisson ratio.
            young_modulus: Young's modulus [Pa].
            mass_density: Object density [kg/m3].
        """

        if not isinstance(constitutive_model, ConstitutiveModel):
            assert ConstitutiveModel.has_value(constitutive_model), f"Received a non valid constitutive_model {constitutive_model}"
            constitutive_model = ConstitutiveModel.member_from_value(constitutive_model)

        assert constitutive_model in ConstitutiveModel, f"Received a non valid constitutive model {constitutive_model}"
        self.constitutive_model = constitutive_model
        self.poisson_ratio = poisson_ratio
        self.young_modulus = young_modulus
        self.mass_density = mass_density

        linear_models = [ConstitutiveModel.LINEAR, ConstitutiveModel.COROTATED]
        if constitutive_model in linear_models:
            m = ["small", "large"]
            self.method = m[ linear_models.index(constitutive_model) ]


# FEM
def add_forcefield(
    parent_node: Sofa.Core.Node,
    material: Material,
    topology: Topology,
    topology_link: str, 
    name: str = "FEM",
    use_caribou: bool = False,
) -> Sofa.Core.Object:
    """ 
    Adds the appropriate force field component depending on the specified topology and material.

    Args:
        parent_node: Parent node where the force field must be added. 
        material: An instance of Material.
        topology: An instance of Topology.
        topology_link: SOFA link to the SOFA topology component which has to be associated with a force field. 
        name: Name of the component.
        use_caribou: If True, uses components from the SofaCaribou plugin instead of default SOFA components. Note that SofaCaribou must be compiled externally.

    Returns:
        The created SOFA force field component.
    """

    # Elastic FEM
    if material.constitutive_model in [ConstitutiveModel.LINEAR, ConstitutiveModel.COROTATED]:
        
        # Tetrahedral components
        if topology == Topology.TETRAHEDRON:
            if use_caribou:
                ff = parent_node.addObject('TetrahedronElasticForce',
                                            youngModulus=material.young_modulus,
                                            poissonRatio=material.poisson_ratio,
                                            corotated=bool( material.constitutive_model == ConstitutiveModel.COROTATED ),
                                            topology_container=topology_link,
                                            name=name
                                        )
            else:
                ff = parent_node.addObject('TetrahedronFEMForceField',
                                            name=name,
                                            method=material.method,
                                            youngModulus=material.young_modulus,
                                            poissonRatio=material.poisson_ratio,
                                            listening=1,
                                            computeVonMisesStress = 0, # 2=using full Green tensor
                                            showVonMisesStressPerNode = 0
                                        )

        # Hexahedral components
        elif topology == Topology.HEXAHEDRON:
            if use_caribou:
                ff = parent_node.addObject('HexahedronElasticForce',
                                            youngModulus=material.young_modulus,
                                            poissonRatio=material.poisson_ratio,
                                            corotated=bool( material.constitutive_model == ConstitutiveModel.COROTATED ),
                                            topology_container=topology_link,
                                            name=name
                                        )
            else:
                ff = parent_node.addObject('HexahedralFEMForceField',
                                            name=name,
                                            youngModulus=material.young_modulus,
                                            poissonRatio=material.poisson_ratio,
                                        )
    # Hyperelastic FEM
    else:
        if use_caribou:
            ff = add_hyperelastic_caribou_forcefield(
                    parent_node=parent_node,
                    material=material,
                    topology=topology.value,
                    topology_link=topology_link,
                    name=name
                )
        else:
            assert topology == Topology.TETRAHEDRON, "Hyperelastic force field is not implemented in default SOFA, please use caribou components!"
            parameters = lame(material)
            ff = parent_node.addObject('TetrahedronHyperelasticityFEMForceField',
                                        ParameterSet=parameters, 
                                        materialName=material.constitutive_model.value,
                                        name=name
                                    )

    return ff

def add_hyperelastic_caribou_forcefield(
    parent_node: Sofa.Core.Node,
    material: Material,
    topology: Topology,
    topology_link: str,
    name: str = "FEM"
) -> Sofa.Core.Object:
    """ 
    Adds hyperelastic force field using components from SofaCaribou.

    Args:
        parent_node: Parent node where the force field must be added. 
        material: An instance of Material.
        topology: An instance of Topology.
        topology_link: SOFA link to the SOFA topology component which has to be associated with a force field. 
        name: Name of the component.

    Returns:
        The created SOFA force field component.
    """

    parent_node.addObject(f"{material.constitutive_model.value}Material", 
                        young_modulus=material.young_modulus, 
                        poisson_ratio=material.poisson_ratio, 
                        name=f"{material.constitutive_model.value}"
                        )
    
    ff = parent_node.addObject('HyperelasticForcefield', 
                                material=f"@{material.constitutive_model.value}", 
                                template=topology,
                                topology=topology_link,
                                name=name
                                )

    return ff

def lame(
    material: Material,
) ->list:
    """
    Given a material, converts the specified young modulus and poisson ratio into lame parameters,
    depending on the specified material (St Venant Kirchhoff or Neo-Hookean).

    Args:
        material: An instance of Material.
    
    Returns
        List with appropriate lame parameters, depending on the specified Material.
    """
    young_modulus = material.young_modulus
    poisson_ratio = material.poisson_ratio
    if material.constitutive_model == ConstitutiveModel.STVENANTKIRCHHOFF:
        mu = young_modulus / (2. * (1. + poisson_ratio))
        l = young_modulus * poisson_ratio / ((1. + poisson_ratio) * (1. - 2.*poisson_ratio))
        parameters = [mu,l]
    elif material.constitutive_model == ConstitutiveModel.NEOHOOKEAN:
        mu = young_modulus / (2. * (1. + poisson_ratio))
        K = young_modulus /(3 * (1. - 2.*poisson_ratio))
        parameters = [mu,K]
    return parameters

def from_lame(
    mu: float, 
    l: float,
) ->tuple:
    """
    Converts the specified lame parameters into young modulus and poisson ratio.

    Args:
        mu: First lame parameter.
        l: Second lame parameter.
    
    Returns
        Tuple with the corresponding poisson ratio and young modulus.
    """
    poisson_ratio = 1. / (2 * ((mu / l) + 1))
    young_modulus = 2*mu*(1 + poisson_ratio)
    return poisson_ratio, young_modulus