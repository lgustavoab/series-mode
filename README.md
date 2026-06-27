# Series Mode

Programa para Windows que monitora áudio e inatividade do usuário para desligar, suspender ou hibernar o computador automaticamente após um período sem som e sem interação.

## Por que este projeto existe

Este projeto nasceu de um problema real.

Eu costumo assistir séries e vídeos pelo computador, enviando a imagem para a TV. O problema é que, quando eu acabava dormindo, o computador continuava ligado por horas.

As soluções padrão não resolviam bem o meu caso:

* O modo de suspensão do Windows podia suspender o computador mesmo enquanto eu ainda estava assistindo.
* O Agendador de Tarefas era rígido demais, porque dependia de um horário fixo.
* Eu queria uma solução que entendesse melhor o contexto: se ainda existe áudio tocando e se eu ainda estou usando o mouse ou teclado.

Por isso criei o Series Mode.

A ideia é simples: o programa só age quando o áudio para e o computador fica sem interação por um tempo configurado.

## O que o programa faz

O Series Mode monitora o áudio do dispositivo padrão de saída do Windows e também verifica há quanto tempo o usuário não mexe no mouse ou teclado.

Quando o programa identifica que:

1. já houve áudio tocando por alguns segundos;
2. o áudio parou;
3. o computador está sem uso por mouse/teclado;
4. o tempo configurado sem áudio foi atingido;

ele exibe um aviso final e, se nada for cancelado, executa a ação escolhida.

As ações disponíveis são:

* Desligar
* Suspender
* Hibernar

Também existe um modo teste para simular a ação sem realmente desligar, suspender ou hibernar o computador.

Além disso, o programa registra o último evento relevante em um arquivo local. Assim, ao abrir o aplicativo no dia seguinte, é possível ver se o Series Mode iniciou o aviso final, simulou uma ação, executou uma ação real ou teve a ação cancelada.

## Como funciona

O fluxo principal é:

1. O usuário abre o programa antes de assistir.
2. Configura os tempos desejados.
3. Clica em **Iniciar monitoramento**.
4. O programa aguarda detectar áudio por alguns segundos para se armar.
5. Enquanto houver áudio, nada acontece.
6. Quando o áudio para, o programa observa a inatividade do mouse e teclado.
7. Se o computador continuar sem áudio e sem interação, a contagem é iniciada.
8. Antes da ação final, o programa exibe um aviso.
9. Se o áudio voltar, se o usuário mexer no mouse/teclado ou cancelar o monitoramento, a ação é cancelada.
10. Se nada for cancelado, o programa simula ou executa a ação final configurada.
11. O último evento é salvo localmente e exibido na próxima abertura do programa.

## Funcionalidades

* Monitora o pico de áudio do dispositivo padrão do Windows.
* Detecta ausência de áudio.
* Detecta inatividade de mouse e teclado.
* Exige áudio inicial para armar o monitoramento.
* Permite configurar tempo sem áudio.
* Permite configurar tempo mínimo sem mouse/teclado.
* Permite configurar aviso final antes da ação.
* Permite escolher entre desligar, suspender ou hibernar.
* Possui modo teste para simular a ação final com segurança.
* Salva as últimas configurações usadas em `config.json`.
* Registra o último evento relevante em `last_event.json`.
* Exibe na interface o último evento registrado.
* Bloqueia os campos de configuração enquanto o monitoramento está ativo.
* Exibe status amigável sobre o que está acontecendo.
* Permite cancelar o monitoramento a qualquer momento.
* Possui código modularizado em uma estrutura MVC leve.
* Possui ícone personalizado para o executável e para a janela do programa.
* Pode ser empacotado como executável para Windows com PyInstaller.

## Tecnologias utilizadas

* Python
* Tkinter
* pycaw
* comtypes
* uv
* PyInstaller

## Arquitetura do projeto

O projeto começou como um único arquivo `main.py`, mas foi refatorado para uma estrutura mais organizada, separando responsabilidades em módulos.

A estrutura atual segue uma abordagem de **MVC leve**, adequada para uma aplicação desktop pequena.

```text
series-mode/
│
├─ main.py
├─ README.md
├─ pyproject.toml
├─ uv.lock
│
├─ assets/
│  └─ series_mode.ico
│
└─ series_mode/
   ├─ __init__.py
   ├─ constants.py
   ├─ utils.py
   ├─ config.py
   ├─ event_log.py
   ├─ audio_monitor.py
   ├─ idle_monitor.py
   ├─ power_actions.py
   ├─ view.py
   └─ controller.py
```

### Responsabilidade dos arquivos

#### `main.py`

Ponto de entrada do programa.

Ele apenas cria a janela principal do Tkinter e inicia o controller da aplicação.

#### `series_mode/controller.py`

É o cérebro do programa.

Controla o fluxo principal da aplicação:

* iniciar monitoramento;
* cancelar monitoramento;
* validar configurações;
* monitorar áudio e inatividade;
* controlar o aviso final;
* registrar eventos;
* executar ou simular a ação final.

#### `series_mode/view.py`

Responsável pela interface gráfica com Tkinter.

Cria e atualiza:

* campos de configuração;
* botões;
* mensagens de status;
* informações técnicas;
* último evento registrado;
* avisos de modo teste ou modo real;
* ícone da janela do programa.

#### `series_mode/config.py`

Responsável pelo arquivo `config.json`.

Cuida de:

* carregar configurações salvas;
* salvar novas configurações;
* validar valores;
* aplicar valores padrão quando necessário.

#### `series_mode/event_log.py`

Responsável pelo arquivo `last_event.json`.

Cuida de:

* salvar o último evento relevante;
* carregar o último evento salvo;
* formatar a mensagem exibida na interface.

O objetivo não é criar um histórico completo, mas manter apenas o último evento importante do programa.

#### `series_mode/audio_monitor.py`

Responsável por medir o áudio do dispositivo padrão de saída do Windows usando `pycaw`.

#### `series_mode/idle_monitor.py`

Responsável por detectar há quanto tempo o usuário não mexe no mouse ou teclado, usando recursos do Windows.

#### `series_mode/power_actions.py`

Responsável pelas ações finais do sistema:

* desligar;
* suspender;
* hibernar.

#### `series_mode/constants.py`

Guarda constantes internas do programa, como limite de áudio, tempo necessário para armar o monitoramento e ações válidas.

#### `series_mode/utils.py`

Guarda funções auxiliares usadas em diferentes partes do projeto.

#### `assets/series_mode.ico`

Ícone personalizado usado no executável e na janela do programa.

## Requisitos

* Windows
* Python
* uv
* Saída de áudio configurada corretamente no Windows

O programa monitora o dispositivo padrão de saída de áudio do Windows. Portanto, se você estiver usando uma TV, monitor externo ou outro dispositivo de áudio, ele precisa estar selecionado como saída padrão.

## Instalação

Este projeto usa `uv` para gerenciar ambiente e dependências.

Clone o repositório:

```powershell
git clone https://github.com/lgustavoab/series-mode.git
```

Entre na pasta:

```powershell
cd series-mode
```

Instale as dependências:

```powershell
uv sync
```

## Como executar em modo desenvolvimento

Dentro da pasta do projeto, rode:

```powershell
uv run python main.py
```

## Como gerar o executável

O projeto usa PyInstaller para gerar uma versão executável para Windows.

Para gerar o executável em modo pasta, com ícone personalizado, rode:

```powershell
uv run pyinstaller --windowed --name "Series Mode" --icon "assets/series_mode.ico" --add-data "assets/series_mode.ico;assets" main.py
```

Após o build, o executável será criado em:

```text
dist/Series Mode/Series Mode.exe
```

Para distribuir o programa, envie a pasta inteira:

```text
dist/Series Mode/
```

Essa pasta contém o executável e os arquivos necessários para funcionamento.

## Executando a versão empacotada

Depois de gerar o executável, abra:

```text
dist/Series Mode/Series Mode.exe
```

Na primeira execução, o programa poderá criar automaticamente os arquivos locais:

```text
config.json
last_event.json
```

Esses arquivos guardam, respectivamente, as configurações do usuário e o último evento relevante registrado pelo programa.

## Configurações disponíveis

Na interface do programa, é possível configurar:

### Tempo sem áudio para agir

Define por quanto tempo o computador precisa ficar sem áudio antes da ação final ser considerada.

Exemplo:

```text
30 minutos
```

### Tempo mínimo sem mouse/teclado

Define quanto tempo o computador precisa estar sem interação do usuário.

Essa verificação evita que o programa execute uma ação enquanto o usuário ainda está acordado e usando o computador.

### Aviso final antes da ação

Define quantos segundos o programa deve esperar antes de executar a ação final.

Durante esse aviso, a ação pode ser cancelada ao:

* mexer no mouse;
* usar o teclado;
* voltar o áudio;
* clicar em **Cancelar monitoramento**.

### Ação final

Define o que o programa deve fazer ao final da contagem:

* Desligar
* Suspender
* Hibernar

### Modo teste

Quando o modo teste está ativado, nenhuma ação real é executada.

O programa apenas simula o comportamento e mostra que aquele seria o momento da ação final.

Esse modo é recomendado para testar as configurações antes de usar o programa em modo real.

## Último evento registrado

O programa exibe na interface o último evento relevante registrado.

Esse recurso ajuda a verificar, ao abrir o programa posteriormente, se o Series Mode chegou a iniciar um aviso, simular uma ação, executar uma ação real ou cancelar uma ação.

Os eventos possíveis incluem:

* aviso final iniciado;
* ação cancelada;
* ação simulada em modo teste;
* ação real executada.

O registro é salvo em:

```text
last_event.json
```

Esse arquivo guarda apenas o último evento. Ele não mantém um histórico completo de uso.

## Arquivos locais

O programa pode criar automaticamente dois arquivos locais:

```text
config.json
last_event.json
```

### `config.json`

Guarda as últimas configurações usadas pelo usuário.

Ao executar pelo Python, esse arquivo é criado na raiz do projeto.

Quando o programa é empacotado como `.exe`, o arquivo de configuração é criado ao lado do executável.

### `last_event.json`

Guarda o último evento relevante registrado pelo programa.

Ao executar pelo Python, esse arquivo é criado na raiz do projeto.

Quando o programa é empacotado como `.exe`, o arquivo de último evento é criado ao lado do executável.

Esses arquivos não devem ser enviados para o GitHub, porque cada usuário pode ter suas próprias configurações e registros locais.

Por isso, ambos ficam no `.gitignore`.

## Atenção

Com o modo teste desativado, o programa pode desligar, suspender ou hibernar o computador de verdade.

Antes de usar em modo real, teste o comportamento com o modo teste ativado.

## Limitações conhecidas

* O programa funciona apenas no Windows.
* O monitoramento de áudio depende do dispositivo padrão de saída do Windows.
* A ação de suspender pode variar conforme as configurações de energia do Windows. Em alguns computadores, o comando de suspensão pode se comportar como hibernação.
* O programa precisa estar aberto para funcionar. Ao fechar a janela, o monitoramento é encerrado.
* Atualmente, o dispositivo de áudio monitorado é sempre o dispositivo padrão do Windows.
* O arquivo `last_event.json` guarda apenas o último evento, não um histórico completo.
* A versão empacotada em modo pasta precisa ser distribuída com todos os arquivos gerados dentro de `dist/Series Mode/`.

## Próximas melhorias possíveis

* Gerar uma versão em arquivo único com `--onefile`.
* Criar atalho para a área de trabalho.
* Criar uma release no GitHub com o executável compactado.
* Polir ainda mais o visual da interface.
* Permitir escolher o dispositivo de áudio diretamente pela interface.
* Adicionar opção para iniciar minimizado.
* Adicionar logs simples de eventos.
* Criar uma tela de “sobre” com informações do projeto.

## Status do projeto

O projeto já possui uma primeira versão funcional com interface gráfica, persistência de configurações, modo teste, registro do último evento e ações reais para desligar, suspender ou hibernar.

A ideia principal já está implementada: automatizar o desligamento do computador com base em ausência de áudio e inatividade real do usuário.

O código também já foi refatorado para uma estrutura modular em MVC leve, separando interface, controller, configuração, registro de eventos, monitoramento de áudio, inatividade e ações do sistema.

Além disso, o projeto já pode ser empacotado como executável para Windows em modo pasta usando PyInstaller, com ícone personalizado no executável e na janela do programa.
