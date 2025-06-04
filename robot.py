import multiprocessing
import time
from config import *
from shared_memory import SharedGameState

class Robot(multiprocessing.Process):
    def __init__(self, robot_id, shared_objects):
        super().__init__()
        self.id = robot_id
        self.shared_objects = shared_objects
        self.shared_state = None

    def initialize(self):
        x, y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        robot_data = {
            'id': self.id,
            'x': x,
            'y': y,
            'status': 1
        }
        
        with self.shared_state.grid_mutex:
            self.shared_state.robots[self.id] = robot_data
            self.shared_state.set_grid_cell(x, y, PLAYER_SYMBOL)

    def run(self):
        self.shared_state = SharedGameState(self.shared_objects)
        self.initialize()
        
        while True:
            time.sleep(1)