import Sofa.Core
from blocks.simulation.sofa.simulation_scene import SofaSimulation
from core.datasample import DataSample
class CostumController(SofaSimulation):
    
    def __init__(self, 
        root: Sofa.Core.Node, 
        sample: DataSample, 
        inputs: list,
        dt: float,
        gravity: float,):
        
        
         ## These are needed (and the normal way to override from a python class)
                    #plugins = "SofaImplicitOdeSolver SofaLoader SofaOpenglVisual SofaBoundaryCondition SofaGeneralLoader SofaGeneralSimpleFem CImgPlugin"
        urdfNode = root.addChild('URDFNode')
        
        urdfNode.addObject('EulerImplicitSolver', name='cg_odesolver')
        urdfNode.addObject('CGLinearSolver', name='linear_solver')
        urdfNode.addObject('MeshSTLLoader', name='meshLoader', filename='../tacto/meshes/digit.STL')
        urdfNode.addObject('OglModel', src='@meshLoader', name='visual')
        #urdfNode.addObject('UniformMass', totalMass='1.0')
        #urdfNode.addObject('UncoupledConstraintCorrection')
        urdfNode.addObject("MechanicalObject", template="Rigid3", name="transform")
        #urdfNode.addObject("RigidRigidMapping", name="map", initialPoints=urdfNode.transform.findData("rest_position").getLinkPath()) 
        
        super().__init__(root,sample,inputs,dt,gravity)
        self.tactileSensor=urdfNode
        print(" Python::__init__::"+str(self.name))
        """
    def getOrgan(self):
         return self.tissue
    def getSensor(self):
         return self.tactileSensor
    def onEvent(self, event):
         This function is the fallback one that is called if the XXXX event is
            received but there is not overriden onXXXX() method.
        
         print("generic event handler catched ", event)
        """
    def onAnimateBeginEvent(self, event):
         print("onAnimateBeginEvent")

    def translate(x, t):
        p = x[0:3]
        q = x[3:]
        return [p[0]+t[0], p[1]+t[1], p[2]+t[2]]+q
    def onKeypressedEvent(self, c):
        o = None
        p = None
        print("awdiojawoid")
        if c == 'UP':
                o=0.1
        elif c == 'DOWN':
                o=-0.1          
        
        if o is not None:
                # Open/Close the cissor. 
                q = self.tactileSensor.transform.rest_position[0]
                self.tactileSensor.transform.rest_position = self.translate(q,[o,0.0,0.0])

        if p is not None:
                ## Move along X the cissor
                q = self.tactileSensor.transform.position[0]
                self.tactileSensor.transform.position = self.translate(q,[p,0.0,0.0])
#def createScene(rootNode):
    #controller = MyController(name="MyC")
    #rootNode.addObject(controller)