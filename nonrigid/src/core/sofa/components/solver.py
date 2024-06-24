import Sofa.Core
from enum import Enum

class SolverType(Enum):
    """  
    Class with possible types of linear solvers.
    """
    CG         = "CGLinearSolver"
    SOFASPARSE = "SparseLDLSolver"

    CARIBOU_CG  = "ConjugateGradientSolver"
    CARIBOU_LLT = "LLTSolver"

class TimeIntegrationType(Enum):
    """  
    Class with possible time integration types.
    """
    STATIC   = "StaticSolver"
    EULER    = "EulerImplicitSolver"

    # Caribou time integration schemes seem not to work with contacts
    CARIBOU_STATIC = "StaticODESolver"
    CARIBOU_EULER  = "BackwardEulerODESolver"

class ConstraintCorrectionType(Enum):
    """  
    Class with possible constraint correction types.
    """
    UNCOUPLED   = "UncoupledConstraintCorrection"
    LINEAR      = "LinearSolverConstraintCorrection"
    PRECOMPUTED = "PrecomputedConstraintCorrection"
    GENERIC     = "GenericConstraintCorrection"

def add_solver(
    parent_node: Sofa.Core.Node,
    solver_type: SolverType = SolverType.CG,
    analysis_type: TimeIntegrationType = TimeIntegrationType.EULER,
    solver_name: str = "Solver",
    rayleigh_stiffness: float = 0.1,
    rayleigh_mass: float = 0.1,
    linear_solver_iterations: int = 1000,
    linear_solver_threshold: float = 1e-8,
    linear_solver_tolerance: float = 1e-8,
    newton_iterations: int = 10,
    add_constraint_correction: bool = False,
    constraint_correction: ConstraintCorrectionType = ConstraintCorrectionType.LINEAR
) ->None:
    """  
    Adds the specified solver to the specified node.

    Args:
        parent_node: Node where the solver should be added.
        solver_type: Type of solver to add.
        analysis_type: Type of analysis to run (either static or dynamic simulation with Euler integration).
        solver_name: Name to associate to the solver component.
        rayleigh_stiffness: rayleigh stiffness coefficient, used in case of dynamic simulation.
        rayleigh_mass: rayleigh mass coefficient, used in case of dynamic simulation.
        linear_solver_iterations: Max number of allowed iterations for the linear solver.
        linear_solver_threshold: Minimum threshold for the linear solver.
        linear_solver_tolerance: Tolerance for the linear solver.
        newton_iterations: Number of Newton iterations to run, in case of static analysis.
        add_constraint_correction: if True, a constraint correction component will be added. 
            This means that the simulation should implement constraints with FreeMotionAnimationLoop.
        constraint_correction: Type of constraint correction to add.
    """
    
    # Analysis
    if analysis_type in [TimeIntegrationType.STATIC, TimeIntegrationType.CARIBOU_STATIC]:
        parent_node.addObject( 
                        analysis_type.value, 
                        newton_iterations=newton_iterations, 
                        correction_tolerance_threshold=1e-7, 
                        residual_tolerance_threshold=1e-7
                        )     
    elif analysis_type == TimeIntegrationType.EULER:
        parent_node.addObject(
                        analysis_type.value, 
                        rayleighMass=rayleigh_mass, 
                        rayleighStiffness=rayleigh_stiffness
                        )
    elif analysis_type == TimeIntegrationType.CARIBOU_EULER:
            parent_node.addObject(
                            analysis_type.value, 
                            rayleigh_mass=rayleigh_mass, 
                            rayleigh_stiffness=rayleigh_stiffness
                            )

    # Solver
    if solver_type == SolverType.CG:
        parent_node.addObject( 
                        solver_type.value, 
                        name=solver_name, 
                        iterations=linear_solver_iterations, 
                        threshold=linear_solver_threshold, 
                        tolerance=linear_solver_tolerance
                        )

    elif solver_type == SolverType.CARIBOU_CG:            
        parent_node.addObject( 
                        solver_type.value, 
                        name=solver_name, 
                        maximum_number_of_iterations=linear_solver_iterations, 
                        residual_tolerance_threshold=linear_solver_threshold, 
                        preconditioning_method="Diagonal",
                        #printLog=1
                        )

    elif solver_type == SolverType.SOFASPARSE:
        parent_node.addObject(
                        solver_type.value, 
                        name=solver_name
                        )

    elif solver_type == SolverType.CARIBOU_LLT:
        parent_node.addObject(
                        solver_type.value, 
                        name=solver_name
                        )
    else:
        raise NotImplementedError(f"No implementation for solver type {solver_type}.")

    if add_constraint_correction:
        parent_node.addObject(constraint_correction.value)#, recompute=1 )