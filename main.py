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
    
    robot_process = Robot(0, shared_objects)
    robot_process.start()

    viewer = Viewer(shared_state)
    
    time.sleep(0.1)

    while True:
        viewer.display_grid(stdscr)
        
        #'q' pra sair
        key = stdscr.getch()
        if key == ord('q'):
            break
        
        #pausa 100ms entre frames
        curses.napms(100)

    robot_process.terminate()
    robot_process.join()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    curses.wrapper(main)