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
        
        self.direction_queue = multiprocessing.Queue()

    def initialize(self):
        x, y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        robot_data = {'id': self.id, 'x': x, 'y': y, 'status': 1}
        
        with self.shared_state.grid_mutex:
            self.shared_state.robots[self.id] = robot_data
            self.shared_state.set_grid_cell(x, y, PLAYER_SYMBOL)

    def set_direction(self, dx, dy):
        while not self.direction_queue.empty():
            self.direction_queue.get_nowait()
        self.direction_queue.put((dx, dy))

    def move(self, dx, dy):
        with self.shared_state.grid_mutex:
            robot_data = self.shared_state.robots[self.id]
            old_x, old_y = robot_data['x'], robot_data['y']
            new_x, new_y = old_x + dx, old_y + dy

            is_valid_move = (0 < new_x < GRID_WIDTH - 1 and
                             0 < new_y < GRID_HEIGHT - 1 and
                             self.shared_state.get_grid_cell(new_x, new_y) == EMPTY_SYMBOL)

            if is_valid_move:
                robot_data['x'] = new_x
                robot_data['y'] = new_y
                self.shared_state.robots[self.id] = robot_data
                
                self.shared_state.set_grid_cell(new_x, new_y, PLAYER_SYMBOL)
                self.shared_state.set_grid_cell(old_x, old_y, EMPTY_SYMBOL)

    def sense_act(self):
        while True:
            dx, dy = self.direction_queue.get_nowait()
            self.move(dx, dy)
            time.sleep(0.1)

    def run(self):
        self.shared_state = SharedGameState(self.shared_objects)
        self.initialize()
        self.sense_act()