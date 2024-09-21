import Sofa
import Sofa.Core
import SofaRuntime

class GelScene:
    def __init__(self, vtk_file, tacto_mechanics):
        """
        GelScene manages the creation of a soft body and the physical scene,
        and attaches it to the rigid body of the TactoController using RigidMapping.

        :param vtk_file: The file path of the soft body's VTK file.
        :param tacto_mechanics: The rigid body mechanical object of the TactoController.
        """
        self.vtk_file = vtk_file
        self.tacto_mechanics = tacto_mechanics
        self.control_points_node = None

    def create_scene(self, root):
        """
        Creates the physical and visual scene for the soft Gel,
        adds it to the root node, and attaches it to the rigid TactoController via RigidMapping.
        """
        # Load necessary plugins
        root.addObject('RequiredPlugin', name='Sofa.Component.ODESolver.Backward')
        root.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')
        root.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')
        root.addObject('RequiredPlugin', name='Sofa.Component.Mass')
        root.addObject('RequiredPlugin', name='Sofa.Component.MechanicalLoad')

        # Load VTK file
        root.addObject('MeshVTKLoader', name='gelLoader', filename=self.vtk_file)

        # Create Gel node
        self.gel_node = root.addChild('Gel')

        # Use MeshTopology to store the topology
        self.gel_node.addObject('TetrahedronSetTopologyContainer', src='@../gelLoader')
        self.gel_node.addObject('TetrahedronSetTopologyModifier')

        # Add mechanical object to store position information
        self.gel_mechanical_object = self.gel_node.addObject('MechanicalObject', name='dofs', template='Vec3d',
                                                             position='@../gelLoader.position')

        # Add mass
        self.gel_node.addObject('UniformMass', totalMass=1.0)

        # Add force field
        self.gel_node.addObject('TetrahedronFEMForceField', template='Vec3d', youngModulus=1e8, poissonRatio=0.1)

        # Visual model
        visual = self.gel_node.addChild('VisualModel')
        visual.addObject('OglModel', name='visual', src='@../../gelLoader')

        # Create control points and add them
        self.control_points_node = root.addChild('ControlPoints')
        control_point_positions = [
            [0.01606825, -0.0073004, -0.01040069],  # Vertex 0
            [0.01606826, 0.00904162, -0.00634731],  # Vertex 1
            [0.01606825, -0.00914089, -0.00630023],  # Vertex 2
            [0.01606825, -0.00020875, -0.01380922],  # Vertex 3
            [0.01606825, 0.00446336, -0.01268844],  # Vertex 4
            [0.01606825, -0.0038385, -0.01296444],  # Vertex 5
            [0.01606825, 0.00758922, -0.00972445],  # Vertex 6
            [0.01606826, -0.00920764, 0.01042104],  # Vertex 7
            [0.01606826, -0.00845061, 0.01120982],  # Vertex 8
            [0.01606826, 0.00822222, 0.01122653],  # Vertex 9
            [0.01606826, 0.0090457, 0.01058317],  # Vertex 10
            [0.01606826, -0.00595934, -0.01160379],  # Vertex 13
            [0.0160683, -0.00822657, -0.00879856],  # Vertex 14
            [0.01606824, 0.0091181, -0.006134],  # Vertex 15
            [0.01606832, 0.00737474, -0.01022446],  # Vertex 17
            [0.01606826, -0.00916443, -0.00561236],  # Vertex 23
            [0.01606833, 0.00435365, -0.01267685],  # Vertex 26
            [0.01606828, 0.00182797, -0.0135791],  # Vertex 28
            [0.01606814, -0.00213384, -0.0135948],  # Vertex 30
            [0.01606826, -0.0091581, 0.010464],  # Vertex 34
            [0.01606826, -0.0082946, 0.01123847],  # Vertex 37
            [0.01606827, 0.00840058, 0.01122075],  # Vertex 41
            [0.01606825, 0.00916695, 0.0103632]  # Vertex 45
        ]

        self.control_points_mechanical_object = self.control_points_node.addObject('MechanicalObject',
                                                                                   template='Vec3d', name='MO',
                                                                                   position=control_point_positions)

        # Use RigidMapping to bind ControlPoints to the rigid body of TactoController
        self.control_points_node.addObject('RigidMapping', input=self.tacto_mechanics.getLinkPath(), output='@MO')

        # Use AttachConstraint to bind control points to the Gel vertices
        root.addObject('AttachConstraint',
                       object1='@ControlPoints/MO',
                       object2='@Gel/dofs',
                       indices1='0 1 2 3 4',
                       indices2='0 1 2 3 4')

        # Get the number of vertices in the Gel and generate an index list of all vertices
        num_gel_points = len(self.gel_mechanical_object.position)
        all_points_indices = ' '.join(map(str, range(num_gel_points)))

        # Add RestShapeSpringsForceField, including all Gel points
        self.gel_node.addObject('RestShapeSpringsForceField',
                                stiffness='0.1',
                                angularStiffness='1',
                                points=all_points_indices,  # Includes all Gel points
                                external_rest_shape='@dofs')
