import tkinter as tk
from tkinter import messagebox, ttk

from series_mode.constants import ACOES_VALIDAS
from series_mode.utils import formatar_valor_campo


# =====================================================
# INTERFACE GRÁFICA
# =====================================================
# Este arquivo concentra a parte visual do programa.
#
# A View não decide quando desligar, suspender ou hibernar.
# Ela apenas:
#   - cria os campos
#   - mostra os botões
#   - exibe mensagens
#   - lê os valores digitados
#   - atualiza os textos da tela
#
# A lógica principal fica no controller.py.


class SeriesModeView:
    def __init__(self, root: tk.Tk, controller, config_salva: dict):
        self.root = root
        self.controller = controller
        self.config_salva = config_salva

        self.root.title("Series Mode")
        self.root.geometry("760x680")
        self.root.minsize(760, 680)
        self.root.resizable(True, True)

        # Variáveis da interface.
        # Elas já começam preenchidas com os valores salvos no config.json.
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

        # Guarda os campos de configuração para bloquear/liberar
        # durante o monitoramento.
        self.campos_configuracao = []

        self.criar_interface()

    # =====================================================
    # CRIAÇÃO DA INTERFACE
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
        self.campos_configuracao.append(self.combo_acao)

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
        self.campos_configuracao.append(self.check_modo_teste)

        # Botões principais ficam antes do status.
        # Assim eles continuam visíveis depois que o monitoramento inicia.
        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(pady=(6, 8))

        self.botao_iniciar = ttk.Button(
            frame_botoes,
            text="Iniciar monitoramento",
            width=24,
            command=self.controller.iniciar_monitoramento,
        )
        self.botao_iniciar.grid(row=0, column=0, padx=6)

        self.botao_cancelar = ttk.Button(
            frame_botoes,
            text="Cancelar monitoramento",
            width=24,
            command=self.controller.cancelar_monitoramento,
            state="disabled",
        )
        self.botao_cancelar.grid(row=0, column=1, padx=6)

        self.botao_fechar = ttk.Button(
            frame_botoes,
            text="Fechar programa",
            width=20,
            command=self.controller.fechar,
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

        self.root.protocol("WM_DELETE_WINDOW", self.controller.fechar)

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

        # Guardamos o campo para conseguir bloquear/liberar depois.
        self.campos_configuracao.append(entrada)

        ttk.Label(frame, text=unidade).grid(
            row=linha,
            column=2,
            sticky="w",
            padx=4,
            pady=8,
        )

    # =====================================================
    # LEITURA DOS CAMPOS
    # =====================================================

    def obter_configuracoes_digitadas(self) -> dict:
        # Retorna os valores digitados na interface.
        #
        # A validação dos valores fica no controller.py.

        return {
            "tempo_sem_audio_minutos": self.var_tempo_audio.get(),
            "tempo_sem_interacao_minutos": self.var_tempo_interacao.get(),
            "aviso_segundos": self.var_tempo_aviso.get(),
            "modo_teste": self.var_modo_teste.get(),
            "acao_final": self.var_acao_final.get(),
        }

    # =====================================================
    # ATUALIZAÇÃO VISUAL
    # =====================================================

    def definir_campos_configuracao(self, habilitado: bool):
        # Bloqueia ou libera os campos de configuração.
        #
        # Enquanto o monitoramento está ativo, os campos ficam bloqueados
        # para evitar confusão entre o que aparece na tela e o que o programa
        # realmente está usando internamente.

        for campo in self.campos_configuracao:
            if isinstance(campo, ttk.Combobox):
                campo.config(state="readonly" if habilitado else "disabled")
            else:
                campo.config(state="normal" if habilitado else "disabled")

    def configurar_estado_monitoramento(self, monitorando: bool):
        # Atualiza botões e campos conforme o estado do monitoramento.

        if monitorando:
            self.botao_iniciar.config(state="disabled")
            self.botao_cancelar.config(state="normal")
            self.definir_campos_configuracao(False)
        else:
            self.botao_iniciar.config(state="normal")
            self.botao_cancelar.config(state="disabled")
            self.definir_campos_configuracao(True)

    def atualizar_status(self, texto: str):
        self.status.config(text=texto)

    def atualizar_info(self, texto: str):
        self.info.config(text=texto)

    def limpar_info(self):
        self.info.config(text="")

    def atualizar_observacao_modo(self, *, modo_teste: bool, acao_final: str):
        # Atualiza o texto inferior da janela, indicando se está em teste ou real.

        if modo_teste:
            self.observacao.config(
                text="MODO TESTE ATIVO: nenhuma ação real será executada.",
                fg="darkorange",
            )
        else:
            self.observacao.config(
                text=f"MODO REAL: ação final configurada para {acao_final}.",
                fg="red",
            )

    # =====================================================
    # MENSAGENS
    # =====================================================

    def mostrar_erro(self, titulo: str, mensagem: str):
        messagebox.showerror(titulo, mensagem)

    def mostrar_aviso(self, titulo: str, mensagem: str):
        messagebox.showwarning(titulo, mensagem)

    def mostrar_info(self, titulo: str, mensagem: str):
        messagebox.showinfo(titulo, mensagem)