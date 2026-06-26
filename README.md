# Series Mode

Programa simples para Windows que monitora o áudio do computador e desliga o PC automaticamente após um período sem áudio e sem interação do usuário.

A ideia principal é usar o programa antes de dormir assistindo séries, vídeos ou filmes. Enquanto houver áudio tocando, o programa não conta o tempo. Quando o áudio para, ele começa a contar. Se o computador também estiver sem uso por mouse ou teclado, o programa exibe um aviso e depois desliga o PC.

## Funcionalidades

- Monitora o áudio do dispositivo padrão do Windows.
- Detecta ausência de áudio.
- Detecta inatividade de mouse e teclado.
- Exibe aviso antes do desligamento.
- Possui modo teste para simular o desligamento sem desligar o computador.
- Pode ser pausado ou fechado a qualquer momento.

## Tecnologias

- Python
- Tkinter
- pycaw
- comtypes
- uv

## Como instalar

Este projeto usa `uv` para gerenciar o ambiente virtual e as dependências.

Dentro da pasta do projeto, rode:

```powershell
uv sync
````

## Como executar

```powershell
uv run python main.py
```

## Configurações principais

As configurações ficam no início do arquivo `main.py`:

```python
MODO_TESTE = False
TEMPO_SEM_AUDIO_PARA_DESLIGAR = 30 * 60
TEMPO_SEM_MOUSE_TECLADO = 5 * 60
TEMPO_AVISO_ANTES_DESLIGAR = 60
LIMITE_AUDIO = 0.003
TEMPO_AUDIO_PARA_ARMAR = 5
```

## Atenção

Com `MODO_TESTE = False`, o programa desliga o computador de verdade quando as condições são atendidas.

Antes de usar em modo real, teste com:

```python
MODO_TESTE = True
```

Assim o programa apenas mostra uma mensagem quando chegaria ao momento de desligar.

## Próximas melhorias planejadas

* Configurar tempo sem áudio pela interface.
* Configurar modo teste pela interface.
* Escolher entre desligar, suspender ou hibernar.
* Salvar configurações em arquivo.
* Gerar versão `.exe`.
