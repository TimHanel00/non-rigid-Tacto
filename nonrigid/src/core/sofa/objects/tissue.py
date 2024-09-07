import numpy as np
import os
import vtk
from vtk import vtkDataSet
from vtk.util import numpy_support
from typing import Optional
from splib3.numerics import RigidDof
import Sofa.Core
from core.sofa.components.solver import TimeIntegrationType, ConstraintCorrectionType, SolverType, add_solver
from core.sofa.components.models import MappingType, add_collision_models, add_mapping
from core.sofa.components.topology import Topology, add_loader, add_topology
from core.sofa.components.forcefield import Material, add_forcefield
from utils.sofautils import get_bbox, check_valid_displacement, get_distance_np
from utils.vtkutils import has_tetra
from core.log import Log
import math
def read_mesh_file(location):
    location=os.path.join(os.getcwd(),location)
    """
    Reads a mesh file and returns a vtkUnstructuredGrid object.
    
    :param location: String representing the file path of the mesh file.
    :return: vtkUnstructuredGrid object containing the mesh data.
    """
    # Create a reader based on the file extension
    if location.endswith('.vtk'):
        reader = vtk.vtkUnstructuredGridReader()
    elif location.endswith('.vtu'):
        reader = vtk.vtkXMLUnstructuredGridReader()
    else:
        raise ValueError(f"Unsupported file format for '{location}'. Only .vtk and .vtu files are supported.")

    # Set the file name
    reader.SetFileName(location)

    # Read the file
    reader.Update()

    # Get the output data object
    output = reader.GetOutput()

    return output

class Tissue(Sofa.Core.Controller):
    """
    Class implementing a deformable tissue.
    """

    #########################################################
    ####### CREATION
    #########################################################
    def __init__(
                self, 
                parent_node: Sofa.Core.Node, 
                simulation_mesh: Optional[vtkDataSet]=None,
                simulation_mesh_filename: str ="",
                material: Optional[Material] = Material(),
                node_name: str = "Tissue",
                surface_mesh: Optional[str] = None,
                grid_resolution: list = [10,10,10],
                use_caribou: bool = False,
                solver: SolverType = SolverType.CG,
                analysis: TimeIntegrationType = TimeIntegrationType.EULER,
                collision: bool = False,
                check_displacement : bool =False,
                contact_stiffness: float = 10.0,
                collision_triangles: bool = True,
                collision_lines: bool 	  = True,
                collision_points: bool 	  = True,
                collision_spheres: bool   = False,
                mechanical: bool =True,
                collision_spheres_radius: float = 0.005,
                view: bool = False,
                senderD = None
                
    ):
        """ 
        Args:
            parent_node: Parent node to which the object is attached.
            simulation_mesh: Simulated object.
            simulation_mesh_filename: Full path to the mesh to simulate.
            material: .
            node_name: .
            surface_mesh: Full path to the surface mesh of the simulated object.
            grid_resolution: .
            use_caribou: .
            solver: .
            analysis: .
            collision: .
            contact_stiffness: .
            collision_triangles: .
            collision_lines: .
            collision_points: .
            collision_spheres: .
            collision_spheres_radius: .
            view: .        
        """
        if simulation_mesh_filename=="":
            print("Error no simulation mesh defined")
            return
        else:
            simulation_mesh=read_mesh_file(simulation_mesh_filename)
        super().__init__(self)
        self.check_displacement=check_displacement
        self.is_stable	  = True
        self.is_moving    = False
        self.surface_node=None
        self.stiffness=contact_stiffness
        self.dataSender=senderD
        # Check on caribou
        if use_caribou:
            # TODO check if caribou libraries are there. If not, use default components setting use_caribou to false
            #Log.log(module="Sofa", severity="WARN", "Trying to use caribou components!")
            raise NotImplementedError( "Trying to use caribou components, but these aren't implemented at the moment!" )

        # --------------------------------------------------#
        # Scene graph creation
        # --------------------------------------------------#
        tissue_node = parent_node.addChild(node_name)
        self.node = tissue_node
        parent_node.addObject("MeshSTLLoader",name="meshLoaderFine",filename="mesh/surface_A.stl")
        
        # Get mesh bounding box
        xmin, xmax, ymin, ymax, zmin, zmax = get_bbox( simulation_mesh.GetPoints().GetData() )
        self.bounding_box = [xmin, ymin, zmin, xmax, ymax, zmax]

        # Topology
        if has_tetra(simulation_mesh):
            Log.log(module="Sofa", msg="Tissue FEM will have tetrahedral topology")
            topology_type = Topology.TETRAHEDRON
            topology_loader = add_loader( parent_node=self.node,
                                         filename = simulation_mesh_filename,
                                         name = f"{node_name}_loader" 	
                                         )
        else:
            Log.log(module="Sofa", msg="Tissue FEM will have hexahedral topology")
            topology_type = Topology.HEXAHEDRON
            topology_loader = self.node.addObject('RegularGridTopology', 
                                                    name=f"{node_name}_grid_topology", 
                                                    min=self.bounding_box[:3],
                                                    max=self.bounding_box[3:],
                                                    n=grid_resolution
                                                    )
            if surface_mesh is None:
                surface_mesh = simulation_mesh		
        
        # Topology
        self.volume_topology = add_topology( parent_node=self.node,
                                            mesh_loader=topology_loader,
                                            topology=topology_type,
                                            name=f"{node_name}_topology"
                                            )

        # Mechanical object
        self.state = self.node.addObject('MechanicalObject', 
                                            src=self.volume_topology.getLinkPath(), 
                                            name="MechanicalObject_state", 
                                            template="Vec3d",
                                            showObject=False
                                            )
        self.transformWrapper=RigidDof(self.state)
        pos=self.transformWrapper.getPosition()
        angles=self.getAngles()
        if self.dataSender is not None:
            self.dataSender.updateTissue(pos,angles)
        self.fem = add_forcefield( parent_node=self.node,
                                    material=material,
                                    topology=topology_type,
                                    topology_link = self.volume_topology.getLinkPath(),
                                    use_caribou=use_caribou,
                                    ) 
        #self.node.addObject('UniformMass', 
                                #totalMass=1.0, 
                                #name='mass'
                                #)	
        self.node.addObject("MeshMatrixMass", name="Mass", massDensity=0.01)
        self.node.addObject('FixedConstraint', name="FixedConstraint", indices="3 39 64")
        #self.node.addObject('LinearSolverConstraintCorrection')
        # Force field
            

        # Solver
        self.node.addObject('EulerImplicitSolver', name="cg_odesolver")
        self.node.addObject("CGLinearSolver",iterations=20, tolerance=1e-2, threshold=1e-2)
        #self.node.addObject("PrecomputedConstraintCorrection")
        """
        add_solver( parent_node=self.node, 
                    analysis_type=analysis, 
                    solver_type=solver, 
                    solver_name="Solver",
                    add_constraint_correction=False,##used to be based on collision or nah but leads to error
                    constraint_correction=ConstraintCorrectionType.PRECOMPUTED #PRECOMPUTED, #UNCOUPLED
                    )"""

        # Surface mesh
        if surface_mesh is not None:
            surface_node_name = f"{node_name}Surface"
            surface_node = self.node.addChild(surface_node_name)
            self.surface_node=surface_node
            self.surface_node = surface_node

            #self.surface_mesh_loader = add_loader( parent_node=parent_node,
                                                    #filename = surface_mesh,
                                                    #name = f"{surface_node_name}_loader" 	
                                                    #)
            #add_mapping(parent_node=surface_node, mapping_type=MappingType.BARYCENTRIC)
            self.visual=tissue_node.addChild("Visual")
            self.visual.addObject("OglModel",name="VisualModel",src="@../../meshLoaderFine")
            self.visual.addObject("MechanicalObject",template="Vec3d",name="StoringVis",scale=1.0)
            self.visual.addObject("BarycentricMapping", name="VMapping", input="@../MechanicalObject_state", output="@VisualModel")
            #self.visual.addObject("BarycentricMapping", name="VMapping", input="@../MechanicalObject_state", output="@meshTransform")
            #self.visual.addObject("STLExporter",filename='mesh/surface_out.stl',position="@VisualModel.position",triangle="@VisualModel.triangles",exportEveryNumberOfSteps="10")
            
            # Visualization
            #if view:
                #self.visualize_surface(f"{surface_node_name}_loader")
        
            if collision:
                #tissue_node.addObject('PrecomputedConstraintCorrection') #, recompute=1)
                #tissue_node.addObject('TriangleCollisionModel', moving=1, simulated=1, contactStiffness=contact_stiffness, color=[0.56,0.56,0.56,0])
                #collision=tissue_node.addChild("Collision")
                #collision.addObject("Mesh",src="@../../meshLoaderFine")
                #collision.addObject("MechanicalObject",name="StoringForces",scale=1.0)
                #collision.addObject("TriangleCollisionModel",name="CollisionModel",contactStiffness=1.0)
                #collision.addObject("BarycentricMapping",name="CollisionMapping",input="@../MechanicalObject_state", output="@StoringForces")
                self.collision=self.node.addChild("Collision")
                self.collision.addObject("Mesh",src="@../../meshLoaderFine")
                self.collision.addObject("MechanicalObject",template="Vec3d",name="StoringForces",scale=1.0)
                self.collision.addObject("TriangleCollisionModel",name="CollisionModel",contactStiffness=self.stiffness)
                self.collision.addObject("BarycentricMapping",name="CollisionMapping",input="@../MechanicalObject_state", output="@StoringForces")

                print(" added collision models")
    def radTodeg(self,angle):
         return (angle*180)/math.pi
    def mapping(self):
        add_mapping(parent_node=self.surface_node, mapping_type=MappingType.BARYCENTRIC)
    #########################################################
    ####### SOFA-RELATED
    #########################################################
    def onSimulationInitDoneEvent(self, __):
        self.previous_pos = np.asarray(self.state.rest_position.value)
    def getAngles(self):
        from splib3.numerics.quat import Quat
        eulerAngles= Quat(self.transformWrapper.getOrientation().tolist()).getEulerAngles()
        return [round(self.radTodeg(el),4) for el in eulerAngles]
    def onAnimateEndEvent(self, __):
        # Check for simulation instability at the end of each time step
        #print(f'pos: {self.transformWrapper.getPosition()}')
        
        pos=self.transformWrapper.getPosition()
        angles=self.getAngles()
        if self.dataSender is not None:
            self.dataSender.updateTissue(pos,angles)
        return
        if(self.check_displacement):
            #print(type(self.state.position))
            current_pos = np.asarray(self.state.position.value)
            displ = current_pos - self.previous_pos
            self.previous_pos = current_pos
            
            self.is_stable, self.is_moving = check_valid_displacement(displ, low_thresh=1e-01, high_thresh=0.4)		

    def reset(self):
        with self.state.position.writeable() as positions:
            positions[:] = self.state.rest_position.value

    #########################################################
    ####### CUSTOM
    #########################################################
    def visualize_surface( self, color=[1, 1, 0.5, 1] ):
        self.surface_node.addObject('OglModel', name="VisualSurfaceOGL", src=self.surface_mesh_loader.getLinkPath(), color=color, listening=1)
        self.surface_node.addObject("BarycentricMapping", name="VMapping", input="@../MechanicalModel", output="@VisualModel")

    def compute_spherical_roi( self, center_position, radius ):
        if isinstance(center_position, list):
            center_position = np.asarray( center_position)
        center_position = center_position.reshape((1,-1))
        dist, idx = get_distance_np( center_position, self.state.position.value )
        indices = np.where(dist <= radius)[0]
        return indices.tolist()
    
    def reset_positions(self, indices):
        for i in indices:
            with self.state.position.writeable() as positions:
                positions[i] = self.state.rest_position.value[i]

        

