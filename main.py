import multiprocessing
import curses
import time
import os
from config import *
from shared_memory import create_shared_state, SharedGameState
from robot import Robot
from viewer import Viewer

def log(msg):
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "a") as f:
        f.write(msg + "\n")


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    shared_objects = create_shared_state()
    
    robot_processes = []
    for i in range(NUM_ROBOTS):
        is_player = (i == 0)
        robot = Robot(i, is_player, shared_objects)
        robot_processes.append(robot)
        robot.start()
        log(f"Robo numero {i} criado")
    
    player_robot = robot_processes[0]
    viewer = Viewer(SharedGameState(shared_objects))
    
    log("Jogo iniciado")
    
    running = True
    while running:
        viewer.display_grid(stdscr)
        
        key = stdscr.getch()
        log(f"Tecla {key} pressionada.")
        if key == ord('q'):
            running = False
            log("Jogo está sendo encerrado, obrigado por jogar <3")
        
        if key == curses.KEY_UP:
            player_robot.set_direction(0, -1)
            log("Robo do jogador se moveu para cima.")
        elif key == curses.KEY_DOWN:
            player_robot.set_direction(0, 1)
            log("Robo do jogador se moveu para baixo.")
        elif key == curses.KEY_LEFT:
            player_robot.set_direction(-1, 0)
            log("Robo do jogador se moveu para a esquerda.")
        elif key == curses.KEY_RIGHT:
            player_robot.set_direction(1, 0)
            log("Robo do jogador se moveu para a direita.")
            
        curses.napms(50)

    for robot in robot_processes:
        robot.terminate()
        robot.join()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    curses.wrapper(main)