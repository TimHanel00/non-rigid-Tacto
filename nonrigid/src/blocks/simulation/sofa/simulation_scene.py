"""
Simulation of a deformable object with ligaments.
"""
import sys, os
import numpy as np
import time
from typing import Optional

print("PATH:", sys.path)
# SIMULATION
import Sofa
import SofaRuntime
import Sofa.Core
import Sofa.SofaGL
import Sofa.Gui

SofaRuntime.importPlugin("Sofa.Component")

#import Sofa.Components.Mass
from blocks.simulation.simulation_block import SimulationBlock
from core.datasample import DataSample

from core.sofa.components.header import add_scene_header
from core.sofa.components.forcefield import Material, ConstitutiveModel
from core.sofa.components.solver import SolverType, TimeIntegrationType
from core.sofa.objects.tissue import Tissue
from core.sofa.objects.boundaries import FixedBoundaries, SpringBoundaries
from core.sofa.objects.forces import NodalForce

from core.log import Log
from utils.sofautils import get_indices_in_roi, sofa2vtu
from core.objects.sceneobjects import DeformableOrgan, FixedAttachments, Ligament, Force
from utils.vtkutils import find_corresponding_indices, vtk2numpy

class SofaSimulation(Sofa.Core.Controller):

    def __init__(self, 
        root: Sofa.Core.Node, 
        sample: DataSample, 
        inputs: list,
        dt: float,
        gravity: float,
    ):
        super(SofaSimulation, self).__init__()

        # Load input files
        self.simulation_mesh_filename = os.path.join(os.getcwd(), sample.path, inputs[0]) 
        self.surface_filename         = os.path.join(os.getcwd(), sample.path, inputs[1])

        # Load simulation mesh in vtk format
        undeformed_simulation_mesh = list(sample.read_all(inputs[0]))
        assert len(undeformed_simulation_mesh) > 0, f"File {inputs[0]} not found!"
        assert len(undeformed_simulation_mesh) <= 1, f"Expected one file matching {inputs[0]}, " \
                                                     f"found {len(undeformed_simulation_mesh)}"
        self.undeformed_simulation_mesh = undeformed_simulation_mesh[0][1]
        assert self.undeformed_simulation_mesh.GetNumberOfPoints() > 0, f"{inputs[0]} is empty!"
        
        root.animate = True

        self.tissue = None
        self.root = root

        add_scene_header( 
                        root,
                        gravity = gravity,
                        dt = dt,
                        alarm_distance = None,
                        contact_distance = None,
                        friction = None,
                        background_color = [0,0,0,1],
                        visual_flags = ["showBehavior", "hideForceFields", "hideCollisionModels"],
                        )
                
        self.createGraph(root, sample)

    ## ------------------------------------------------------------------- ##
    ##                          SCENE CREATION                             ##
    ## ------------------------------------------------------------------- ##
    def createGraph(self, root, sample):

        #print("\n----------------\nScene information")

        # Create deformable organs
        organs = [so for so in sample.scene_objects if isinstance(so, DeformableOrgan)]
        if len(organs):
            for org in organs:
                material = Material(
                                    young_modulus = org.young_modulus,
                                    poisson_ratio = org.poisson_ratio,
                                    constitutive_model = ConstitutiveModel.COROTATED,
                                    mass_density = org.mass_density
                                )

                tissue = root.addObject( 
                                        Tissue(
                                            root,
                                            simulation_mesh=self.undeformed_simulation_mesh,
                                            simulation_mesh_filename=self.simulation_mesh_filename,
                                            material=material,
                                            node_name='Tissue',
                                            #grid_resolution=[8,2,6], # for simulation with hexa
                                            solver=SolverType.CG,
                                            analysis=TimeIntegrationType.EULER,
                                            surface_mesh=self.surface_filename, # e.g. surface for visualization or collision
                                            view=False,
                                            collision=False,
                                            )
                                        )					
                self.tissue = tissue

                assert len(self.tissue.volume_topology.position.value) > 0, "Volume topology has NOT been correctly initialized"
        else:
            raise ValueError("Need exactly one DeformableOrgan in the scene!")
        #print(f"Tissue has {len(self.tissue.volume_topology.position.value)} DOFs")

        # Get tissue dimensions
        tissue_xmin = tissue.bounding_box[0]
        tissue_xmax = tissue.bounding_box[3]
        tissue_ymin = tissue.bounding_box[1]
        tissue_ymax = tissue.bounding_box[4]
        tissue_zmin = tissue.bounding_box[2]
        tissue_zmax = tissue.bounding_box[5]

        
        #####################################
        # Fixed attachment points
        fixed_attachments = [so for so in sample.scene_objects if isinstance(so, FixedAttachments)]
        if len(fixed_attachments):
            for fixed in fixed_attachments:
                obj_list = list(sample.read_all(f"{fixed.filename}"))
                assert len(obj_list) > 0, f"Couldn't read from {fixed.filename}!"
                assert len(obj_list) <= 1, f"Too many files matching {fixed.filename}: {len(obj_list)} instead of 1!"
                obj = obj_list[0][1]

                assert obj.GetNumberOfPoints() > 0, f"{fixed.filename} is empty!"
                
                points = vtk2numpy(obj)
                
                fixed_indices = find_corresponding_indices(
                        mesh=self.undeformed_simulation_mesh, 
                        points=points
                        )
 
                #print("FIXED INDICES:", fixed_indices)
                self.fixed_indices = fixed_indices
                Log.log(module="SimulationBlock",
                        msg=f"Number of fixed points: {len(self.fixed_indices)}")
            
                boundaries = FixedBoundaries(
                                            parent_node=tissue.node,
                                            indices=self.fixed_indices,
                                            view=True,
                                            name=fixed.filename
                                        )

        #####################################
        # Spring attachment points (e.g., ligaments)
        self.springs = []
        ligaments = [so for so in sample.scene_objects if isinstance(so, Ligament)]
        if len(ligaments):
            for lig in ligaments:
                obj_list = list(sample.read_all(f"{lig.filename}"))
                assert len(obj_list) > 0, f"Couldn't read from {lig.filename}!"
                assert len(obj_list) <= 1, f"Too many files matching {lig.filename}: {len(obj_list)} instead of 1!"
                obj = obj_list[0][1]
                assert obj.GetNumberOfPoints() > 0, f"{lig.filename} is empty!"

                # Load 
                points = vtk2numpy(obj)

                # Find out how many springs this ligament is made of.
                # Every two points form one spring, so multiply number of points by 0.5:
                N_springs = int(points.shape[0]*0.5)
                if N_springs < 1:
                    continue

                for i in range(N_springs):
                    start_point = points[i*2]
                    end_point = points[i*2+1]
                    spring_indices = find_corresponding_indices(
                            self.undeformed_simulation_mesh, [start_point])
                    spring_end_positions = [end_point]
                    #print(f"Indices: {spring_indices}")
                    #print(f"End position: {spring_end_positions}")
                    #rest_length_factor = sample.get_config_value(SimulationBlock,
                            #"rest_length_factor", lig.filename)
                    spring_length = np.linalg.norm(end_point-start_point).item()
                    rest_length = spring_length*lig.rest_length_factor

                    springs = root.addObject(
                                                SpringBoundaries(tissue.node,
                                                                attached_object=tissue,
                                                                start_indices=spring_indices,
                                                                end_points=spring_end_positions,
                                                                name = lig.filename,
                                                                stiffness = lig.stiffness,
                                                                rest_length = rest_length,
                                                                incremental=False,
                                                                active=True,
                                                                view=True,
                                                                view_end_points=True,
                                                                )
                                                )
                    self.springs.append( springs )

        #####################################
        # Nodal force
        forces = [so for so in sample.scene_objects if isinstance(so, Force)]
        if len(forces):
            for f in forces:
                obj_list = list(sample.read_all(f"{f.filename}"))
                assert len(obj_list) > 0, f"Couldn't read from {f.filename}!"
                assert len(obj_list) <= 1, f"Too many files matching {f.filename}: {len(obj_list)} instead of 1!"
                obj = obj_list[0][1]
                assert obj.GetNumberOfPoints() > 0, f"{f.filename} is empty!"

                force_vector_points = vtk2numpy(obj)
                force_magnitude = force_vector_points[1]-force_vector_points[0]

                if f.roi_radius is not None:
                    force_indices = get_indices_in_roi(
                        positions=self.tissue.volume_topology.position.value,
                        center=force_vector_points[0],
                        radius=f.roi_radius
                        )
                else:
                    force_indices = find_corresponding_indices(
                            mesh=self.undeformed_simulation_mesh, 
                            points=[force_vector_points[0]]
                            )

                NodalForce(
                    parent_node=tissue.node,
                    indices=force_indices,
                    magnitude=force_magnitude
                )

        self.num_steps = 1
        self.deformedStates = []
        self.time = 0
        self.step = 0
        self.prevVel = None
        self.isInit = True
        self.root = root
        
        self.start_time = time.time()
        self.actual_simulation_time = 0.0


    def init(self):
        pass
        
    def onAnimateBeginEvent(self,__):
        pass

    def onAnimateEndEvent(self, event):
        sim_end = False
        
        # Check for simulation instability at the end of each time step
        if self.tissue.is_stable is False:
            Log.log(module="SimulationBlock", msg="Simulation is UNSTABLE", severity="WARN")
            sim_end = True    
    
        v = self.tissue.state.velocity.value
        v_mag = np.linalg.norm(v, axis=1)
        v_avg = v_mag.mean()
        #print("Average velocity:", vAvg)
        
        if v_avg < 0.001:
            sim_end = True

        # if self.prevVel:
        #     accelSum = 0
        #     for i, v in enumerate(vel):
        #         velDiff = np.linalg.norm( v - self.prevVel[i] )
        #         accelSum = accelSum + velDiff
        #     accelAvg = accelSum/len(vel)
        #     print("Average acceleration:", accelAvg)
        #     if vAvg < self.mean_velocity_thresh and accelAvg < self.mean_acceleration_thresh and self.step > self.min_simulation_steps:
        #         sim_end = True
        # self.prevVel = vel

        if sim_end:
            self.actual_simulation_time = time.time()-self.start_time
            self.root.animate.value = False
        
            
    def get_deformed_mesh(self):
        return sofa2vtu(self.tissue.state, self.undeformed_simulation_mesh)
        
    def reset(self):
        self.tissue.reset()
        sys.stdout.flush()
        return 0


