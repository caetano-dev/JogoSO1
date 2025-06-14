import multiprocessing
import random
from config import *
import os
import datetime

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")


def create_shared_state():
    manager = multiprocessing.Manager()
    
    grid = manager.list()
    robots = manager.list()
    batteries = manager.list()
    flags = manager.dict()
    
    init_mutex = manager.Lock()
    grid_mutex = manager.Lock()
    robots_mutex = manager.Lock()
    battery_mutexes = [manager.Lock() for _ in range(NUM_BATTERIES)]
    
    for y in range(GRID_HEIGHT):
        row = []
        for x in range(GRID_WIDTH):
            if x == 0 or x == GRID_WIDTH-1 or y == 0 or y == GRID_HEIGHT-1:
                row.append(BORDER_SYMBOL)
            else:
                grid_aleatoria = random.randint(3,3)#0,3
                match(grid_aleatoria):
                    case 0:
                        row.append(EMPTY_SYMBOL)
                    case 1:
                        if ((10 <= x < 15 or 25 < x <= 30) and (y == 5 or y == 15)) or((x==10 or x==30) and (5<y<9 or 12<y<15)):
                            row.append(BORDER_SYMBOL)
                        else:
                            row.append(EMPTY_SYMBOL)
                    case 2:
                        if ((15 <= x <= 25) and (y == 3 or y == 17)) or((x==5 or x==35) and (3<=y<9 or 11<y<=17)):
                            row.append(BORDER_SYMBOL)
                        else:
                            row.append(EMPTY_SYMBOL)
                    case 3:
                        if ((x==10 or x==30) and (4<=y<8 or 12<y<=16)) or (x==20 and (5<y<10 or 10<y<15)):
                            row.append(BORDER_SYMBOL)
                        else:
                            row.append(EMPTY_SYMBOL)
        grid.append(row)
    
    for robot_id in range(NUM_ROBOTS):
        robots.append(manager.dict({
            'id': robot_id,
            'x': 0,
            'y': 0,
            'F': 0,
            'E': 0,
            'V': 0,
            'status': 0  # 0: morto, 1: vivo TODO: poderia ser um enum
        }))
    
    for battery_id in range(NUM_BATTERIES):
        batteries.append(manager.dict({
            'x': 0,
            'y': 0,
            'collected': 0,
            'owner': -1
        }))
    
    flags.update({
        'init_done': 0,
        'game_over': 0,
        'winner': -1,
        'alive_count': 0
    })
    
    return {
        'grid': grid,
        'robots': robots,
        'batteries': batteries,
        'flags': flags,
        'init_mutex': init_mutex,
        'grid_mutex': grid_mutex,
        'robots_mutex': robots_mutex,
        'battery_mutexes': battery_mutexes
    }

class SharedGameState:
    def __init__(self, shared_objects):
        self.grid = shared_objects['grid']
        self.robots = shared_objects['robots']
        self.batteries = shared_objects['batteries']
        self.flags = shared_objects['flags']
        self.init_mutex = shared_objects['init_mutex']
        self.grid_mutex = shared_objects['grid_mutex']
        self.robots_mutex = shared_objects['robots_mutex']
        self.battery_mutexes = shared_objects['battery_mutexes']

    def get_grid_cell(self, x, y):
        if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
            return self.grid[y][x]
        return BORDER_SYMBOL

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

    def get_robot_data(self, robot_id):
        if not (0 <= robot_id < NUM_ROBOTS):
            return None
        return dict(self.robots[robot_id])

    def set_robot_data(self, robot_id, robot_data):
        if not (0 <= robot_id < NUM_ROBOTS):
            return
        self.robots[robot_id].update(robot_data)

    def get_flags(self):
        return dict(self.flags)

    def set_flags(self, flags_dict):
        self.flags.update(flags_dict)

    def take_grid_snapshot(self):
        snapshot = []
        for y in range(GRID_HEIGHT):
            row = []
            for x in range(GRID_WIDTH):
                cell_value = self.get_grid_cell(x, y)
                row.append(cell_value)
            snapshot.append(row)
        return snapshot