import multiprocessing
import random
from config import *
import os

def log(msg):
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "a") as f:
        f.write(msg + "\n")


def create_shared_state():
    manager = multiprocessing.Manager()
    grid = manager.list([manager.list([EMPTY_SYMBOL] * GRID_WIDTH) for _ in range(GRID_HEIGHT)])
    robots = manager.list([manager.dict() for _ in range(NUM_ROBOTS)])
    batteries = manager.list([manager.dict() for _ in range(NUM_BATTERIES)])
    
    grid_mutex = manager.Lock()
    robots_mutex = manager.Lock()
    battery_mutexes = [manager.Lock() for _ in range(NUM_BATTERIES)]
    
    return {
        'grid': grid,
        'robots': robots,
        'batteries': batteries,
        'grid_mutex': grid_mutex,
        'robots_mutex': robots_mutex,
        'battery_mutexes': battery_mutexes
    }

class SharedGameState:
    def __init__(self, shared_objects):
        self.grid = shared_objects['grid']
        self.robots = shared_objects['robots']
        self.batteries = shared_objects['batteries']
        self.grid_mutex = shared_objects['grid_mutex']
        self.robots_mutex = shared_objects['robots_mutex']
        self.battery_mutexes = shared_objects['battery_mutexes']

    def get_grid_cell(self, x, y):
        if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
            return self.grid[y][x]
        return None

    def set_grid_cell(self, x, y, value):
        if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
            row = self.grid[y]
            row[x] = str(value)[0]
            self.grid[y] = row

    def get_battery_data(self, battery_id):
        if not (0 <= battery_id < NUM_BATTERIES):
            return None
        return dict(self.batteries[battery_id])

    def set_battery_data(self, battery_id, battery_data):
        if not (0 <= battery_id < NUM_BATTERIES):
            return
        self.batteries[battery_id].update(battery_data)