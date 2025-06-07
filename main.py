import multiprocessing
import curses
import time
from shared_memory import create_shared_state, SharedGameState
from robot import Robot
from viewer import Viewer

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    shared_objects = create_shared_state()
    shared_state = SharedGameState(shared_objects)
    
    player_robot = Robot(0, shared_objects)
    player_robot.start()

    viewer = Viewer(shared_state)
    time.sleep(0.1)

    running = True
    while running:
        viewer.display_grid(stdscr)
        
        #'q' pra sair
        key = stdscr.getch()
        if key == ord('q'):
            running = False
        
        if key == curses.KEY_UP:
            player_robot.set_direction(0, -1)
        elif key == curses.KEY_DOWN:
            player_robot.set_direction(0, 1)
        elif key == curses.KEY_LEFT:
            player_robot.set_direction(-1, 0)
        elif key == curses.KEY_RIGHT:
            player_robot.set_direction(1, 0)
            
        curses.napms(50)

    player_robot.terminate()
    player_robot.join()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    curses.wrapper(main)