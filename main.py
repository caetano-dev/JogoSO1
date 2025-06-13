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
    log("MAIN - ADQUIRINDO robots_mutex para contar robos vivos")
    with shared_state.robots_mutex:
        log("MAIN - robots_mutex ADQUIRIDO")
        alive_robots = []
        for robot_id in range(num_robots):
            robot_data = shared_state.get_robot_data(robot_id)
            if robot_data and robot_data['status'] == 1:
                alive_robots.append((robot_id, robot_data))
        
        alive_count = len(alive_robots)
        if alive_count == 1:
            winner_id = alive_robots[0][0]
        else:
            winner_id = -1
        log("MAIN - LIBERANDO robots_mutex")
    
    flags = shared_state.get_flags()
    if alive_count <= 1:
        game_over_status = 1
        if alive_count == 1:
            log(f"JOGO - Robo {winner_id} ganhou.")
        else:
            log(f"JOGO - Fim de jogo - empate")
    else:
        game_over_status = 0
    
    if flags.get('alive_count', -1) != alive_count:
        log(f"JOGO - Robos vivos: {alive_count}")
        
    flags.update({
        'alive_count': alive_count,
        'game_over': game_over_status,
        'winner': winner_id
    })
    shared_state.set_flags(flags)
    return alive_count

def main(stdscr):
    log("MAIN - Iniciando jogo de robos")
    curses.curs_set(0)
    stdscr.nodelay(True)

    shared_objects = create_shared_state()
    shared_state = SharedGameState(shared_objects)
    
    robot_processes = []
    log(f"MAIN - Criando {NUM_ROBOTS} processos de robos")
    for i in range(NUM_ROBOTS):
        is_player = (i == 0)
        robot = Robot(i, is_player, shared_objects)
        robot_processes.append(robot)
        robot.start()
        log(f"MAIN - Robo {i} {'(JOGADOR)' if is_player else '(IA)'} iniciado")
    
    player_robot = robot_processes[0]
    viewer = Viewer(shared_state)
    time.sleep(1)

    log("MAIN - Interface grafica iniciada - jogo em execucao")
    
    log("Jogo iniciado")

    while True:
        update_alive_count(shared_state, NUM_ROBOTS)
        viewer.display_grid(stdscr)
        
        flags = shared_state.get_flags()
        if flags['game_over']:
            game_status = viewer.format_game_status_message(flags)
            winner_msg = game_status

            if flags['winner'] == 0:
                winner_msg += " (voce ganhou!)"
                log("MAIN - voce ganhou!")
            else:
                log("MAIN - o adversario ganhou")

            stdscr.addstr(GRID_HEIGHT + 3, 0, winner_msg)
            stdscr.addstr(GRID_HEIGHT + 4, 0, "Pressione qualquer tecla para sair...")
            stdscr.refresh()
            stdscr.nodelay(False)
            stdscr.getch()
            break
        
        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            log("MAIN - Usuario pressionou 'q' - encerrando jogo")
            break
        
        if key == curses.KEY_UP:
            player_robot.set_direction(0, -1)
        elif key == curses.KEY_DOWN:
            player_robot.set_direction(0, 1)
        elif key == curses.KEY_LEFT:
            player_robot.set_direction(-1, 0)
        elif key == curses.KEY_RIGHT:
            player_robot.set_direction(1, 0)
            
        curses.napms(25)

    log("MAIN - Finalizando processos de robos")
    for robot in robot_processes:
        robot.running = False
    for robot in robot_processes:
        robot.join()
        if robot.is_alive():
            log(f"MAIN - Forçando termino do robo {robot.id}")
            robot.terminate()
    log("MAIN - Jogo finalizado")

if __name__ == "__main__":
    clearLog()
    multiprocessing.set_start_method('spawn', force=True)
    curses.wrapper(main)
