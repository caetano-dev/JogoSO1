import multiprocessing
import time
import random
from config import *
from shared_memory import SharedGameState
import os

def log(msg):
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "a") as f:
        f.write(msg + "\n")


class Robot(multiprocessing.Process):
    def __init__(self, robot_id, is_player, shared_objects):
        super().__init__()
        self.id = robot_id
        self.is_player = is_player
        self.shared_objects = shared_objects
        self.shared_state = None
        
        self.F = random.randint(9, 10)
        self.E = random.randint(95, 100)
        self.V = random.randint(4, 5)
        
        self.direction_queue = multiprocessing.Queue() if is_player else None

    def get_robot_symbol(self):
        return PLAYER_SYMBOL if self.is_player else str(self.id)

    def place_batteries(self):
        for battery_idx in range(NUM_BATTERIES):
            for _ in range(100):
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                
                with self.shared_state.grid_mutex:
                    if self.shared_state.get_grid_cell(x, y) == EMPTY_SYMBOL:
                        with self.shared_state.battery_mutexes[battery_idx]:
                            battery_data = {
                                'x': x, 
                                'y': y, 
                                'collected': 0, 
                                'owner': -1
                            }
                            self.shared_state.set_battery_data(battery_idx, battery_data)
                        
                        self.shared_state.set_grid_cell(x, y, BATTERY_SYMBOL)
                        break

    def initialize_arena_if_needed(self):
        with self.shared_state.init_mutex:
            flags = self.shared_state.get_flags()
            if flags['init_done']: 
                return
            self.place_batteries()
            self.initialize_robots_shared_data()
            flags['init_done'] = 1
            flags['alive_count'] = NUM_ROBOTS
            self.shared_state.set_flags(flags)

    def initialize_robots_shared_data(self):
        for robot_idx in range(NUM_ROBOTS):
            for _ in range(100):
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                
                if not (0 < x < GRID_WIDTH - 1 and 0 < y < GRID_HEIGHT - 1):
                    continue
                    
                with self.shared_state.grid_mutex:
                    if self.shared_state.get_grid_cell(x, y) == EMPTY_SYMBOL:
                        with self.shared_state.robots_mutex:
                            self.shared_state.set_robot_data(robot_idx, {
                                'id': robot_idx, 
                                'x': x, 
                                'y': y,
                                'F': self.F if robot_idx == self.id else random.randint(6, 10),
                                'E': self.E if robot_idx == self.id else random.randint(80, 100),
                                'V': self.V if robot_idx == self.id else random.randint(3, 5),
                                'status': 1
                            })
                        self.shared_state.set_grid_cell(x, y, PLAYER_SYMBOL if robot_idx == 0 else str(robot_idx))
                        break

    def set_direction(self, dx, dy):
        if self.is_player and self.direction_queue:
            while not self.direction_queue.empty():
                self.direction_queue.get_nowait()
            self.direction_queue.put((dx, dy))

    def move(self, dx, dy):
        with self.shared_state.robots_mutex, self.shared_state.grid_mutex:
            robot_data = self.shared_state.get_robot_data(self.id)
            old_x, old_y = robot_data['x'], robot_data['y']
            new_x, new_y = old_x + dx, old_y + dy

            is_valid_move = (0 < new_x < GRID_WIDTH - 1 and
                             0 < new_y < GRID_HEIGHT - 1 and
                             self.shared_state.get_grid_cell(new_x, new_y) == EMPTY_SYMBOL)

            if is_valid_move:
                robot_data['x'] = new_x
                robot_data['y'] = new_y
                robot_data['E'] = max(0, robot_data['E'] - 1)
                
                if robot_data['E'] <= 0:
                    robot_data['status'] = 0
                
                self.shared_state.set_robot_data(self.id, robot_data)
                
                if robot_data['status'] == 0:
                    self.shared_state.set_grid_cell(old_x, old_y, EMPTY_SYMBOL)
                    self.shared_state.set_grid_cell(new_x, new_y, EMPTY_SYMBOL)
                else:
                    self.shared_state.set_grid_cell(new_x, new_y, self.get_robot_symbol())
                    self.shared_state.set_grid_cell(old_x, old_y, EMPTY_SYMBOL)

    def sense_act(self):
        while True:
            with self.shared_state.robots_mutex:
                robot_data = self.shared_state.get_robot_data(self.id)
                if robot_data['status'] == 0:
                    break
            
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
        time.sleep(0.01 * self.id)
        self.initialize_arena_if_needed()
        
        while not self.shared_state.get_flags()['init_done']:
            time.sleep(0.1)
        
        self.sense_act()