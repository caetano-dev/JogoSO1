import multiprocessing
import threading
import time
import random
from config import *
from shared_memory import SharedGameState
import os
import datetime

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    path = os.path.join(os.path.dirname(__file__), "log.txt")
    with open(path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")


class Robot(multiprocessing.Process):
    def __init__(self, robot_id, is_player, shared_objects):
        super().__init__()
        self.id = robot_id
        self.is_player = is_player
        self.shared_objects = shared_objects
        self.shared_state = None
        self.running = True
        
        self.F = random.randint(9, 10)
        self.E = random.randint(95, 100)
        self.V = random.randint(4, 5)
        
        self.current_battery_id = None
        self.current_battery_mutex = None
        
        self.direction_queue = multiprocessing.Queue() if is_player else None
        
        robot_type = "JOGADOR" if is_player else "IA"
        log(f"Robo {robot_id} ({robot_type}) criado - F:{self.F}, E:{self.E}, V:{self.V}")

    def get_robot_symbol(self):
        return PLAYER_SYMBOL if self.is_player else str(self.id)

    def attach_shared_memory(self):
        self.shared_state = SharedGameState(self.shared_objects)
        log(f"Robo {self.id} - Memória compartilhada anexada")

    def validate_robot_data(self, robot_data):
        return robot_data and robot_data['status'] == 1

    def place_batteries(self):
        for battery_idx in range(NUM_BATTERIES):
            for _ in range(100):
#                x = random.randint(1, GRID_WIDTH - 2)
                x = random.randint(1, GRID_WIDTH - 3) #2 celulas por bateria
                y = random.randint(1, GRID_HEIGHT - 2)
                
                with self.shared_state.grid_mutex:
#                    if self.shared_state.get_grid_cell(x, y) == EMPTY_SYMBOL:
                    if (self.shared_state.get_grid_cell(x, y) == EMPTY_SYMBOL and # 2 celulas por bateria
                        self.shared_state.get_grid_cell(x + 1, y) == EMPTY_SYMBOL): # 2 celular por bateria
                        with self.shared_state.battery_mutexes[battery_idx]:
                            battery_data = {
                                'x': x, 
                                'y': y, 
                                'collected': 0, 
                                'owner': -1
                            }
                            self.shared_state.set_battery_data(battery_idx, battery_data)
                        self.shared_state.set_grid_cell(x, y, BATTERY_SYMBOL) # mander
                        self.shared_state.set_grid_cell(x + 1, y, BATTERY_SYMBOL) # 2 celulas por bateria
                        break

    def initialize_arena_if_needed(self):
        with self.shared_state.init_mutex:
            flags = self.shared_state.get_flags()
            if flags['init_done']: 
                return
            self.place_batteries()
            self.initialize_robots_shared_data()
            flags['init_done'] = 1
            flags['alive_count'] = NUM_ROBOTS
            self.shared_state.set_flags(flags)

    def initialize_robots_shared_data(self):
        for robot_idx in range(NUM_ROBOTS):
            for _ in range(100):
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                
                if not (0 < x < GRID_WIDTH - 1 and 0 < y < GRID_HEIGHT - 1):
                    continue
                    
                with self.shared_state.grid_mutex:
                    if self.shared_state.get_grid_cell(x, y) == EMPTY_SYMBOL:
                        with self.shared_state.robots_mutex:
                            self.shared_state.set_robot_data(robot_idx, {
                                'id': robot_idx, 
                                'x': x, 
                                'y': y,
                                'F': self.F if robot_idx == self.id else random.randint(6, 10),
                                'E': self.E if robot_idx == self.id else random.randint(80, 100),
                                'V': self.V if robot_idx == self.id else random.randint(3, 5),
                                'status': 1
                            })
                        self.shared_state.set_grid_cell(x, y, PLAYER_SYMBOL if robot_idx == 0 else str(robot_idx))
                        break

    def set_direction(self, dx, dy):
        if self.is_player and self.direction_queue:
            while not self.direction_queue.empty():
                self.direction_queue.get_nowait()
            self.direction_queue.put((dx, dy))

    def try_move(self, dx, dy, robot_data_snapshot):
        old_x, old_y = robot_data_snapshot['x'], robot_data_snapshot['y']
        new_x, new_y = old_x + dx, old_y + dy

        if not (0 < new_x < GRID_WIDTH - 1 and 0 < new_y < GRID_HEIGHT - 1):
            return

        log(f"Robo {self.id} - ADQUIRINDO grid_mutex para mover de ({old_x},{old_y}) para ({new_x},{new_y})")
        with self.shared_state.grid_mutex:
            log(f"Robo {self.id} - grid_mutex ADQUIRIDO")
            target_cell = self.shared_state.get_grid_cell(new_x, new_y)

            if target_cell == EMPTY_SYMBOL:
                self.perform_move(old_x, old_y, new_x, new_y)

            elif target_cell == BATTERY_SYMBOL:
                battery_id = self.find_battery_at_position(new_x, new_y)
                if battery_id is not None:
                    log(f"Robo {self.id} - Encontrou bateria {battery_id}, adquirindo mutex")
                    time.sleep(0.02)
                    self.acquire_battery_mutex(battery_id)
                    self.perform_move(old_x, old_y, new_x, new_y)

            elif target_cell.isdigit() or target_cell == PLAYER_SYMBOL:
                if self.find_battery_at_position(new_x, new_y) is not None: 
                    return 
                other_robot_id = self.find_robot_at_position(new_x, new_y)
                if other_robot_id is not None and other_robot_id != self.id:
                    log(f"Robo {self.id} - DUELO iniciado com robo {other_robot_id}")
                    self.initiate_duel(other_robot_id, old_x, old_y, new_x, new_y)
            
            log(f"Robo {self.id} - LIBERANDO grid_mutex")

    def try_move_to_battery(self, old_x, old_y, new_x, new_y):
        battery_id = self.find_battery_at_position(new_x, new_y)
        if battery_id is None: #n achou bateria
            return
        
        log(f"Robo {self.id} - Tentando mover para bateria {battery_id} em ({new_x},{new_y})")
        time.sleep(0.01 + random.uniform(0, 0.02))
        self.acquire_battery_mutex(battery_id)
        time.sleep(0.02 + random.uniform(0, 0.03))

        try:
            log(f"Robo {self.id} - ADQUIRINDO grid_mutex para mover para bateria {battery_id}")
            with self.shared_state.grid_mutex:
                log(f"Robo {self.id} - grid_mutex ADQUIRIDO")
                self.execute_move_onto_battery_core(old_x, old_y, new_x, new_y, battery_id)
                log(f"Robo {self.id} - LIBERANDO grid_mutex")
        except Exception as e:
            log(f"Robo {self.id} - Erro ao mover para bateria {battery_id}: {e}")
            if self.current_battery_id == battery_id:
                self.release_battery_mutex()

    def execute_move_onto_battery_core(self, old_x, old_y, new_x, new_y, battery_id):
        log(f"Robo {self.id} - Movimento para bateria {battery_id} de ({old_x},{old_y}) para ({new_x},{new_y})")
        try:
            robot_data = self.update_robot_state(self.id, new_x, new_y, -1)
            if not robot_data:
                if self.current_battery_id == battery_id: 
                    self.release_battery_mutex()
                return

            if robot_data['status'] == 0:
                self.handle_robot_death(old_x, was_on_battery=self.is_on_battery(old_x, old_y))
                self.update_grid_cell(new_x, new_y, True)
                return

            self.update_grid_cell(old_x, old_y, self.is_on_battery(old_x, old_y))
            self.shared_state.set_grid_cell(new_x, new_y, self.get_robot_symbol())
            log(f"Robo {self.id} - Movimento para bateria {battery_id} realizado com sucesso")

        except Exception as e:
            log(f"Robo {self.id} - ERRO durante movimento para bateria {battery_id}: {e}")
            if self.current_battery_id == battery_id:
                self.release_battery_mutex()
            raise

    def perform_move(self, old_x, old_y, new_x, new_y):
        was_on_battery = self.is_on_battery(old_x, old_y)
        log(f"Robo {self.id} - Movimento normal de ({old_x},{old_y}) para ({new_x},{new_y}), estava em bateria: {was_on_battery}")
        
        robot_data = self.update_robot_state(self.id, new_x, new_y, -0.5)
        if not robot_data:
            return

        if robot_data['status'] == 0:
            self.handle_robot_death(old_x, old_y, was_on_battery)
            return

        self.update_grid_cell(old_x, old_y, was_on_battery)
        self.shared_state.set_grid_cell(new_x, new_y, self.get_robot_symbol())

        if was_on_battery:
            log(f"Robo {self.id} - Saiu da bateria, liberando mutex")
            self.release_battery_mutex()

    def update_robot_state(self, robot_id, new_x=None, new_y=None, energy_difference=0, new_status=None):
        with self.shared_state.robots_mutex:
            log(f"Robo {self.id} - robots_mutex ADQUIRIDO")
            robot_data = self.shared_state.get_robot_data(robot_id)
            if not self.validate_robot_data(robot_data):
                log(f"Robo {self.id} - LIBERANDO robots_mutex (dados invalidos)")
                return None
            
            if new_x is not None: robot_data['x'] = new_x
            if new_y is not None: robot_data['y'] = new_y
            if energy_difference != 0: 
                robot_data['E'] = max(0, robot_data['E'] + energy_difference)
            if new_status is not None: robot_data['status'] = new_status
            if robot_data['E'] <= 0: 
                robot_data['status'] = 0
                log(f"Robo {robot_id} - MORREU por falta de energia")
            
            self.shared_state.set_robot_data(robot_id, robot_data)
            log(f"Robo {self.id} - LIBERANDO robots_mutex")
            return robot_data

    def sense_act(self):
        log(f"Robo {self.id} - Iniciando ciclo sense_act")
        while self.running:
            grid_snapshot = self.take_grid_snapshot()
            with self.shared_state.robots_mutex:
                log(f"Robo {self.id} - robots_mutex ADQUIRIDO")
                robot_data = self.shared_state.get_robot_data(self.id)
                log(f"Robo {self.id} - LIBERANDO robots_mutex")
            if not self.validate_robot_data(robot_data):
                break
            
            actions = self.decide_actions(grid_snapshot, robot_data)
            for action in actions:
                self.execute_action(action, robot_data)
                with self.shared_state.robots_mutex:
                    log(f"Robo {self.id} - robots_mutex ADQUIRIDO")
                    robot_data = self.shared_state.get_robot_data(self.id)
                    log(f"Robo {self.id} - LIBERANDO robots_mutex")
                    if not self.validate_robot_data(robot_data):
                        log(f"Robo {self.id} - Morreu durante execução de ação, finalizando")
                        return
            
            time.sleep(0.2)

    def decide_actions(self, grid_snapshot, robot_data):
        actions = []
        if self.is_player:
            try:
                dx, dy = self.direction_queue.get_nowait()
                actions.append(('move', dx, dy))
            except:
                pass 
        else:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (0, 0)]
            if random.random() < 0.8:  #80% de chance de ir pra bateria
                direction = self.find_nearest_battery_direction(grid_snapshot, robot_data)
                if direction:
                    dx, dy = direction
                    if random.random() < 0.5:
                        log(f"Robo {self.id} - Robo decidiu ir para bateria: {direction}")
                        actions.append(('move_to_battery', dx, dy))
                    else:
                        log(f"Robo {self.id} - Robo movendo para: {direction}")
                        actions.append(('move', dx, dy))
                else:
                    dx, dy = random.choice(directions)
                    log(f"Robo {self.id} - Robo movendo para: {(dx, dy)}")
                    actions.append(('move', dx, dy))
            else:
                dx, dy = random.choice(directions)
                if random.random() < 0.4:
                    log(f"Robo {self.id} - Robo movendo para bateria: {(dx, dy)}")
                    actions.append(('move_to_battery', dx, dy))
                else:
                    log(f"Robo {self.id} - Robo movimento aleatório: {(dx, dy)}")
                    actions.append(('move', dx, dy))
        return actions

    def execute_action(self, action, robot_data):
        action_type = action[0]
        if action_type == 'move':
            dx, dy = action[1], action[2]
            movement_delay = (robot_data['V'] * 0.200)
            log(f"Robo {self.id} - Executando movimento ({dx},{dy}) com delay {movement_delay:.3f}s")
            time.sleep(movement_delay)
            if dx != 0 or dy != 0:
                self.try_move(dx, dy, robot_data)
        elif action_type == 'move_to_battery':
            dx, dy = action[1], action[2]
            movement_delay = (robot_data['V'] * 0.200)
            log(f"Robo {self.id} - Executando movimento para bateria ({dx},{dy}) com delay {movement_delay:.3f}s")
            time.sleep(movement_delay)
            old_x, old_y = robot_data['x'], robot_data['y']
            new_x, new_y = old_x + dx, old_y + dy
            
            if 0 < new_x < GRID_WIDTH-1 and 0 < new_y < GRID_HEIGHT-1:
                self.try_move_to_battery(old_x, old_y, new_x, new_y)

    def take_grid_snapshot(self):
        return self.shared_state.take_grid_snapshot()

    def find_nearest_battery_direction(self, grid_snapshot, robot_data):
        robot_x, robot_y = robot_data['x'], robot_data['y']
        min_distance = float('inf')
        best_direction = None
        battery_count = 0
        
        for y_coord in range(len(grid_snapshot)):
            for x_coord in range(len(grid_snapshot[0])):
                if grid_snapshot[y_coord][x_coord] == BATTERY_SYMBOL:
                    battery_count += 1
                    distance = abs(x_coord - robot_x) + abs(y_coord - robot_y)
                    if distance < min_distance:
                        min_distance = distance
                        dx = 0 if x_coord == robot_x else (1 if x_coord > robot_x else -1)
                        dy = 0 if y_coord == robot_y else (1 if y_coord > robot_y else -1)
                        best_direction = (dx, 0) if abs(x_coord - robot_x) >= abs(y_coord - robot_y) else (0, dy)
        
        if best_direction and battery_count > 0:
            log(f"Robo {self.id} - Encontrou {battery_count} baterias, indo para mais próxima (distância {min_distance})")
        return best_direction

    def find_battery_at_position(self, x, y):
        for battery_idx in range(NUM_BATTERIES):
            battery_data = self.shared_state.get_battery_data(battery_idx)
            if battery_data and battery_data['x'] > 0:
                bx, by = battery_data['x'], battery_data['y']
#                if x == bx and y == by:
                if (x == bx and y == by) or (x == bx+1 and y == by): #2 celulas pra bateria
                    return battery_idx
        return None

    def is_on_battery(self, x, y):
        return self.find_battery_at_position(x, y) is not None

    def find_robot_at_position(self, x, y):
        for robot_idx in range(NUM_ROBOTS):
            robot_data = self.shared_state.get_robot_data(robot_idx)
            if self.validate_robot_data(robot_data) and robot_data['x'] == x and robot_data['y'] == y:
                return robot_idx
        return None

    def update_grid_cell(self, x, y, was_on_battery):
        if was_on_battery:
            battery_id = self.find_battery_at_position(x, y)
            if battery_id is not None:
                self.shared_state.set_grid_cell(x, y, BATTERY_SYMBOL)
            else:
                self.shared_state.set_grid_cell(x, y, EMPTY_SYMBOL)
        else:
            self.shared_state.set_grid_cell(x, y, EMPTY_SYMBOL)

    def handle_robot_death(self, x, y, was_on_battery):
        log(f"Robo {self.id} - Processando morte na posição ({x},{y})")
        self.update_grid_cell(x, y, was_on_battery)
        if self.current_battery_id is not None:
            self.release_battery_mutex()

    def acquire_battery_mutex(self, battery_id):
        if battery_id is not None and self.current_battery_id != battery_id:
            if self.current_battery_id is not None:
                log(f"Robo {self.id} - Liberando mutex da bateria {self.current_battery_id} antes de adquirir bateria {battery_id}")
                self.release_battery_mutex()
            time.sleep(0.01 + random.uniform(0, 0.02))
            log(f"Robo {self.id} - TENTANDO ADQUIRIR battery_mutex da bateria {battery_id}")
            self.shared_state.battery_mutexes[battery_id].acquire()
            self.current_battery_id = battery_id
            self.current_battery_mutex = self.shared_state.battery_mutexes[battery_id]
            log(f"Robo {self.id} - battery_mutex da bateria {battery_id} ADQUIRIDO COM SUCESSO")
    
    def initiate_duel(self, other_robot_id, old_x, old_y, new_x, new_y):
        with self.shared_state.robots_mutex: # ja temos o grid mutex
            my_data = self.shared_state.get_robot_data(self.id)
            other_data = self.shared_state.get_robot_data(other_robot_id)
            if not self.validate_robot_data(my_data) or not self.validate_robot_data(other_data):
                return
            my_power = 2 * my_data['F'] + my_data['E']
            other_power = 2 * other_data['F'] + other_data['E']
            if my_power > other_power:
                other_data['status'] = 0
                self.shared_state.set_robot_data(other_robot_id, other_data)
                
                my_data['x'] = new_x
                my_data['y'] = new_y
                my_data['E'] = max(0, my_data['E'] - 1)
                if my_data['E'] <= 0:
                    my_data['status'] = 0
                self.shared_state.set_robot_data(self.id, my_data)
                
                self.update_grid_cell(old_x, old_y, self.is_on_battery(old_x, old_y))
                self.shared_state.set_grid_cell(new_x, new_y, self.get_robot_symbol())
                
                if my_data['status'] == 0:
                    self.handle_robot_death(new_x, new_y, self.is_on_battery(new_x, new_y))
                    
            elif other_power > my_power:
                my_data['status'] = 0
                self.shared_state.set_robot_data(self.id, my_data)
                self.handle_robot_death(old_x, old_y, self.is_on_battery(old_x, old_y))
                
            else:
                my_data['status'] = 0
                other_data['status'] = 0
                self.shared_state.set_robot_data(self.id, my_data)
                self.shared_state.set_robot_data(other_robot_id, other_data)
                self.update_grid_cell(old_x, old_y, self.is_on_battery(old_x, old_y))
                self.update_grid_cell(new_x, new_y, self.is_on_battery(new_x, new_y))
                if self.current_battery_id is not None:
                    self.release_battery_mutex()

    def release_battery_mutex(self):
        if self.current_battery_mutex is not None:
            try:
                log(f"Robo {self.id} - LIBERANDO battery_mutex da bateria {self.current_battery_id}")
                self.current_battery_mutex.release()
                log(f"Robo {self.id} - battery_mutex da bateria {self.current_battery_id} LIBERADO COM SUCESSO")
            except Exception as e:
                log(f"Robo {self.id} - ERRO ao liberar battery_mutex da bateria {self.current_battery_id}: {e}")
                pass
            finally:
                old_battery_id = self.current_battery_id
                self.current_battery_id = None
                self.current_battery_mutex = None
                log(f"Robo {self.id} - Referências do battery_mutex da bateria {old_battery_id} limpas")

    def housekeeping(self):
        log(f"Robo {self.id} - Thread housekeeping iniciada")
        while self.running:
            time.sleep(0.4 + random.uniform(0, 0.1))
            robot_data = self.update_robot_state(self.id)
            if not robot_data:
                log(f"Robo {self.id} - Housekeeping: robo morto, encerrando thread")
                break
                
            on_battery_now = self.is_on_battery(robot_data['x'], robot_data['y'])
            battery_id_under_robot = self.find_battery_at_position(robot_data['x'], robot_data['y'])

            if on_battery_now and self.current_battery_id == battery_id_under_robot:
                log(f"Robo {self.id} - Housekeeping: carregando energia na bateria {battery_id_under_robot}")
                self.update_robot_state(self.id, energy_difference=5)
            else:
                updated_data = self.update_robot_state(self.id, energy_difference=-0.5)
                if updated_data and updated_data['status'] == 0:
                    log(f"Robo {self.id} - Housekeeping: robo morreu")
                    with self.shared_state.grid_mutex:
                        self.handle_robot_death(robot_data['x'], robot_data['y'], on_battery_now)
                    break

    def run(self):
        log(f"Robo {self.id} - Processo iniciado")
        housekeeping_thread = None
        try:
            self.attach_shared_memory()
            time.sleep(0.01 * self.id)
            self.initialize_arena_if_needed()
            housekeeping_thread = threading.Thread(target=self.housekeeping, daemon=True)
            housekeeping_thread.start()
            
            log(f"Robo {self.id} - Aguardando inicialização do arena")
            while not self.shared_state.get_flags()['init_done']:
                time.sleep(0.1)
            
            log(f"Robo {self.id} - Arena inicializada, começando sense_act")
            self.sense_act()
        except Exception as e:
            log(f"Robo {self.id} - ERRO no processo principal: {e}")
            pass
        finally:
            log(f"Robo {self.id} - Finalizando processo")
            self.running = False
            if housekeeping_thread and housekeeping_thread.is_alive():
                housekeeping_thread.join(timeout=0.2)
            if self.current_battery_id is not None:
                log(f"Robo {self.id} - Liberando mutex final da bateria {self.current_battery_id}")
                self.release_battery_mutex()