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
Isso acontecia pois não faziamos o tratamento de obtenção dos mutex, então poderia acontecer essa situação em que eles se travariam.
Para tratamento disso, mudamos para garantir que o sistema apenas pegue o mutex da bateria apenas quando tiver o mutex do tabuleiro.