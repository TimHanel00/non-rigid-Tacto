import threading
from multiprocessing import Pipe
from time import sleep
class TransportData:
    def __init__(self, position=None, orientation=None, forces=None,tissuePos=None,tissueOr=None,mesh=None):
        if position is None:
            position = [0, 0, 0]
        if orientation is None:
            orientation = [0, 0, 0]
        if forces is None:
            forces = 0
        if tissuePos is None:
            tissuePos = [0, 0, 0]
        if tissueOr is None:
            tissueOr = [0, 0, 0]
        self.position = position
        self.orientation = orientation
        self.tissuePos=tissuePos
        self.tissueOr=tissueOr
        self.normalForces = forces
        self.mesh=mesh
        

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
    def get(self):
        return self.latest_data
    def stop(self):
        self.running = False
        self.conn.close()

class Sender(threading.Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.curData = TransportData()
        self.running = True

    def update(self, pos, orientation, forces=None,mesh=None):
        self.curData = TransportData(pos, orientation, forces,self.curData.tissuePos,self.curData.tissueOr,mesh)
    def updateTissue(self, tissuePos,tissueOr):
        self.curData = TransportData(self.curData.position, self.curData.orientation, self.curData.normalForces,tissuePos,tissueOr)
    def run(self):
        while self.running:
            if self.curData:
                self.conn.send(self.curData)
                #print(f"Sent: {self.curData}")
                  # Reset after sending
            sleep(0.01)  # Simulate some delay

    def stop(self):
        self.running = False
        self.conn.close()