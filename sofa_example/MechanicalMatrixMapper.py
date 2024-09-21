# This Python scene requires the SofaPython3 plugin
#
# This scene shows the use of MechanicalMatrixMapper. A beam made of hexahedrons is simulated. One part is
# deformable, while the other is rigid.
#
# To achieve this behavior, the two parts are defined independently. The deformable part (respectively the rigid part)
# is defined with vec3 (respectively rigid) degrees of freedom. The two parts are joined as a single object using a
# mapping, which has both parts as input. The FEM is really computed in the mapped node. The deformable part is just a
# subset of the FEM degrees of freedom, while the rigid part is mapped on the rigid degree of freedom.
#
# SOFA does not transfer the mapped stiffness matrix naturally (on an assembled linear system). The FEM in the mapped
# node must be transferred to the global matrix system using MechanicalMatrixMapper. Otherwise, the derivatives of the
# FEM forces are considered null.
#

import Sofa
import numpy as np


def getComplementaryIndices(bwhole, b1, b2):  # Return indices of set bwhole/(b1|b2)
    ind_list = []
    for ind in bwhole.indices.value:
        if (not (ind in b1.indices.value)) and (not (ind in b2.indices.value)):
            ind_list.append(ind)
    return ind_list


def getComplementaryPointsInROI(bwhole, b1, b2):  # Return pointsInROI of set bwhole/(b1|b2)
    point_list = []
    for ind in bwhole.indices.value:
        print(str(ind))
        if (not (ind in b1.indices.value)) and (not (ind in b2.indices.value)):
            print("At index " + str(ind) + " point is " + str(bwhole.pointsInROI[ind][0]))
            point = bwhole.pointsInROI[ind]
            print(str(type(bwhole.pointsInROI[ind])))
            point_list.append(point.tolist())
            print(str(type(point_list)))
    print("Got all points!")
    return point_list


def createScene(rootNode):
    rootNode.gravity = [0, 0, -9.81]
    rootNode.addObject('RequiredPlugin', name='SofaSparseSolver')
    rootNode.addObject('RequiredPlugin', name='SofaBoundaryCondition')
    rootNode.addObject('RequiredPlugin', name='SofaDeformable')
    rootNode.addObject('RequiredPlugin', name='SofaEngine')
    rootNode.addObject('RequiredPlugin', name='SofaGeneralEngine')
    rootNode.addObject('RequiredPlugin', name='SofaGeneralAnimationLoop')
    rootNode.addObject('RequiredPlugin', name='SofaImplicitOdeSolver')
    rootNode.addObject('RequiredPlugin', name='SofaRigid')
    rootNode.addObject('RequiredPlugin', name='SofaMiscMapping')
    rootNode.addObject('RequiredPlugin', name='SofaSimpleFem')

    rootNode.addObject('VisualStyle',
                       displayFlags='showCollisionModels showBehaviorModels hideMappings showForceFields')
    rootNode.addObject('DefaultAnimationLoop')
    rootNode.addObject('DefaultVisualManagerLoop')

    meshDivision = rootNode.addChild('meshDivision')
    meshDivision.addObject('RegularGridTopology', name='topology', n=[12, 12, 3], min=[-0.5, 0.0, -0.05],
                           max=[0.5, 1.0, 0.05])
    meshOfStructure = meshDivision.addObject('MeshTopology', name='foamMesh', src="@topology")
    meshDivision.addObject('MechanicalObject', name="structureMO", template='Vec3d')
    boxWhole = meshDivision.addObject('BoxROI', template="Vec3d", name='box_roi_whole',
                                      box=[-0.51, -0.01, -0.11, 0.51, 1.01, 0.11], position="@beamMesh.position",
                                      drawBoxes=True)
    boxRigid = meshDivision.addObject('BoxROI', template="Vec3d", name='box_roi_rigid',
                                      box=[-0.1, 1.01, -0.1, 0.1, 0.9, 0.1], position="@beamMesh.position",
                                      drawBoxes=True)
    boxRigid2 = meshDivision.addObject('BoxROI', template="Vec3d", name='box_roi_rigid2',
                                       box=[-0.1, -0.01, -0.1, 0.1, 0.1, 0.1], position="@beamPart1Mech.position",
                                       drawBoxes=True)
    # boxDeformable= meshDivision.addObject('BoxROI',template="Vec3d", name='box_roi_deformable', box=[-0.51, 0.1001, -0.11, 0.51, 0.8999, 0.11], position="@beamMesh.position", drawBoxes=True )

    SolverNode = rootNode.addChild('SolverNode')
    SolverNode.addObject("EulerImplicitSolver", name="odeSolver", rayleighStiffness="0.1", rayleighMass="0.1",
                         vdamping="1.0")
    SolverNode.addObject('SparseLDLSolver', name="ldlsolveur", template="CompressedRowSparseMatrixd")


def createScene2(rootNode):
    #####   RECALL VALUES FROM FIRST INIT PART (They will be used in this function)
    meshOfStructure = rootNode.meshDivision.foamMesh
    meshDivision = rootNode.meshDivision
    boxRigid = rootNode.meshDivision.box_roi_rigid
    boxRigid2 = rootNode.meshDivision.box_roi_rigid2
    SolverNode = rootNode.SolverNode

    # Perform computations related to the complementary to (B1|B2) in Bwhole
    # (in order to get indices and nodal coords for the deformable part)
    defObjPos = getComplementaryPointsInROI(rootNode.meshDivision.box_roi_whole, rootNode.meshDivision.box_roi_rigid,
                                            rootNode.meshDivision.box_roi_rigid2)
    defObjInd = getComplementaryIndices(rootNode.meshDivision.box_roi_whole, rootNode.meshDivision.box_roi_rigid,
                                        rootNode.meshDivision.box_roi_rigid2)

    # We have to put the MechanicalMatrixMapper in this second part of the scene, since the nodes (deformablePartNode, RigidNode) are declared here
    SolverNode.addObject('MechanicalMatrixMapper', name="MechanicalMatrixMapper1", template='Vec3d,Rigid3d',
                         fastMatrixProduct=True,
                         object1='@./deformablePartNode/beamPart1Mech',
                         object2='@./RigidNode/rigid1',
                         nodeToParse='@./deformablePartNode/FEMNode')
    SolverNode.addObject('MechanicalMatrixMapper', name="MechanicalMatrixMapper2", template='Vec3d,Rigid3d',
                         fastMatrixProduct=True,
                         object1='@./deformablePartNode/beamPart1Mech',
                         object2='@./RigidNode2/rigid2',
                         nodeToParse='@./deformablePartNode/FEMNode')

    #####   Deformable Part of the object (Main Body)
    deformablePartNode = SolverNode.addChild('deformablePartNode')
    # We cannot do
    # deformablePartNode.addObject('MechanicalObject', template='Vec3d',name='beamPart1Mech', position="@"+boxDeformable.getPathName()+".pointsInROI")
    # since the deformable DOFs cannot be created using just a BoxROI. We use the complementary instead:
    deformablePartNode.addObject('MechanicalObject', template='Vec3d', name='beamPart1Mech', position=defObjPos)

    #####   Rigid Part of the object (Top)
    RigidNode = SolverNode.addChild('RigidNode')
    RigidNode.addObject("MechanicalObject", template="Rigid3d", name="rigid1", position=[0, 1, 0, 0, 0, 0, 1],
                        showObject=True, showObjectScale=0.1)
    RigidNode.addObject('FixedConstraint', indices='0')

    RigidifiedNode = RigidNode.addChild('RigidifiedNode')
    RigidifiedNode.addObject("MechanicalObject", name="rigidMecha", template="Vec3d",
                             position="@" + boxRigid.getPathName() + ".pointsInROI")
    RigidifiedNode.addObject("RigidMapping", globalToLocalCoords="true")

    #####   Rigid Part of the object 2 (Top)
    RigidNode2 = SolverNode.addChild('RigidNode2')
    RigidNode2.addObject("MechanicalObject", template="Rigid3d", name="rigid2", position=[0, 0, 0, 0, 0, 0, 1],
                         showObject=True, showObjectScale=0.1)
    RigidNode2.addObject('FixedConstraint', indices='0')

    RigidifiedNode2 = RigidNode2.addChild('RigidifiedNode2')
    RigidifiedNode2.addObject("MechanicalObject", name="rigidMecha", template="Vec3d",
                              position="@" + boxRigid2.getPathName() + ".pointsInROI")
    RigidifiedNode2.addObject("RigidMapping", globalToLocalCoords="true")

    #####   Combined object
    FEMNode = deformablePartNode.addChild('FEMNode')
    RigidifiedNode.addChild(FEMNode)
    RigidifiedNode2.addChild(FEMNode)

    FEMNode.addObject('MeshTopology', name='meshInput', src="@" + meshOfStructure.getPathName())
    FEMNode.addObject('MechanicalObject', template='Vec3d', name='beamMecha')
    FEMNode.addObject('HexahedronFEMForceField', name='HexaFF', src="@meshInput", poissonRatio=0.3, youngModulus=10000,
                      method="polar")
    FEMNode.addObject('MeshMatrixMass', massDensity='50')

    # We remove the external force on the object
    # FEMNode.addObject('BoxROI', name='corner', box=[0.5, 0.8, -0.5, 1, 1, 0.5], drawBoxes="2")
    # FEMNode.addObject('ConstantForceField', name='xMoins', indices='@corner.indices', force=[50, 0, 0])

    # Perform pairs computation and mapping
    meshDivision.init()
    boxRigid.init()
    boxRigid2.init()
    index_pairs = [[0, 0]] * len(meshOfStructure.position)

    i = 0
    for index in defObjInd:  # instead of boxDeformable.indices.value:
        index_pairs[index] = [0, i]
        i += 1
    i = 0
    for index in boxRigid.indices.value:
        index_pairs[index] = [1, i]
        i += 1
    i = 0
    # print(str(index_pairs))
    for index in boxRigid2.indices.value:
        index_pairs[index] = [2, i]
        i += 1
    # print("==========")
    # print(str(index_pairs))

    FEMNode.addObject("SubsetMultiMapping", name="subsetMapping", template="Vec3d,Vec3d",
                      input="@../beamPart1Mech @../../RigidNode/RigidifiedNode/rigidMecha @../../RigidNode2/RigidifiedNode2/rigidMecha",
                      output="@./beamMecha",
                      indexPairs=index_pairs)

    # Use controller to move the grippers
    RigidNode.addObject(
        ControlParticles(name="MouvementPinces", Particle1=RigidNode.rigid1, Particle2=RigidNode2.rigid2,
                         root=rootNode))

    return rootNode


class ControlParticles(Sofa.Core.Controller):
    def __init__(self, *args, **kwargs):
        # These are needed (and the normal way to override from a python class)
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.Particle1 = kwargs.get("Particle1")
        self.Particle2 = kwargs.get("Particle2")
        self.root = kwargs.get("root")
        self.time = 0.0

    def onAnimateBeginEvent(self, event):  # Compute gripper poses for the next time step
        self.time += self.root.dt.value
        # print('Time: ' + str(self.time)) # For debug
        pos1, pos2 = generator(self.time)
        # print('Computed poses, pos1: ' + str(pos1)) # For debug
        with self.Particle1.position.writeableArray() as wa1:
            wa1[0] = pos1
        with self.Particle2.position.writeableArray() as wa2:
            wa2[0] = pos2
        return 0;

    def onKeypressedEvent(self, event):
        key = event['key']
        if key == "-":
            print("Reset key was pressed!")
            self.time = 0.0
        return 0


def generator(t, tmin=0, tmax=5):  # Makes the same motion than the data files
    t = (t - tmin) / (tmax - tmin)
    if t > 1:
        t = 1
    y1 = 1 - 0.05 * (10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5)
    y2 = 0.05 * (10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5)
    qw = 1 - 0.05 * (10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5)
    qx1 = np.sqrt(1 - qw ** 2)
    qx2 = -np.sqrt(1 - qw ** 2)
    pos1 = [0, y1, 0, qx1, 0, 0, qw]
    pos2 = [0, y2, 0, qx2, 0, 0, qw]
    return pos1, pos2


def main():
    import SofaRuntime
    import Sofa.Gui
    # Make sure to load all SOFA libraries
    SofaRuntime.importPlugin("SofaBaseMechanics")
    SofaRuntime.importPlugin("SofaOpenglVisual")

    # Create the root node
    root = Sofa.Core.Node("root")
    # Call the below 'createScene' function to create the scene graph
    # The call is made separately because 'structureMO' must be initialized in order to perform complementary ROI computation
    createScene(root)
    Sofa.Simulation.init(root)
    # Now 'structureMO' is filled with nodal coordinates and we can perform getComplementaryIndices() and getComplementaryPointsInROI()
    createScene2(root)
    Sofa.Simulation.init(root)

    # Launch the GUI (qt or qglviewer)
    Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
    Sofa.Gui.GUIManager.createGUI(root, __file__)
    Sofa.Gui.GUIManager.SetDimension(1080, 1080)
    # Initialization of the scene will be done here
    Sofa.Gui.GUIManager.MainLoop(root)
    Sofa.Gui.GUIManager.closeGUI()
    print("Simulation is done.")


# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()