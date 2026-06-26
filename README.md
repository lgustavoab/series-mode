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
* Bloqueia os campos de configuração enquanto o monitoramento está ativo.
* Exibe status amigável sobre o que está acontecendo.
* Permite cancelar o monitoramento a qualquer momento.
* Possui código modularizado em uma estrutura MVC leve.
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
└─ series_mode/
   ├─ __init__.py
   ├─ constants.py
   ├─ utils.py
   ├─ config.py
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
* executar ou simular a ação final.

#### `series_mode/view.py`

Responsável pela interface gráfica com Tkinter.

Cria e atualiza:

* campos de configuração;
* botões;
* mensagens de status;
* informações técnicas;
* avisos de modo teste ou modo real.

#### `series_mode/config.py`

Responsável pelo arquivo `config.json`.

Cuida de:

* carregar configurações salvas;
* salvar novas configurações;
* validar valores;
* aplicar valores padrão quando necessário.

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

Para gerar o executável em modo pasta, rode:

```powershell
uv run pyinstaller --windowed --name "Series Mode" main.py
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

Na primeira execução, o programa poderá criar automaticamente o arquivo:

```text
config.json
```

Esse arquivo guarda as últimas configurações usadas pelo usuário.

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

## Arquivo de configuração

O programa salva automaticamente as últimas configurações usadas em um arquivo chamado:

```text
config.json
```

Ao executar pelo Python, esse arquivo é criado na raiz do projeto.

Quando o programa é empacotado como `.exe`, o arquivo de configuração é criado ao lado do executável.

Esse arquivo não deve ser enviado para o GitHub, porque cada usuário pode ter suas próprias configurações.

Por isso, o arquivo fica no `.gitignore`.

## Atenção

Com o modo teste desativado, o programa pode desligar, suspender ou hibernar o computador de verdade.

Antes de usar em modo real, teste o comportamento com o modo teste ativado.

## Limitações conhecidas

* O programa funciona apenas no Windows.
* O monitoramento de áudio depende do dispositivo padrão de saída do Windows.
* A ação de suspender pode variar conforme as configurações de energia do Windows. Em alguns computadores, o comando de suspensão pode se comportar como hibernação.
* O programa precisa estar aberto para funcionar. Ao fechar a janela, o monitoramento é encerrado.
* Atualmente, o dispositivo de áudio monitorado é sempre o dispositivo padrão do Windows.
* A versão empacotada em modo pasta precisa ser distribuída com todos os arquivos gerados dentro de `dist/Series Mode/`.

## Próximas melhorias possíveis

* Adicionar ícone personalizado ao programa.
* Gerar uma versão em arquivo único com `--onefile`.
* Criar atalho para a área de trabalho.
* Criar uma release no GitHub com o executável compactado.
* Polir ainda mais o visual da interface.
* Permitir escolher o dispositivo de áudio diretamente pela interface.
* Adicionar opção para iniciar minimizado.
* Adicionar logs simples de eventos.
* Criar uma tela de “sobre” com informações do projeto.

## Status do projeto

O projeto já possui uma primeira versão funcional com interface gráfica, persistência de configurações, modo teste e ações reais para desligar, suspender ou hibernar.

A ideia principal já está implementada: automatizar o desligamento do computador com base em ausência de áudio e inatividade real do usuário.

O código também já foi refatorado para uma estrutura modular em MVC leve, separando interface, controller, configuração, monitoramento de áudio, inatividade e ações do sistema.

Além disso, o projeto já pode ser empacotado como executável para Windows em modo pasta usando PyInstaller.
