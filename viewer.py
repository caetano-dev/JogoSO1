import time
import curses
from config import *

class Viewer:
    def __init__(self, shared_state):
        self.shared_state = shared_state

    def draw_borders(self, stdscr):
        max_y, max_x = stdscr.getmaxyx() #pega o tamanho máximo da janela
        
        for x in range(min(GRID_WIDTH, max_x)): #desenha as bordas
            stdscr.addch(0, x, BORDER_SYMBOL)
            if GRID_HEIGHT < max_y:
                stdscr.addch(GRID_HEIGHT - 1, x, BORDER_SYMBOL)
        for y in range(min(GRID_HEIGHT, max_y)):
            stdscr.addch(y, 0, BORDER_SYMBOL)
            if GRID_WIDTH < max_x:
                stdscr.addch(y, GRID_WIDTH - 1, BORDER_SYMBOL)

    def display_grid(self, stdscr):
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        self.draw_borders(stdscr)

        for y in range(1, min(GRID_HEIGHT - 1, max_y - 1)):
            for x in range(1, min(GRID_WIDTH - 1, max_x - 1)):
                symbol = self.shared_state.get_grid_cell(x, y)
                if symbol:
                    stdscr.addch(y, x, symbol)
        
        stdscr.refresh()