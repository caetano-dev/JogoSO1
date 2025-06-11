import time
import curses
import os
from config import *
import datetime

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")


class Viewer:
    def __init__(self, shared_state):
        self.shared_state = shared_state

    def display_grid(self, stdscr):
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        for y in range(min(GRID_HEIGHT, max_y - 1)):
            for x in range(min(GRID_WIDTH, max_x - 1)):
                symbol = self.shared_state.get_grid_cell(x, y)
                if symbol:
                    stdscr.addch(y, x, symbol)
        
        stdscr.refresh()