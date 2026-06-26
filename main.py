import ctypes
import json
import os
import subprocess
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation


# =====================================================
# CONFIGURAÇÕES INTERNAS
# =====================================================
# Estas configurações são valores internos do programa.
#
# As principais opções de uso ficam na interface:
#   - tempo sem áudio
#   - tempo sem mouse/teclado
#   - aviso final
#   - modo teste
#   - ação final


LIMITE_AUDIO = 0.003
# Sensibilidade usada para decidir se existe áudio tocando.
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
# Primeiro ele espera detectar áudio real por alguns segundos.


ACOES_VALIDAS = ("Desligar", "Suspender", "Hibernar")
# Ações finais permitidas na interface.


# =====================================================
# ARQUIVO DE CONFIGURAÇÃO
# =====================================================
# O config.json guarda as últimas configurações usadas.
#
# Ele fica na mesma pasta do main.py.
# Assim, quando o programa abre novamente, ele recupera:
#   - tempo sem áudio
#   - tempo sem mouse/teclado
#   - aviso final
#   - modo teste
#   - ação final


CONFIG_FILE = Path(__file__).with_name("config.json")


DEFAULT_CONFIG = {
    "tempo_sem_audio_minutos": 30,
    "tempo_sem_interacao_minutos": 5,
    "aviso_segundos": 60,
    "modo_teste": True,
    "acao_final": "Desligar",
}


def converter_numero_config(
    valor,
    padrao: float,
    *,
    permite_zero: bool,
) -> float:
    # Converte valores vindos do config.json para número.
    #
    # Se o arquivo estiver com valor inválido, usa o padrão.
    # Exemplo:
    #   "30" vira 30.0
    #   "2,5" vira 2.5
    #   "abc" volta para o padrão

    try:
        numero = float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return padrao

    if permite_zero:
        if numero < 0:
            return padrao
    else:
        if numero <= 0:
            return padrao

    return numero


def converter_bool_config(valor, padrao: bool) -> bool:
    # Converte o valor do modo teste vindo do config.json.
    #
    # Normalmente ele será True ou False.
    # Esta função também aceita strings como "true", "false", "sim" e "não".

    if isinstance(valor, bool):
        return valor

    if isinstance(valor, str):
        texto = valor.strip().lower()

        if texto in {"true", "1", "sim", "s", "yes", "y"}:
            return True

        if texto in {"false", "0", "nao", "não", "n", "no"}:
            return False

    return padrao


def formatar_valor_campo(valor) -> str:
    # Formata números para aparecerem de forma mais limpa na interface.
    #
    # Exemplo:
    #   30.0 aparece como "30"
    #   2.5 aparece como "2.5"

    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return str(valor)

    if numero.is_integer():
        return str(int(numero))

    return str(numero)


def normalizar_configuracoes(config: dict) -> dict:
    # Garante que as configurações carregadas sejam válidas.
    #
    # Isso evita erro se o config.json for editado manualmente
    # ou ficar com algum valor quebrado.

    tempo_sem_audio = converter_numero_config(
        config.get("tempo_sem_audio_minutos"),
        DEFAULT_CONFIG["tempo_sem_audio_minutos"],
        permite_zero=False,
    )

    tempo_sem_interacao = converter_numero_config(
        config.get("tempo_sem_interacao_minutos"),
        DEFAULT_CONFIG["tempo_sem_interacao_minutos"],
        permite_zero=True,
    )

    aviso_segundos = converter_numero_config(
        config.get("aviso_segundos"),
        DEFAULT_CONFIG["aviso_segundos"],
        permite_zero=False,
    )

    modo_teste = converter_bool_config(
        config.get("modo_teste"),
        DEFAULT_CONFIG["modo_teste"],
    )

    acao_final = str(config.get("acao_final", DEFAULT_CONFIG["acao_final"]))

    if acao_final not in ACOES_VALIDAS:
        acao_final = DEFAULT_CONFIG["acao_final"]

    return {
        "tempo_sem_audio_minutos": tempo_sem_audio,
        "tempo_sem_interacao_minutos": tempo_sem_interacao,
        "aviso_segundos": int(aviso_segundos),
        "modo_teste": modo_teste,
        "acao_final": acao_final,
    }


def carregar_configuracoes_salvas() -> dict:
    # Carrega as configurações salvas no config.json.
    #
    # Se o arquivo não existir, usa os valores padrão.
    # Se o arquivo estiver inválido/corrompido, também usa os valores padrão.
    #
    # O merge com DEFAULT_CONFIG garante que, se no futuro adicionarmos
    # novas opções, o programa continue funcionando mesmo com config antigo.

    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            config = json.load(file)

        if not isinstance(config, dict):
            return DEFAULT_CONFIG.copy()

        config_completa = {**DEFAULT_CONFIG, **config}
        return normalizar_configuracoes(config_completa)

    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()


def salvar_configuracoes(config: dict) -> bool:
    # Salva as configurações atuais no config.json.
    #
    # Retorna True se salvou corretamente.
    # Retorna False se houve algum erro de escrita.
    #
    # Usamos ensure_ascii=False para manter acentos legíveis.
    # Usamos indent=4 para o arquivo ficar fácil de ler e editar.

    try:
        config_normalizada = normalizar_configuracoes(config)

        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(config_normalizada, file, ensure_ascii=False, indent=4)

        return True

    except OSError:
        return False


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
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def tempo_sem_mouse_teclado() -> float:
    # Retorna há quantos segundos o usuário não mexe no mouse ou teclado.

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

        try:
            return float(self.meter.GetPeakValue())
        except Exception:
            return 0.0


# =====================================================
# APLICATIVO PRINCIPAL
# =====================================================


class ModoSerieApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Series Mode")
        self.root.geometry("760x680")
        self.root.minsize(760, 680)
        self.root.resizable(True, True)

        self.monitor_audio = MonitorAudio()

        # Estado do monitoramento.
        self.ativo = False
        self.armado = False
        self.audio_detectado_por = 0.0
        self.inicio_silencio = None
        self.ultimo_tick = time.monotonic()

        # Estado do aviso final.
        self.aviso_ativo = False
        self.contagem_aviso = 60

        # Carrega as configurações salvas no config.json.
        # Se o arquivo não existir, usa DEFAULT_CONFIG.
        self.config_salva = carregar_configuracoes_salvas()

        # Configurações que serão lidas da interface ao iniciar.
        self.tempo_sem_audio_para_desligar = (
            float(self.config_salva["tempo_sem_audio_minutos"]) * 60
        )
        self.tempo_sem_mouse_teclado = (
            float(self.config_salva["tempo_sem_interacao_minutos"]) * 60
        )
        self.tempo_aviso_antes_desligar = int(self.config_salva["aviso_segundos"])
        self.modo_teste = bool(self.config_salva["modo_teste"])
        self.acao_final = str(self.config_salva["acao_final"])

        # Variáveis da interface.
        # Elas já começam preenchidas com os valores salvos.
        self.var_tempo_audio = tk.StringVar(
            value=formatar_valor_campo(self.config_salva["tempo_sem_audio_minutos"])
        )
        self.var_tempo_interacao = tk.StringVar(
            value=formatar_valor_campo(
                self.config_salva["tempo_sem_interacao_minutos"]
            )
        )
        self.var_tempo_aviso = tk.StringVar(
            value=formatar_valor_campo(self.config_salva["aviso_segundos"])
        )
        self.var_modo_teste = tk.BooleanVar(
            value=bool(self.config_salva["modo_teste"])
        )
        self.var_acao_final = tk.StringVar(value=str(self.config_salva["acao_final"]))

        self.criar_interface()

        # O loop fica rodando, mas só monitora quando self.ativo = True.
        self.loop()

    # =====================================================
    # INTERFACE
    # =====================================================

    def criar_interface(self):
        self.titulo = tk.Label(
            self.root,
            text="Series Mode",
            font=("Segoe UI", 20, "bold"),
        )
        self.titulo.pack(pady=(16, 4))

        self.subtitulo = tk.Label(
            self.root,
            text="Desligamento automático após silêncio e inatividade",
            font=("Segoe UI", 10),
            fg="gray",
        )
        self.subtitulo.pack(pady=(0, 14))

        frame_config = ttk.LabelFrame(self.root, text="Configurações")
        frame_config.pack(padx=20, pady=8, fill="x")

        self.criar_linha_config(
            frame_config,
            linha=0,
            texto="Tempo sem áudio para agir:",
            variavel=self.var_tempo_audio,
            unidade="minutos",
        )

        self.criar_linha_config(
            frame_config,
            linha=1,
            texto="Tempo mínimo sem mouse/teclado:",
            variavel=self.var_tempo_interacao,
            unidade="minutos",
        )

        self.criar_linha_config(
            frame_config,
            linha=2,
            texto="Aviso final antes da ação:",
            variavel=self.var_tempo_aviso,
            unidade="segundos",
        )

        ttk.Label(frame_config, text="Ação final:").grid(
            row=3,
            column=0,
            sticky="w",
            padx=10,
            pady=8,
        )

        self.combo_acao = ttk.Combobox(
            frame_config,
            textvariable=self.var_acao_final,
            values=ACOES_VALIDAS,
            state="readonly",
            width=17,
        )
        self.combo_acao.grid(row=3, column=1, sticky="w", padx=8, pady=8)

        self.check_modo_teste = ttk.Checkbutton(
            frame_config,
            text="Modo teste: simular a ação sem desligar/suspender",
            variable=self.var_modo_teste,
        )
        self.check_modo_teste.grid(
            row=4,
            column=0,
            columnspan=3,
            sticky="w",
            padx=10,
            pady=(8, 12),
        )

        # Botões principais ficam antes do status.
        # Assim eles continuam visíveis depois que o monitoramento inicia.
        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(pady=(6, 8))

        self.botao_iniciar = ttk.Button(
            frame_botoes,
            text="Iniciar monitoramento",
            width=24,
            command=self.iniciar_monitoramento,
        )
        self.botao_iniciar.grid(row=0, column=0, padx=6)

        self.botao_cancelar = ttk.Button(
            frame_botoes,
            text="Cancelar monitoramento",
            width=24,
            command=self.cancelar_monitoramento,
            state="disabled",
        )
        self.botao_cancelar.grid(row=0, column=1, padx=6)

        self.botao_fechar = ttk.Button(
            frame_botoes,
            text="Fechar programa",
            width=20,
            command=self.fechar,
        )
        self.botao_fechar.grid(row=0, column=2, padx=6)

        frame_status = ttk.LabelFrame(self.root, text="Status")
        frame_status.pack(padx=20, pady=8, fill="x")

        self.status = tk.Label(
            frame_status,
            text="Parado. Configure e clique em Iniciar monitoramento.",
            font=("Segoe UI", 10),
            wraplength=680,
            justify="center",
        )
        self.status.pack(padx=12, pady=(10, 6))

        self.info = tk.Label(
            frame_status,
            text="",
            font=("Consolas", 10),
            justify="left",
            anchor="w",
        )
        self.info.pack(padx=12, pady=(4, 10))

        self.observacao = tk.Label(
            self.root,
            text="Dica: use modo teste antes de usar a ação real.",
            font=("Segoe UI", 9, "bold"),
            fg="darkorange",
        )
        self.observacao.pack(pady=(4, 12))

        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

    def criar_linha_config(
        self,
        frame: ttk.LabelFrame,
        linha: int,
        texto: str,
        variavel: tk.StringVar,
        unidade: str,
    ):
        ttk.Label(frame, text=texto).grid(
            row=linha,
            column=0,
            sticky="w",
            padx=10,
            pady=8,
        )

        entrada = ttk.Entry(
            frame,
            textvariable=variavel,
            width=10,
        )
        entrada.grid(row=linha, column=1, sticky="w", padx=8, pady=8)

        ttk.Label(frame, text=unidade).grid(
            row=linha,
            column=2,
            sticky="w",
            padx=4,
            pady=8,
        )

    # =====================================================
    # VALIDAÇÃO E CONTROLE
    # =====================================================

    def ler_configuracoes_da_interface(self) -> bool:
        # Lê, valida e salva os valores digitados na interface.
        #
        # Retorna True se estiver tudo correto.
        # Retorna False se algum campo estiver inválido.

        try:
            tempo_audio_min = float(self.var_tempo_audio.get().replace(",", "."))
            tempo_interacao_min = float(self.var_tempo_interacao.get().replace(",", "."))
            tempo_aviso_seg = int(float(self.var_tempo_aviso.get().replace(",", ".")))
        except ValueError:
            messagebox.showerror(
                "Configuração inválida",
                "Preencha os tempos apenas com números.",
            )
            return False

        if tempo_audio_min <= 0:
            messagebox.showerror(
                "Configuração inválida",
                "O tempo sem áudio precisa ser maior que zero.",
            )
            return False

        if tempo_interacao_min < 0:
            messagebox.showerror(
                "Configuração inválida",
                "O tempo sem mouse/teclado não pode ser negativo.",
            )
            return False

        if tempo_aviso_seg <= 0:
            messagebox.showerror(
                "Configuração inválida",
                "O aviso final precisa ser maior que zero.",
            )
            return False

        self.tempo_sem_audio_para_desligar = tempo_audio_min * 60
        self.tempo_sem_mouse_teclado = tempo_interacao_min * 60
        self.tempo_aviso_antes_desligar = tempo_aviso_seg
        self.modo_teste = self.var_modo_teste.get()
        self.acao_final = self.var_acao_final.get()

        config_atual = {
            "tempo_sem_audio_minutos": tempo_audio_min,
            "tempo_sem_interacao_minutos": tempo_interacao_min,
            "aviso_segundos": tempo_aviso_seg,
            "modo_teste": self.modo_teste,
            "acao_final": self.acao_final,
        }

        salvou = salvar_configuracoes(config_atual)

        if not salvou:
            messagebox.showwarning(
                "Configuração não salva",
                (
                    "O monitoramento será iniciado, mas não foi possível "
                    "salvar as configurações no config.json."
                ),
            )

        return True

    def iniciar_monitoramento(self):
        # Inicia o monitoramento com as configurações atuais da interface.
        #
        # O programa ainda não começa contando silêncio imediatamente.
        # Primeiro ele espera detectar áudio por TEMPO_AUDIO_PARA_ARMAR segundos.

        if not self.ler_configuracoes_da_interface():
            return

        self.ativo = True
        self.resetar_contadores()

        self.botao_iniciar.config(state="disabled")
        self.botao_cancelar.config(state="normal")

        self.status.config(
            text=(
                "Monitoramento iniciado. "
                "Aguardando áudio para armar o sistema..."
            )
        )

        self.atualizar_observacao_modo()

    def cancelar_monitoramento(self):
        # Cancela o monitoramento atual.
        #
        # Pode ser usado em qualquer momento:
        #   - aguardando áudio
        #   - monitoramento armado
        #   - contando silêncio
        #   - aviso final
        #
        # Depois de cancelar, o programa volta ao estado inicial
        # e só monitora novamente se o usuário clicar em Iniciar.

        self.ativo = False
        self.aviso_ativo = False
        self.resetar_contadores()

        self.botao_iniciar.config(state="normal")
        self.botao_cancelar.config(state="disabled")

        self.status.config(
            text="Monitoramento cancelado. Clique em Iniciar monitoramento para ativar novamente."
        )

        self.info.config(text="")
        self.atualizar_observacao_modo()

    def atualizar_observacao_modo(self):
        # Atualiza o texto inferior da janela, indicando se está em teste ou real.

        if self.modo_teste:
            self.observacao.config(
                text="MODO TESTE ATIVO: nenhuma ação real será executada.",
                fg="darkorange",
            )
        else:
            self.observacao.config(
                text=f"MODO REAL: ação final configurada para {self.acao_final}.",
                fg="red",
            )

    def resetar_contadores(self):
        # Zera todos os estados temporários do monitoramento.

        self.armado = False
        self.audio_detectado_por = 0.0
        self.inicio_silencio = None
        self.aviso_ativo = False
        self.contagem_aviso = self.tempo_aviso_antes_desligar
        self.ultimo_tick = time.monotonic()

    # =====================================================
    # LÓGICA DE AVISO E AÇÃO FINAL
    # =====================================================

    def iniciar_aviso(self):
        # Inicia o aviso final antes da ação.
        #
        # Durante esse aviso, a ação será cancelada se:
        #   - voltar áudio
        #   - o usuário mexer no mouse/teclado
        #   - o monitoramento for cancelado

        self.aviso_ativo = True
        self.contagem_aviso = self.tempo_aviso_antes_desligar

        acao = self.acao_final.lower()

        self.status.config(
            text=(
                f"O PC será colocado em ação de '{acao}' em breve. "
                "Mexa no mouse/teclado ou clique em Cancelar monitoramento para cancelar."
            )
        )

        self.contagem_regressiva()

    def contagem_regressiva(self):
        # Controla a contagem regressiva do aviso final.

        if not self.aviso_ativo:
            return

        pico = self.monitor_audio.pico_audio()
        sem_interacao = tempo_sem_mouse_teclado()

        if pico >= LIMITE_AUDIO or sem_interacao < 3 or not self.ativo:
            self.status.config(text="Ação cancelada. Monitoramento reiniciado.")
            self.resetar_contadores()
            self.root.after(1000, self.loop)
            return

        self.info.config(
            text=(
                f"Ação final: {self.acao_final}\n"
                f"Executando/simulando em: {self.contagem_aviso} segundos\n"
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {self.formatar_tempo(sem_interacao)}\n"
                f"Modo teste: {self.modo_teste}"
            )
        )

        if self.contagem_aviso <= 0:
            self.executar_acao_final()
            return

        self.contagem_aviso -= 1
        self.root.after(1000, self.contagem_regressiva)

    def executar_acao_final(self):
        # Executa a ação final configurada.
        #
        # Em modo teste:
        #   Apenas mostra uma mensagem.
        #
        # Em modo real:
        #   Executa a ação escolhida na interface.

        if self.modo_teste:
            messagebox.showinfo(
                "Series Mode - teste",
                (
                    "Teste concluído.\n\n"
                    f"Neste momento a ação seria: {self.acao_final}.\n\n"
                    "Como o modo teste está ativado, nada foi executado."
                ),
            )
            self.resetar_contadores()
            self.root.after(1000, self.loop)
            return

        if self.acao_final == "Desligar":
            subprocess.run(["shutdown", "/s", "/t", "0"], check=False)
            return

        if self.acao_final == "Hibernar":
            subprocess.run(["shutdown", "/h"], check=False)
            return

        if self.acao_final == "Suspender":
            # Observação:
            # Em alguns computadores, este comando pode hibernar em vez de suspender,
            # dependendo da configuração de energia do Windows.
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return

        messagebox.showerror(
            "Ação inválida",
            f"Ação final desconhecida: {self.acao_final}",
        )

    # =====================================================
    # LOOP PRINCIPAL
    # =====================================================

    def loop(self):
        # Coração do programa.
        #
        # Essa função roda a cada 1 segundo e decide o que fazer.
        #
        # Fluxo principal:
        #   1. Se o monitoramento estiver pausado/cancelado, não faz nada.
        #   2. Lê o pico de áudio.
        #   3. Verifica há quanto tempo o usuário não mexe no PC.
        #   4. Se houver áudio, arma o monitoramento após alguns segundos.
        #   5. Se não houver áudio e o programa estiver armado,
        #      começa a contar o tempo de silêncio.
        #   6. Se o tempo de silêncio atingir o limite,
        #      inicia o aviso final.

        if self.aviso_ativo:
            return

        agora = time.monotonic()
        delta = agora - self.ultimo_tick
        self.ultimo_tick = agora

        if not self.ativo:
            self.root.after(1000, self.loop)
            return

        pico = self.monitor_audio.pico_audio()
        tem_audio = pico >= LIMITE_AUDIO
        sem_interacao = tempo_sem_mouse_teclado()

        if tem_audio:
            self.audio_detectado_por += delta
            self.inicio_silencio = None

            if not self.armado and self.audio_detectado_por >= TEMPO_AUDIO_PARA_ARMAR:
                self.armado = True
                self.status.config(
                    text=(
                        "Áudio detectado. Monitoramento armado. "
                        "Quando o áudio parar, o contador começa."
                    )
                )
        else:
            self.audio_detectado_por = 0.0

            if self.armado and sem_interacao >= self.tempo_sem_mouse_teclado:
                if self.inicio_silencio is None:
                    self.inicio_silencio = agora

                tempo_silencio = agora - self.inicio_silencio

                if tempo_silencio >= self.tempo_sem_audio_para_desligar:
                    self.iniciar_aviso()
                    return
            else:
                self.inicio_silencio = None

        tempo_silencio_atual = 0.0
        if self.inicio_silencio is not None:
            tempo_silencio_atual = agora - self.inicio_silencio

        if not self.armado:
            situacao = "Aguardando áudio para armar"
        elif tem_audio:
            situacao = "Áudio tocando"
        elif self.inicio_silencio is not None:
            situacao = "Sem áudio. Contando para ação final"
        else:
            situacao = "Sem áudio, mas aguardando inatividade"

        self.info.config(
            text=(
                f"Status: {situacao}\n"
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {self.formatar_tempo(sem_interacao)}\n"
                f"Tempo sem áudio contado: {self.formatar_tempo(tempo_silencio_atual)}\n"
                f"Tempo configurado: {self.formatar_tempo(self.tempo_sem_audio_para_desligar)}\n"
                f"Ação final: {self.acao_final}\n"
                f"Modo teste: {self.modo_teste}\n"
                f"Armado: {self.armado}"
            )
        )

        self.root.after(1000, self.loop)

    # =====================================================
    # UTILITÁRIOS
    # =====================================================

    def formatar_tempo(self, segundos: float) -> str:
        # Converte segundos em formato MM:SS.

        segundos = int(max(0, segundos))
        minutos = segundos // 60
        resto = segundos % 60
        return f"{minutos:02d}:{resto:02d}"

    def fechar(self):
        # Fecha o programa.
        #
        # Ao fechar, o monitoramento para completamente.
        # Nada fica rodando em segundo plano.

        self.root.destroy()


# =====================================================
# PONTO DE ENTRADA DO PROGRAMA
# =====================================================


if __name__ == "__main__":
    root = tk.Tk()
    app = ModoSerieApp(root)
    root.mainloop()
