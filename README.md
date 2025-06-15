# <span style="color: #8B008B">Trabalho Final de Sistemas Operacionais I</span>
Integrantes do Grupo

 * Enzo Moraes da Costa 
 * Gabriel de Menezes Balthazar
 * Marcos Vinícius Alves Martins
 * Pedro Caetano Pires

Professor
 * Helio do Nascimento Cunha Neto

 ## <span style="color: #8B008B"></span>


Antes de tudo, precisamos ressaltar que essa prevenção está numa branch separada, chamada de 'preventDeadlock', e não na main.<br>

### <span style="color: #8B008B">Como isso funciona?</span>

Durante o desenvolvimento do programa, identificamos que era possível a ocorrência de um **deadlock clássico** em situações onde múltiplos robôs competem pelos mesmos recursos compartilhados: as baterias e o grid do jogo.

#### <span style="color: #8B008B">Cenário do Deadlock</span>

O deadlock ocorre quando dois ou mais robôs adquirem mutexes em ordens diferentes, criando uma dependência circular:

1. Robô A adquire o `grid_mutex` e depois tenta adquirir o `battery_mutex` de uma bateria específica
2. Robô B já possui o `battery_mutex` da mesma bateria e tenta adquirir o `grid_mutex`
3. Resultado: Robô A espera pelo mutex que Robô B possui, enquanto Robô B espera pelo mutex que Robô A possui

Esta situação cria uma **espera circular** onde nenhum dos robôs pode prosseguir, travando todo o sistema.

#### <span style="color: #8B008B">Condições para Deadlock</span>

O deadlock acontece quando todas as quatro condições são satisfeitas:
- Exclusão mútua: Os mutexes só podem ser possuídos por um robô por vez
- Posse e espera: Robôs mantêm recursos enquanto esperam por outros
- Não preempção: Mutexes não podem ser forçadamente liberados
- Espera circular: Existe um ciclo de dependências entre os robôs

### <span style="color: #8B008B">Exemplo de Deadlock Detectado</span>

Robô 0 adquire `grid_mutex` e tenta se mover para a bateria 1, enquanto o robô 4 já possui `battery_mutex` da bateria 1 e tenta adquirir o `grid_mutex`: 

**Robô 0 (possui grid_mutex, quer battery_mutex):**
```
[12:15:15.793] Robo 0 - grid_mutex ADQUIRIDO
[12:15:15.796] Robo 0 - Encontrou bateria 1, adquirindo mutex
[12:15:15.796] RISCO DE DEADLOCK: Robo 0 - Tentando adquirir battery_mutex já tendo grid_mutex
[12:15:15.848] Robo 0 - TENTANDO ADQUIRIR battery_mutex da bateria 1
```

**Robô 4 (possui battery_mutex, quer grid_mutex):**
```
[12:15:16.033] Robo 4 - ADQUIRINDO grid_mutex para mover de (2,12) para (3,12)
[12:15:16.033] RISCO DE DEADLOCK: Robo 4 - Adquirindo grid_mutex primeiro
[12:15:16.033] RISCO DE DEADLOCK: Robo 4 - Já possui mutex da bateria 1
```

**Resultado**: O deadlock ocorre e nenhum outro robô consegue se mover, causando o travamento completo do jogo.

### <span style="color: #8B008B">Prevenção Implementada</span>

Para resolver este problema, fizemos a aquisição ordenada de recursos:

#### <span style="color: #8B008B">Ordem consistente para mutexes</span>

Todos os robôs agora seguem a mesma ordem de aquisição: `battery_mutex` → `grid_mutex`

```python
#Ordem consistente em ambas as funções try_move e try_move_to_battery
if not self.acquire_battery_mutex(battery_id): #Se não conseguir adquirir o mutex da bateria, não prossegue
    #...
    return
try:
    #...
    with self.shared_state.grid_mutex: #Adquire o mutex do grid
        # Processa movimento
```

Esta implementação está presente nas funções `try_move` e `try_move_to_battery` da classe `robot.py`, garantindo que não hajam deadlocks.

Nos logs:

```
[19:14:20.152] Robo 1 - TENTANDO ADQUIRIR battery_mutex da bateria 1
[19:14:20.152] Robo 1 - battery_mutex da bateria 1 ADQUIRIDO COM SUCESSO
[19:14:20.152] Robo 1 - ADQUIRINDO grid_mutex para mover de (15,4) para (15,3)
[19:14:20.152] PREVENÇÃO DEADLOCK: Robô 1 - Seguindo ordem consistente: battery_mutex → grid_mutex
[19:14:20.153] Robo 1 - grid_mutex ADQUIRIDO
```

## <span style="color: #8B008B">O que é o que?</span>

### <span style="color: #8B008B"> - main.py</span>

É a classe que é responsável por inicializar o programa. Logo de cara ela limpa um possível arquivo de log já existente, para poder manter a consistência de o log só retratar uma única execução. Além disso, ela inicializa o grid na memória compartilhada, instancia os robôs e fica responsável por administrar todo o processo, de forma que está sempre esperando um input do usuário para ou movimentar o player (através de inputs nas teclas de seta enviados para a classe robot.py) ou encerrar o jogo manualmente (através do input da tecla 'q'). Por fim, também é responsável por atualizar os estados do jogo como um todo.

### <span style="color: #8B008B"> - viewer.py</span>

É a classe responsável por printar o jogo na tela, como o mapa, os status dos robos e a mensagem final do jogo, se é Vitória ou Empate.

### <span style="color: #8B008B"> - robot.py</span>

Responsável por administrar tudo relacionados aos robôs, como inicializar com robôs atributos aleatórios, inicializar e anexar a memória compartilhada a cada robô, inicializar as baterias do mapa, realizar o movimentos dos robôs, atualizar o estado do robô, as ações referentes às baterias no mapa e lidar com os duelos entre robôs, além de uma forma rudimentar de 'IA', para tomar as decisões para os robôs não controlados pelo jogados e documentar os riscos de deadlock nas ações dos robôs. 

### <span style="color: #8B008B"> - shared_memory.py</span>

É aonde estarão todos os dados que necessitam ser compartilhados através de diferentes classes do programa, para manter esses dados 'centralizados' e evitar algum erro de transferência inconsistente ou uma ação não ter os dados necessários para alguma ação.

 ## <span style="color: #8B008B">O ciclo de funcionamento</span>

Logo após iniciar a execução, você verá a tela abaixo:

![alt text](image-1.png)

A partir disso, você verá o status de cara robô, como energia, força e velocidade, além de ver se um robô está em uma bateria recebendo carga, pelo ícone de relâmpago do lado de cada um.

## <span style="color: #8B008B">Principais Funções do Sistema</span>

### <span style="color: #8B008B">main.py - Funções Principais</span>

#### **`main(stdscr)`**
Função principal que gerencia todo o ciclo de vida do jogo. Inicializa o estado compartilhado, cria e inicia os processos dos robôs, gerencia a interface gráfica usando curses e processa inputs do usuário. Também é responsável por finalizar todos os processos quando o jogo termina.

#### **`update_alive_count(shared_state, num_robots)`**
Conta quantos robôs ainda estão vivos no jogo, determina se há um vencedor ou empate, e atualiza as flags do jogo. Esta função é chamada continuamente para ver se o jogo acabou.

### <span style="color: #8B008B">robot.py - Funções Principais</span>

#### **`__init__(self, robot_id, is_player, shared_objects)`**
Construtor da classe Robot que inicializa um robô com ID único, determina se é controlado pelo jogador ou não e configura as estruturas necessárias para comunicação entre processos.

#### **`attach_shared_memory(self)`**
Anexa o robô ao estado de memória compartilhada, permitindo que ele acesse e modifique dados compartilhados como o grid, estado dos robôs e baterias.

#### **`initialize_arena_if_needed(self)`**
Inicializa o arena do jogo apenas uma vez. O primeiro robô a chamar esta função coloca as baterias no mapa e inicializa os dados compartilhados de todos os robôs em posições aleatórias.

#### **`place_batteries(self)`**
Posiciona aleatoriamente as baterias no mapa, garantindo que cada bateria ocupe 2 células horizontais e não sobreponha com as barreiras.

#### **`sense_act(self)`**
Loop principal de decisão e ação do robô. Ela analisa o ambiente, decide as próximas ações (movimento ou coleta de bateria) e as executa.

#### **`try_move(self, dx, dy, robot_data_snapshot)`**
Tenta mover o robô para uma nova posição. Verifica colisões, gerencia movimentos para baterias, e inicia duelos quando encontra outros robôs. Esta função é onde o deadlock pode ocorrer devido à ordem de aquisição de mutexes.

#### **`try_move_to_battery(self, old_x, old_y, new_x, new_y)`**
Versão especializada de movimento que primeiro adquire o mutex da bateria antes do mutex do grid.

#### **`initiate_duel(self, other_robot_id, old_x, old_y, new_x, new_y)`**
Gerencia o combate entre dois robôs quando eles ocupam a mesma posição. Calcula o poder de cada robô (2×Força + Energia) e determina o vencedor, podendo resultar em empate onde ambos morrem.

#### **`acquire_battery_mutex(self, battery_id)`** / **`release_battery_mutex(self)`**
Funções que gerenciam a aquisição e liberação segura dos mutexes das baterias, garantindo que apenas um robô possa interagir com uma bateria específica por vez.

#### **`housekeeping(self)`**
Thread separada que roda em paralelo ao loop principal, responsável por atualizar a energia do robô. 

#### **`update_robot_state(self, robot_id, new_x=None, new_y=None, energy_difference=0, new_status=None)`**
Função central para modificar o estado de um robô. Atualiza posição, energia e status, verificando automaticamente se o robô morreu por falta de energia.

#### **`find_nearest_battery_direction(self, grid_snapshot, robot_data)`**
Analisa o grid para encontrar a bateria mais próxima e retornando a direção para se mover em direção a ela. Serve apenas para robôs que não são controlados pelo jogador.

### <span style="color: #8B008B">shared_memory.py - Funções Principais</span>

#### **`create_shared_state()`**
Cria e inicializa todas as estruturas de dados compartilhadas usando multiprocessing.Manager(). Configura o grid com bordas e obstáculos, inicializa arrays para robôs e baterias, e cria todos os mutexes necessários.

#### **`get_grid_cell(self, x, y)` / `set_grid_cell(self, x, y, value)`**
Funções para ler e escrever células individuais do grid. Incluem verificação de limites para evitar acessos inválidos.

#### **`get_robot_data(self, robot_id)` / `set_robot_data(self, robot_id, robot_data)`**
Gerenciam o acesso aos dados dos robôs (posição, energia, força, velocidade, status).

#### **`get_battery_data(self, battery_id)` / `set_battery_data(self, battery_id, battery_data)`**
Controlam o acesso às informações das baterias (posição, estado de coleta, proprietário atual).

#### **`take_grid_snapshot(self)`**
Cria uma cópia completa do estado atual do grid para análise.

### <span style="color: #8B008B">viewer.py - Funções Principais</span>

#### **`display_grid(self, stdscr)`**
Função principal de renderização que desenha o grid do jogo, status dos robôs, contadores e mensagens de controle na tela.

#### **`is_robot_on_battery(self, x, y)`**
Verifica se um robô está posicionado em uma bateria para mostrar o indicador de carregamento (⚡) na interface.

#### **`format_game_status_message(self, flags)`**
Formata as mensagens de fim de jogo (vitória ou empate) baseado no estado atual das flags do jogo.

## <span style="color: #8B008B">Fluxo de Execução</span>

### **Ordem de Execução:**
1. **main.py** limpa logs e inicializa estruturas compartilhadas
2. Cria e inicia **NUM_ROBOTS** processos Robot
3. Cada robô anexa à memória compartilhada e inicializa o arena (apenas o primeiro)
4. Robôs começam seus loops **sense_act()** e threads **housekeeping()**
5. **main()** entra no loop de interface gráfica e processa inputs do usuário
6. **update_alive_count()** verifica continuamente condições de fim de jogo

### **Mutexes Utilizados:**
- `init_mutex`: Garante inicialização única do arena
- `grid_mutex`: Protege modificações no grid do jogo  
- `robots_mutex`: Sincroniza atualizações nos dados dos robôs
- `battery_mutexes[]`: Array de mutexes individuais para cada bateria 