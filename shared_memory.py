import multiprocessing
from config import *

def create_shared_state():
    manager = multiprocessing.Manager()
    grid = manager.list([manager.list([EMPTY_SYMBOL] * GRID_WIDTH) for _ in range(GRID_HEIGHT)])
    robots = manager.Lock()
    grid_mutex = manager.Lock()
    
    return {
        'grid': grid,
        'robots': robots,
        'grid_mutex': grid_mutex
    }

class SharedGameState:
    def __init__(self, shared_objects):
        self.grid = shared_objects['grid']
        self.robots = shared_objects['robots']
        self.grid_mutex = shared_objects['grid_mutex']

    def get_grid_cell(self, x, y):
        if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
            return self.grid[y][x]
        return None

    def set_grid_cell(self, x, y, value):
        if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
            row = self.grid[y]
            row[x] = value
            self.grid[y] = row