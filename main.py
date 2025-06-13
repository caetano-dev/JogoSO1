import multiprocessing
import curses
import time
import os
from config import *
from shared_memory import create_shared_state, SharedGameState
from robot import Robot
from viewer import Viewer
import datetime

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
        
def clearLog():
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "w") as f:
        f.write("")

def update_alive_count(shared_state, num_robots):
    with shared_state.robots_mutex:
        alive_count = 0
        for robot_id in range(num_robots):
            robot_data = shared_state.get_robot_data(robot_id)
            if robot_data and robot_data['status'] == 1:
                alive_count += 1
        
        flags = shared_state.get_flags()
        flags['alive_count'] = alive_count
        shared_state.set_flags(flags)
        return alive_count

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    shared_objects = create_shared_state()
    shared_state = SharedGameState(shared_objects)
    
    robot_processes = []
    for i in range(NUM_ROBOTS):
        is_player = (i == 0)
        robot = Robot(i, is_player, shared_objects)
        robot_processes.append(robot)
        robot.start()
        log(f"Robo numero {i} criado")
    
    player_robot = robot_processes[0]
    viewer = Viewer(shared_state)
    
    log("Jogo iniciado")
    
    running = True
    while running:
        update_alive_count(shared_state, NUM_ROBOTS)
        viewer.display_grid(stdscr)
        
        key = stdscr.getch()
        log(f"Tecla {key} pressionada.")
        
        if key == ord('q') or key == ord('Q'):
            running = False
            log("Jogo esta sendo encerrado, obrigado por jogar <3")
        
        if key == curses.KEY_UP:
            player_robot.set_direction(0, -1)
            log(f"Tecla {key} pressionada.")
            log("Robo do jogador se moveu para cima.")
        elif key == curses.KEY_DOWN:
            player_robot.set_direction(0, 1)
            log(f"Tecla {key} pressionada.")
            log("Robo do jogador se moveu para baixo.")
        elif key == curses.KEY_LEFT:
            player_robot.set_direction(-1, 0)
            log(f"Tecla {key} pressionada.")
            log("Robo do jogador se moveu para a esquerda.")
        elif key == curses.KEY_RIGHT:
            player_robot.set_direction(1, 0)
            log(f"Tecla {key} pressionada.")
            log("Robo do jogador se moveu para a direita.")
            
        curses.napms(50)

    for robot in robot_processes:
        robot.terminate()
        robot.join()

if __name__ == "__main__":
    clearLog()
    multiprocessing.set_start_method('spawn', force=True)
    curses.wrapper(main)