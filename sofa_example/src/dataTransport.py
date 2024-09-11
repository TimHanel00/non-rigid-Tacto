import threading
from multiprocessing import Pipe
from time import sleep
import copy
class sofaObject:
    def __init__(self,name,position=None,orientation=None,forces=None,mesh=None):
        self.containsForces=True
        self.containsMesh=True
        if position is None:
            position = [0, 0, 0]
        if orientation is None:
            orientation = [0, 0, 0]
        if forces is None:
            forces=0
            self.containsForces=False
        if mesh is None:
            self.containsMesh=False
        self.name=name
        self.position=position
        self.orientation=orientation
        self.mesh=mesh
        self.normalForces=forces
    def updateMesh(self,mesh):
        self.mesh=mesh
class TransportData:
    def __init__(self):
        self.sofaOjectDict={}
    def addObject(self,objectD):
        if objectD.name in self.sofaOjectDict:
            if objectD.position is None and objectD.mesh is not None:
                self.sofaOjectDict[objectD.name].mesh=objectD.mesh
        self.sofaOjectDict[objectD.name]=objectD
    def get(self,name):
        print(self.sofaOjectDict.items())
        return self.sofaOjectDict[name]
    def tolist(self):
        return [v for k,v in self.sofaOjectDict.items()]  

    def __repr__(self):
        return f"TransportData(position={self.position}, orientation={self.orientation}, forces={self.normalForces})"

class DataReceiver(threading.Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.latest_data = TransportData()
        self.running = True

    def run(self):
        while self.running:
            if self.conn.poll(0.1):  # Poll for 0.1 second
                self.latest_data = self.conn.recv()
                #print(f"Received: {self.latest_data}")
    
    def get(self,name):
        return self.latest_data.get(name)
    def get(self):
        return self.latest_data
    def tolist(self):
        self.latest_data.tolist()
    def stop(self):
        self.running = False
        self.conn.close()

class Sender(threading.Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.curData = TransportData()
        self.running = True

    def update(self, name, pos, orientation, forces=None,mesh=None):
        self.curData.addObject(sofaObject(name=name,position=pos,orientation=orientation,forces=forces,mesh=mesh))
        #self.curData = TransportData(pos, orientation, forces,self.curData.tissuePos,self.curData.tissueOr,mesh)
    def copyLatest(self):
        return copy.deepcopy(self.curData)
    def run(self):
        while self.running:
            if self.curData:
                self.conn.send(self.copyLatest())
                #print(f"Sent: {self.curData}")
                  # Reset after sending
            sleep(0.01)  # Simulate some delay

    def stop(self):
        self.running = False
        self.conn.close()