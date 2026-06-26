import ctypes
import os
import time
import tkinter as tk
from tkinter import messagebox

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation


# =====================================================
# CONFIGURAÇÕES GERAIS DO PROGRAMA
# =====================================================
# Altere estes valores para ajustar o comportamento do Series Mode.
#
# O objetivo do programa é:
#   1. Esperar detectar áudio tocando.
#   2. "Armar" o monitoramento depois de alguns segundos com áudio.
#   3. Quando o áudio parar, começar uma contagem.
#   4. Só permitir o desligamento se o PC também estiver sem uso.
#   5. Mostrar um aviso final antes de desligar.
#
# Os tempos estão em segundos.
#
# Exemplos:
#   30 * 60 = 30 minutos
#   5 * 60 = 5 minutos
#   60 = 60 segundos


MODO_TESTE = False
# Define se o programa está em modo teste ou modo real.
#
# True:
#   O programa NÃO desliga o computador.
#   Ele apenas mostra uma mensagem dizendo que o desligamento aconteceria.
#   Use esse modo quando quiser testar a lógica com segurança.
#
# False:
#   O programa desliga o computador de verdade quando as condições forem atendidas.
#   Use somente depois de confirmar que:
#     - o áudio está sendo detectado corretamente
#     - o contador está funcionando
#     - o cancelamento ao mexer no mouse/teclado está funcionando


TEMPO_SEM_AUDIO_PARA_DESLIGAR = 30 * 60
# Tempo que o computador precisa ficar sem áudio antes de iniciar o desligamento.
#
# No uso real:
#   30 * 60 = 30 minutos sem áudio.
#
# Exemplo prático:
#   Você está assistindo série.
#   Enquanto a série toca áudio, o programa não conta nada.
#   Quando o episódio termina, pausa ou fica parado sem som,
#   o programa começa a contar esse tempo.
#
# Se o áudio voltar antes do tempo acabar, a contagem é zerada.


TEMPO_SEM_MOUSE_TECLADO = 5 * 60
# Tempo mínimo sem mexer no mouse ou teclado para permitir o desligamento.
#
# Essa é uma trava de segurança.
# Ela evita que o PC desligue enquanto você ainda está acordado usando o computador sem áudio.
#
# Exemplo:
#   Se a série estiver pausada, mas você estiver mexendo no PC,
#   o programa não deve desligar.
#
# O desligamento só avança quando o computador está:
#   - sem áudio
#   - sem interação do usuário


TEMPO_AVISO_ANTES_DESLIGAR = 60
# Tempo do aviso final antes de desligar o computador.
#
# Quando todas as condições forem atendidas, o programa mostra um aviso.
# Durante esse aviso, ainda dá para cancelar o desligamento.
#
# O desligamento é cancelado se:
#   - o áudio voltar
#   - você mexer no mouse ou teclado
#   - você pausar o monitoramento
#   - você fechar o programa


LIMITE_AUDIO = 0.003
# Sensibilidade usada para decidir se existe áudio tocando.
#
# O programa lê o "pico de áudio" do dispositivo padrão do Windows.
# Se esse pico for maior ou igual ao LIMITE_AUDIO, consideramos que há áudio.
#
# Valores menores deixam o programa mais sensível:
#   0.001 detecta sons mais baixos.
#
# Valores maiores deixam o programa menos sensível:
#   0.005 ou 0.01 ajudam a ignorar ruídos muito baixos.
#
# Recomendação:
#   Mantenha 0.003 se o campo "Pico de áudio" sobe quando a série toca
#   e volta para 0.00000 ou quase zero quando o vídeo pausa.


TEMPO_AUDIO_PARA_ARMAR = 5
# Tempo mínimo de áudio contínuo necessário para armar o monitoramento.
#
# Isso evita que o programa comece a contar silêncio logo que for aberto.
#
# Exemplo:
#   Você abre o programa antes de escolher a série.
#   Ele fica aguardando áudio.
#   Quando a série começa a tocar áudio por 5 segundos,
#   o monitoramento é armado.
#   A partir daí, se o áudio parar, a contagem pode começar.


# =====================================================
# DETECÇÃO DE INATIVIDADE DO WINDOWS
# =====================================================
# Esta parte usa funções do próprio Windows para descobrir
# há quanto tempo o usuário não mexe no mouse ou teclado.
#
# O programa usa essa informação como uma camada extra de segurança:
# ele só desliga se estiver sem áudio E sem interação do usuário.


class LASTINPUTINFO(ctypes.Structure):
    # Estrutura exigida pela função GetLastInputInfo do Windows.
    #
    # cbSize:
    #   Tamanho da estrutura em memória.
    #
    # dwTime:
    #   Momento da última interação do usuário com mouse ou teclado,
    #   medido pelo contador interno do Windows.
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def tempo_sem_mouse_teclado() -> float:
    # Retorna há quantos segundos o usuário não mexe no mouse ou teclado.
    #
    # Se o usuário acabou de mexer no mouse, o valor fica próximo de 0.
    # Se o PC está parado há 5 minutos, retorna aproximadamente 300.
    #
    # Essa função é importante para evitar desligamentos acidentais
    # quando o usuário está usando o PC sem áudio.

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return 0

    millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
    return millis / 1000


# =====================================================
# DETECÇÃO DE ÁUDIO DO DISPOSITIVO PADRÃO
# =====================================================
# Esta parte acessa o dispositivo padrão de saída de áudio do Windows.
#
# No seu caso, quando você seleciona:
#   LG TV (AMD High Definition Audio Device)
#
# como saída de áudio padrão, o programa mede o áudio que está saindo por ela.


class MonitorAudio:
    def __init__(self):
        # Pega o dispositivo padrão de saída de áudio do Windows.
        speakers = AudioUtilities.GetSpeakers()

        # Nas versões atuais do pycaw, GetSpeakers() retorna um AudioDevice.
        # O dispositivo COM real fica dentro de speakers._dev.
        #
        # Aqui acessamos a interface IAudioMeterInformation,
        # que permite ler o pico de áudio atual do dispositivo.
        interface = speakers._dev.Activate(
            IAudioMeterInformation._iid_,
            CLSCTX_ALL,
            None,
        )

        self.meter = interface.QueryInterface(IAudioMeterInformation)

    def pico_audio(self) -> float:
        # Retorna o pico de áudio atual.
        #
        # Valores próximos de 0.00000 indicam silêncio.
        # Valores maiores indicam que existe áudio saindo.
        #
        # Se houver algum erro na leitura, retornamos 0.0 para evitar travar o app.
        try:
            return float(self.meter.GetPeakValue())
        except Exception:
            return 0.0


# =====================================================
# APLICATIVO PRINCIPAL
# =====================================================
# Esta classe controla:
#   - a janela do programa
#   - os botões
#   - os textos exibidos
#   - os contadores
#   - a lógica de áudio, inatividade e desligamento


class ModoSerieApp:
    def __init__(self, root: tk.Tk):
        # Configuração básica da janela.
        self.root = root
        self.root.title("Series Mode")
        self.root.geometry("560x390")
        self.root.resizable(False, False)

        # Cria o monitor de áudio.
        self.monitor_audio = MonitorAudio()

        # Indica se o monitoramento está ativo.
        # Quando False, o programa fica aberto, mas não faz nada.
        self.ativo = True

        # Indica se o monitoramento já foi armado.
        # O programa só arma depois de detectar áudio por alguns segundos.
        self.armado = False

        # Conta por quanto tempo o áudio ficou ativo antes de armar.
        self.audio_detectado_por = 0.0

        # Guarda o momento em que o silêncio começou.
        # Fica como None quando não estamos contando silêncio.
        self.inicio_silencio = None

        # Guarda o momento do último ciclo do loop.
        # Usado para calcular quanto tempo passou entre uma verificação e outra.
        self.ultimo_tick = time.monotonic()

        # Indica se o aviso final de desligamento está ativo.
        self.aviso_ativo = False

        # Contador regressivo do aviso final.
        self.contagem_aviso = TEMPO_AVISO_ANTES_DESLIGAR

        # Título principal da janela.
        self.titulo = tk.Label(
            root,
            text="Series Mode ativado",
            font=("Segoe UI", 18, "bold"),
        )
        self.titulo.pack(pady=14)

        # Texto de status principal.
        self.status = tk.Label(
            root,
            text="Aguardando áudio para armar o monitoramento...",
            font=("Segoe UI", 11),
            wraplength=500,
            justify="center",
        )
        self.status.pack(pady=8)

        # Área de informações técnicas:
        # pico de áudio, tempo sem mouse/teclado, tempo contado etc.
        self.info = tk.Label(
            root,
            text="",
            font=("Consolas", 10),
            justify="left",
        )
        self.info.pack(pady=10)

        # Botão para pausar/retomar o monitoramento sem fechar o programa.
        self.botao_pausar = tk.Button(
            root,
            text="Pausar monitoramento",
            width=28,
            command=self.alternar_monitoramento,
        )
        self.botao_pausar.pack(pady=4)

        # Botão para fechar o programa completamente.
        self.botao_fechar = tk.Button(
            root,
            text="Fechar programa",
            width=28,
            command=self.fechar,
        )
        self.botao_fechar.pack(pady=4)

        # Aviso visual indicando se o programa está em modo teste ou modo real.
        texto_modo = (
            "MODO TESTE ATIVO: o computador não será desligado."
            if MODO_TESTE
            else "MODO REAL: o computador será desligado."
        )

        cor_modo = "darkorange" if MODO_TESTE else "red"

        self.observacao = tk.Label(
            root,
            text=texto_modo,
            font=("Segoe UI", 9, "bold"),
            fg=cor_modo,
        )
        self.observacao.pack(pady=12)

        # Quando o usuário clicar no X da janela,
        # o programa fecha e deixa de monitorar.
        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

        # Inicia o loop principal do programa.
        self.loop()

    def formatar_tempo(self, segundos: float) -> str:
        # Converte segundos em formato MM:SS.
        #
        # Exemplo:
        #   90 segundos vira 01:30.
        segundos = int(max(0, segundos))
        minutos = segundos // 60
        resto = segundos % 60
        return f"{minutos:02d}:{resto:02d}"

    def alternar_monitoramento(self):
        # Pausa ou retoma o monitoramento.
        #
        # Pausar não fecha o programa.
        # Apenas impede que ele conte silêncio ou desligue o computador.

        self.ativo = not self.ativo

        if self.ativo:
            self.titulo.config(text="Series Mode ativado")
            self.botao_pausar.config(text="Pausar monitoramento")
            self.status.config(text="Monitoramento retomado. Aguardando áudio...")
            self.resetar_contadores()
        else:
            self.titulo.config(text="Series Mode pausado")
            self.botao_pausar.config(text="Retomar monitoramento")
            self.status.config(text="Pausado. O computador não será desligado.")
            self.resetar_contadores()

    def resetar_contadores(self):
        # Zera todos os estados temporários do monitoramento.
        #
        # Usamos isso quando:
        #   - o áudio volta
        #   - o usuário cancela o desligamento
        #   - o monitoramento é pausado/retomado
        #   - o modo teste termina
        #
        # Depois de resetar, o programa precisa detectar áudio novamente para armar.

        self.armado = False
        self.audio_detectado_por = 0.0
        self.inicio_silencio = None
        self.aviso_ativo = False
        self.contagem_aviso = TEMPO_AVISO_ANTES_DESLIGAR
        self.ultimo_tick = time.monotonic()

    def iniciar_aviso(self):
        # Inicia o aviso final antes do desligamento.
        #
        # Esse aviso é a última chance de cancelar.
        # Se o usuário mexer no mouse, voltar o áudio ou pausar o programa,
        # o desligamento é cancelado.

        self.aviso_ativo = True
        self.contagem_aviso = TEMPO_AVISO_ANTES_DESLIGAR

        self.titulo.config(text="Aviso de desligamento")
        self.status.config(
            text=(
                "O PC será desligado/simulado em breve. "
                "Mexa no mouse ou clique em Pausar para cancelar."
            )
        )

        self.contagem_regressiva()

    def contagem_regressiva(self):
        # Controla a contagem regressiva do aviso final.
        #
        # A cada segundo, o programa verifica se ainda deve desligar.
        #
        # O desligamento é cancelado se:
        #   - voltar áudio
        #   - o usuário mexer no mouse/teclado
        #   - o monitoramento for pausado

        if not self.aviso_ativo:
            return

        pico = self.monitor_audio.pico_audio()
        sem_interacao = tempo_sem_mouse_teclado()

        if pico >= LIMITE_AUDIO or sem_interacao < 3 or not self.ativo:
            self.status.config(text="Desligamento cancelado. Monitoramento reiniciado.")
            self.resetar_contadores()
            self.root.after(1000, self.loop)
            return

        self.info.config(
            text=(
                f"Desligando/simulando em: {self.contagem_aviso} segundos\n"
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {self.formatar_tempo(sem_interacao)}\n"
                f"Modo teste: {MODO_TESTE}"
            )
        )

        if self.contagem_aviso <= 0:
            self.executar_desligamento()
            return

        self.contagem_aviso -= 1
        self.root.after(1000, self.contagem_regressiva)

    def executar_desligamento(self):
        # Executa a ação final.
        #
        # Em modo teste:
        #   Mostra uma mensagem e não desliga o computador.
        #
        # Em modo real:
        #   Executa o comando shutdown do Windows e desliga o PC.

        if MODO_TESTE:
            messagebox.showinfo(
                "Series Mode - teste",
                (
                    "Teste concluído.\n\n"
                    "Neste momento o computador seria desligado.\n\n"
                    "Como MODO_TESTE está True, nada será desligado."
                ),
            )
            self.resetar_contadores()
            self.root.after(1000, self.loop)
            return

        os.system("shutdown /s /t 0")

    def loop(self):
        # Coração do programa.
        #
        # Essa função roda a cada 1 segundo e decide o que fazer.
        #
        # Fluxo principal:
        #   1. Lê o pico de áudio.
        #   2. Verifica há quanto tempo o usuário não mexe no PC.
        #   3. Se houver áudio, mantém ou arma o monitoramento.
        #   4. Se não houver áudio e o programa estiver armado,
        #      começa a contar o tempo de silêncio.
        #   5. Se o tempo de silêncio atingir o limite,
        #      inicia o aviso final.
        #
        # Importante:
        #   O programa não conta silêncio antes de ser armado.
        #   Isso evita desligamento se você abrir o app antes de dar play na série.

        if self.aviso_ativo:
            return

        agora = time.monotonic()
        delta = agora - self.ultimo_tick
        self.ultimo_tick = agora

        # Se o monitoramento estiver pausado, não faz nenhuma verificação.
        if not self.ativo:
            self.info.config(text="")
            self.root.after(1000, self.loop)
            return

        pico = self.monitor_audio.pico_audio()
        tem_audio = pico >= LIMITE_AUDIO
        sem_interacao = tempo_sem_mouse_teclado()

        if tem_audio:
            # Enquanto há áudio, o programa:
            #   - acumula tempo de áudio detectado
            #   - zera qualquer contagem de silêncio
            self.audio_detectado_por += delta
            self.inicio_silencio = None

            # Depois de alguns segundos com áudio,
            # o programa considera que a série/vídeo realmente começou.
            if not self.armado and self.audio_detectado_por >= TEMPO_AUDIO_PARA_ARMAR:
                self.armado = True
                self.status.config(
                    text=(
                        "Áudio detectado. Monitoramento armado. "
                        "Quando o áudio parar, o contador começa."
                    )
                )
        else:
            # Se não há áudio, zeramos a contagem necessária para armar.
            self.audio_detectado_por = 0.0

            # Só contamos silêncio se:
            #   - o programa já foi armado
            #   - o usuário está sem mexer no mouse/teclado pelo tempo mínimo
            if self.armado and sem_interacao >= TEMPO_SEM_MOUSE_TECLADO:
                if self.inicio_silencio is None:
                    self.inicio_silencio = agora

                tempo_silencio = agora - self.inicio_silencio

                if tempo_silencio >= TEMPO_SEM_AUDIO_PARA_DESLIGAR:
                    self.iniciar_aviso()
                    return
            else:
                # Se o programa não está armado ou o usuário mexeu no PC,
                # não contamos silêncio.
                self.inicio_silencio = None

        tempo_silencio_atual = 0.0
        if self.inicio_silencio is not None:
            tempo_silencio_atual = agora - self.inicio_silencio

        # Define o texto de status que aparece na janela.
        if not self.armado:
            situacao = "Aguardando áudio para armar"
        elif tem_audio:
            situacao = "Áudio tocando"
        elif self.inicio_silencio is not None:
            situacao = "Sem áudio. Contando para desligar"
        else:
            situacao = "Sem áudio, mas aguardando inatividade"

        # Atualiza as informações exibidas na janela.
        self.info.config(
            text=(
                f"Status: {situacao}\n"
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {self.formatar_tempo(sem_interacao)}\n"
                f"Tempo sem áudio contado: {self.formatar_tempo(tempo_silencio_atual)}\n"
                f"Tempo configurado: {self.formatar_tempo(TEMPO_SEM_AUDIO_PARA_DESLIGAR)}\n"
                f"Armado: {self.armado}"
            )
        )

        # Agenda a próxima verificação para daqui a 1 segundo.
        self.root.after(1000, self.loop)

    def fechar(self):
        # Fecha o programa.
        #
        # Ao fechar, o monitoramento para completamente.
        # Nada fica rodando em segundo plano.
        self.root.destroy()


# =====================================================
# PONTO DE ENTRADA DO PROGRAMA
# =====================================================
# Esta parte só roda quando executamos:
#   uv run python main.py
#
# Ela cria a janela e inicia o aplicativo.


if __name__ == "__main__":
    root = tk.Tk()
    app = ModoSerieApp(root)
    root.mainloop()
