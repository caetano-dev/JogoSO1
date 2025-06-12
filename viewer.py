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
    
    def is_robot_on_battery(self, x, y):
        for battery_id in range(NUM_BATTERIES):
            battery_data = self.shared_state.get_battery_data(battery_id)
            if battery_data:
                bx, by = battery_data['x'], battery_data['y']
                if x == bx and y == by:
                    return True
        return False
    
    def format_game_status_message(self, flags):
        if flags['game_over']:
            if flags['winner'] >= 0:
                return f"Fim - Vencedor: Robô {flags['winner']}"
            else:
                return "Fim - Empate"
        return ""

    def display_grid(self, stdscr):
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # mostra mapa
        for y in range(min(GRID_HEIGHT, max_y - 5)):
            row = ""
            for x in range(min(GRID_WIDTH, max_x - 1)):
                row += self.shared_state.get_grid_cell(x, y)
            stdscr.addstr(y, 0, row)
        
        # mostra status dos robos
        if GRID_HEIGHT + 1 < max_y:
            with self.shared_state.robots_mutex:
                # mostra jogador principal
                robot_data = self.shared_state.get_robot_data(0)
                if robot_data and GRID_HEIGHT + 1 < max_y:
                    status = "alive" if robot_data['status'] == 1 else "dead"
                    charge_indicator = " ⚡" if self.is_robot_on_battery(robot_data['x'], robot_data['y']) else ""
                    info = f"Jogador (P): Energia={robot_data['E']}, Força={robot_data['F']}, Velocidade={robot_data['V']}, Status={status}{charge_indicator}"
                    stdscr.addstr(GRID_HEIGHT + 1, 0, info[:max_x-1])
                
                # mostra outros robos
                other_robots = [f" Robô {i}: E={data['E']}, F={data['F']}, V={data['V']}{' ⚡' if self.is_robot_on_battery(data['x'], data['y']) else ''}"
                              for i in range(1, NUM_ROBOTS) 
                              if (data := self.shared_state.get_robot_data(i)) and data['status'] == 1]
                if other_robots and GRID_HEIGHT + 2 < max_y:
                    stdscr.addstr(GRID_HEIGHT + 2, 0, " | ".join(other_robots)[:max_x-1])
        
        # mostra status do jogo
        if GRID_HEIGHT + 3 < max_y:
            flags = self.shared_state.get_flags()
            status_info = f"Robôs vivos: {flags['alive_count']}"
            game_status = self.format_game_status_message(flags)
            if game_status:
                status_info += f" | {game_status}"
            stdscr.addstr(GRID_HEIGHT + 3, 0, status_info[:max_x-1])
        
        if GRID_HEIGHT + 4 < max_y:
            controls = "Use setas para mover o jogador (P). Q para sair."
            stdscr.addstr(GRID_HEIGHT + 4, 0, controls[:max_x-1])
        
        stdscr.refresh()

    def handle_quit_input(self, stdscr):
        key = stdscr.getch()
        return key == ord('q')
    
    def run(self, stdscr):
        stdscr.nodelay(True)
        
        while self.running:
            try:
                flags = self.shared_state.get_flags()
                if flags['game_over']:
                    self.display_grid(stdscr)
                    time.sleep(2)
                    break
                
                self.display_grid(stdscr)
                
                key = stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    break
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break