import threading
from multiprocessing import Pipe
from time import sleep
class TransportData:
    def __init__(self, position=None, orientation=None, forces=None):
        
        self.position = position
        self.orientation = orientation
        self.normalForces = forces
        if position is None:
            position = [0, 0, 0]
        if orientation is None:
            orientation = [0, 0, 0]
        if forces is None:
            forces = [0, 0, 0]

    def __repr__(self):
        return f"TransportData(position={self.position}, orientation={self.orientation}, forces={self.normalForces})"

class DataReceiver(threading.Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.latest_data = None
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

    def update(self, pos, orientation, forces=None):
        self.curData = TransportData(pos, orientation, forces)

    def run(self):
        while self.running:
            if self.curData:
                self.conn.send(self.curData)
                #print(f"Sent: {self.curData}")
                self.curData = None  # Reset after sending
            sleep(0.01)  # Simulate some delay

    def stop(self):
        self.running = False
        self.conn.close()