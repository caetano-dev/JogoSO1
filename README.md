# <span style="color: #8B008B">Trabalho Final de Sistemas Operacionais I</span>
Integrantes do Grupo

 * Enzo Moraes da Costa 
 * Gabriel de Menezes Balthazar
 * Marcos Vinícius Alves Martins
 * Pedro Caetano Pires

Professor
 * Helio do Nascimento Cunha Neto

 ## <span style="color: #8B008B"></span>

  ## <span style="color: #8B008B">Prevenção do Deadlock</span>

Antes de tudo, precisamos ressaltar que essa prevenção está numa branch separada, chamada de 'preventDeadlock', e não na main.<br>
 ### <span style="color: #8B008B">Como isso funciona?</span>

Durante o desenvolvimento do programa, percebemos que era possível a ocorrência de um deadlock na situação de ter um robô querendo entrar em uma bateria que já tem um outro robô, enquanto esse que está na bateria está tentando sair.
Isso acontecia pois não faziamos a obtenção dos mutexes na ordem correta, então poderia acontecer essa situação em que eles se travariam.
Para tratamento disso, mudamos para garantir que o sistema apenas pegue o mutex da bateria quando já tiver o mutex do tabuleiro.
Todas essas coisas estão presentes na classe robot.py, nas funções 'try_move' e 'try_move_to_battery'. Os movimentos dos robôs que podem causar deadlock recebem um tratamento especial, para facilitar a vizualização do que está acontecendo no log.

Exemplo de deadlock: 

Robô 0 adquire grid_mutex e tenta se mover para a bateria 1, enquanto o robô 4 adquire battery_mutex da bateria 1 e tenta se mover para o grid_mutex. 

```
[12:15:15.793] Robo 0 - grid_mutex ADQUIRIDO
[12:15:15.796] Robo 0 - Encontrou bateria 1, adquirindo mutex
[12:15:15.796] RISCO DE DEADLOCK: Robo 0 - Tentando adquirir battery_mutex já tendo grid_mutex
[12:15:15.848] Robo 0 - TENTANDO ADQUIRIR battery_mutex da bateria 1
```

```
[12:15:16.033] Robo 4 - ADQUIRINDO grid_mutex para mover de (2,12) para (3,12)
[12:15:16.033] RISCO DE DEADLOCK: Robo 4 - Adquirindo grid_mutex primeiro
[12:15:16.033] RISCO DE DEADLOCK: Robo 4 - Já possui mutex da bateria 1
```

depois disso, o deadlock ocorre e nenhum outro robô consegue se mover, e o jogo fica travado.

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