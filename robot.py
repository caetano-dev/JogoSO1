import multiprocessing
import time
import random
from config import *
from shared_memory import SharedGameState

class Robot(multiprocessing.Process):
    def __init__(self, robot_id, is_player, shared_objects):
        super().__init__()
        self.id = robot_id
        self.is_player = is_player
        self.shared_objects = shared_objects
        self.shared_state = None
        
        self.direction_queue = multiprocessing.Queue() if is_player else None

    def get_robot_symbol(self):
        return PLAYER_SYMBOL if self.is_player else str(self.id)

    def initialize(self):
        while True:
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            
            with self.shared_state.grid_mutex:
                if self.shared_state.get_grid_cell(x, y) == EMPTY_SYMBOL:
                    robot_data = {'id': self.id, 'x': x, 'y': y, 'status': 1}
                    
                    with self.shared_state.robots_mutex:
                         self.shared_state.robots[self.id] = robot_data
                    
                    self.shared_state.set_grid_cell(x, y, self.get_robot_symbol())
                    break 

    def set_direction(self, dx, dy):
        if self.is_player and self.direction_queue:
            while not self.direction_queue.empty():
                self.direction_queue.get_nowait()
            self.direction_queue.put((dx, dy))

    def move(self, dx, dy):
        with self.shared_state.robots_mutex, self.shared_state.grid_mutex:
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
                
                self.shared_state.set_grid_cell(new_x, new_y, self.get_robot_symbol())
                self.shared_state.set_grid_cell(old_x, old_y, EMPTY_SYMBOL)

    def sense_act(self):
        while True:
            dx, dy = 0, 0
            if self.is_player:
                try:
                    dx, dy = self.direction_queue.get_nowait()
                except:
                    pass 
            else:
                if random.random() < 0.2: 
                    dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

            if dx != 0 or dy != 0:
                self.move(dx, dy)
            
            time.sleep(0.2) 

    def run(self):
        self.shared_state = SharedGameState(self.shared_objects)
        time.sleep(0.01 * self.id) #atrasa um pouco pra nao dar race condition
        self.initialize()
        self.sense_act()