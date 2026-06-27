import time
import tkinter as tk

from series_mode.audio_monitor import MonitorAudio
from series_mode.config import carregar_configuracoes_salvas, salvar_configuracoes
from series_mode.constants import LIMITE_AUDIO, TEMPO_AUDIO_PARA_ARMAR
from series_mode.event_log import (
    carregar_ultimo_evento,
    formatar_ultimo_evento,
    salvar_evento,
)
from series_mode.idle_monitor import tempo_sem_mouse_teclado
from series_mode.power_actions import executar_acao_final
from series_mode.utils import formatar_tempo
from series_mode.view import SeriesModeView


# =====================================================
# CONTROLLER PRINCIPAL
# =====================================================
# Este arquivo é o cérebro do programa.
#
# Ele liga:
#   - View: interface gráfica
#   - Services: áudio, inatividade, ações de energia, config
#
# A interface não decide quando agir.
# O controller decide e apenas manda a view atualizar os textos.


class SeriesModeController:
    def __init__(self, root: tk.Tk):
        self.root = root

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

        # Carrega o último evento registrado em last_event.json.
        ultimo_evento = carregar_ultimo_evento()
        ultimo_evento_texto = formatar_ultimo_evento(ultimo_evento)

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

        # Cria a interface gráfica.
        self.view = SeriesModeView(
            root=self.root,
            controller=self,
            config_salva=self.config_salva,
            ultimo_evento_texto=ultimo_evento_texto,
        )

        # O loop fica rodando, mas só monitora quando self.ativo = True.
        self.loop()

    # =====================================================
    # REGISTRO DE EVENTOS
    # =====================================================

    def registrar_evento(
        self,
        *,
        status: str,
        mensagem: str,
    ):
        # Salva o último evento relevante e atualiza a interface.
        #
        # O arquivo last_event.json guarda somente o último evento.
        # Ele não cria histórico completo.

        salvou = salvar_evento(
            status=status,
            acao_final=self.acao_final,
            modo_teste=self.modo_teste,
            mensagem=mensagem,
        )

        if salvou:
            self.atualizar_ultimo_evento_na_interface()

    def atualizar_ultimo_evento_na_interface(self):
        # Recarrega o último evento salvo e mostra na interface.

        ultimo_evento = carregar_ultimo_evento()
        ultimo_evento_texto = formatar_ultimo_evento(ultimo_evento)
        self.view.atualizar_ultimo_evento(ultimo_evento_texto)

    # =====================================================
    # VALIDAÇÃO E CONTROLE
    # =====================================================

    def ler_configuracoes_da_interface(self) -> bool:
        # Lê, valida e salva os valores digitados na interface.
        #
        # Retorna True se estiver tudo correto.
        # Retorna False se algum campo estiver inválido.

        config_digitada = self.view.obter_configuracoes_digitadas()

        try:
            tempo_audio_min = float(
                str(config_digitada["tempo_sem_audio_minutos"]).replace(",", ".")
            )
            tempo_interacao_min = float(
                str(config_digitada["tempo_sem_interacao_minutos"]).replace(",", ".")
            )
            tempo_aviso_seg = int(
                float(str(config_digitada["aviso_segundos"]).replace(",", "."))
            )
        except ValueError:
            self.view.mostrar_erro(
                "Configuração inválida",
                "Preencha os tempos apenas com números.",
            )
            return False

        if tempo_audio_min <= 0:
            self.view.mostrar_erro(
                "Configuração inválida",
                "O tempo sem áudio precisa ser maior que zero.",
            )
            return False

        if tempo_interacao_min < 0:
            self.view.mostrar_erro(
                "Configuração inválida",
                "O tempo sem mouse/teclado não pode ser negativo.",
            )
            return False

        if tempo_aviso_seg <= 0:
            self.view.mostrar_erro(
                "Configuração inválida",
                "O aviso final precisa ser maior que zero.",
            )
            return False

        self.tempo_sem_audio_para_desligar = tempo_audio_min * 60
        self.tempo_sem_mouse_teclado = tempo_interacao_min * 60
        self.tempo_aviso_antes_desligar = tempo_aviso_seg
        self.modo_teste = bool(config_digitada["modo_teste"])
        self.acao_final = str(config_digitada["acao_final"])

        config_atual = {
            "tempo_sem_audio_minutos": tempo_audio_min,
            "tempo_sem_interacao_minutos": tempo_interacao_min,
            "aviso_segundos": tempo_aviso_seg,
            "modo_teste": self.modo_teste,
            "acao_final": self.acao_final,
        }

        salvou = salvar_configuracoes(config_atual)

        if not salvou:
            self.view.mostrar_aviso(
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

        self.view.configurar_estado_monitoramento(monitorando=True)

        self.view.atualizar_status(
            (
                "Monitoramento iniciado.\n"
                "Aguardando áudio inicial para armar o sistema."
            )
        )
        self.view.limpar_info()

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

        estava_em_aviso = self.aviso_ativo

        if estava_em_aviso:
            self.registrar_evento(
                status="acao_cancelada",
                mensagem="Ação cancelada manualmente pelo usuário durante o aviso final.",
            )

        self.ativo = False
        self.aviso_ativo = False
        self.resetar_contadores()

        self.view.configurar_estado_monitoramento(monitorando=False)

        self.view.atualizar_status(
            "Monitoramento cancelado. Clique em Iniciar monitoramento para ativar novamente."
        )

        self.view.limpar_info()
        self.atualizar_observacao_modo()

    def atualizar_observacao_modo(self):
        # Atualiza o texto inferior da janela, indicando se está em teste ou real.

        self.view.atualizar_observacao_modo(
            modo_teste=self.modo_teste,
            acao_final=self.acao_final,
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

        self.registrar_evento(
            status="aviso_iniciado",
            mensagem=(
                "Aviso final iniciado. A ação será executada se não houver "
                "áudio, interação ou cancelamento manual."
            ),
        )

        acao = self.acao_final.lower()

        self.view.atualizar_status(
            (
                f"Atenção: {acao} em breve.\n"
                "Mexa no mouse/teclado, volte o áudio ou clique em "
                "Cancelar monitoramento para cancelar."
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
            motivo = "houve cancelamento durante o aviso final."

            if pico >= LIMITE_AUDIO:
                motivo = "o áudio voltou durante o aviso final."
            elif sem_interacao < 3:
                motivo = "houve interação com mouse ou teclado durante o aviso final."
            elif not self.ativo:
                motivo = "o monitoramento foi interrompido durante o aviso final."

            self.registrar_evento(
                status="acao_cancelada",
                mensagem=f"Ação cancelada porque {motivo}",
            )

            self.view.atualizar_status("Ação cancelada. Monitoramento reiniciado.")
            self.resetar_contadores()
            self.root.after(1000, self.loop)
            return

        self.view.atualizar_info(
            (
                f"Ação final: {self.acao_final}\n"
                f"Executando/simulando em: {self.contagem_aviso} segundos\n"
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {formatar_tempo(sem_interacao)}\n"
                f"Modo: {self.texto_modo_atual()}"
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
            self.registrar_evento(
                status="acao_simulada",
                mensagem="Ação simulada em modo teste. Nenhuma ação real foi executada.",
            )

            self.view.mostrar_info(
                "Series Mode - teste",
                (
                    "Teste concluído.\n\n"
                    f"Neste momento a ação seria: {self.acao_final}.\n\n"
                    "Como o modo teste está ativado, nada foi executado."
                ),
            )

            self.ativo = False
            self.aviso_ativo = False
            self.resetar_contadores()

            self.view.configurar_estado_monitoramento(monitorando=False)

            self.view.atualizar_status(
                (
                    "Teste concluído. Ajuste as configurações ou clique em "
                    "Iniciar monitoramento novamente."
                )
            )
            self.view.limpar_info()
            self.atualizar_observacao_modo()

            self.root.after(1000, self.loop)
            return

        self.registrar_evento(
            status="acao_executada",
            mensagem="Ação real disparada pelo Series Mode.",
        )

        acao_executada = executar_acao_final(self.acao_final)

        if not acao_executada:
            self.view.mostrar_erro(
                "Ação inválida",
                f"Ação final desconhecida: {self.acao_final}",
            )

    # =====================================================
    # STATUS VISUAL
    # =====================================================

    def texto_modo_atual(self) -> str:
        # Retorna o modo atual em texto amigável para a interface.

        return "Teste" if self.modo_teste else "Real"

    def atualizar_status_monitoramento(
        self,
        *,
        tem_audio: bool,
        pico: float,
        sem_interacao: float,
        tempo_silencio_atual: float,
    ):
        # Atualiza a mensagem principal e os detalhes do status.
        #
        # A mensagem principal deve ser fácil de entender.
        # Os detalhes ficam abaixo para diagnóstico e acompanhamento.

        tempo_configurado = self.tempo_sem_audio_para_desligar
        tempo_restante = max(0, tempo_configurado - tempo_silencio_atual)

        if not self.armado:
            progresso_audio = min(
                self.audio_detectado_por,
                TEMPO_AUDIO_PARA_ARMAR,
            )

            mensagem_principal = (
                "Aguardando áudio inicial.\n"
                f"Dê play em um vídeo/música por pelo menos {TEMPO_AUDIO_PARA_ARMAR} "
                "segundos para armar o monitoramento."
            )

            detalhes = (
                f"Progresso para armar: {formatar_tempo(progresso_audio)} / "
                f"{formatar_tempo(TEMPO_AUDIO_PARA_ARMAR)}\n"
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {formatar_tempo(sem_interacao)}\n"
                f"Ação final: {self.acao_final}\n"
                f"Modo: {self.texto_modo_atual()}"
            )

        elif tem_audio:
            mensagem_principal = (
                "Monitoramento armado.\n"
                "Áudio detectado. Enquanto houver som, nenhuma contagem será iniciada."
            )

            detalhes = (
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {formatar_tempo(sem_interacao)}\n"
                "Tempo sem áudio: 00:00\n"
                f"Tempo configurado: {formatar_tempo(tempo_configurado)}\n"
                f"Ação final: {self.acao_final}\n"
                f"Modo: {self.texto_modo_atual()}"
            )

        elif self.inicio_silencio is not None:
            mensagem_principal = (
                "Sem áudio detectado.\n"
                f"Ação final em {formatar_tempo(tempo_restante)}, "
                "se o áudio não voltar e você não mexer no PC."
            )

            detalhes = (
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {formatar_tempo(sem_interacao)}\n"
                f"Tempo sem áudio: {formatar_tempo(tempo_silencio_atual)} / "
                f"{formatar_tempo(tempo_configurado)}\n"
                f"Ação final: {self.acao_final}\n"
                f"Modo: {self.texto_modo_atual()}"
            )

        else:
            mensagem_principal = (
                "Áudio parado, mas aguardando inatividade.\n"
                "Quando o PC ficar sem uso pelo tempo configurado, a contagem começa."
            )

            detalhes = (
                f"Pico de áudio: {pico:.5f}\n"
                f"Sem mouse/teclado: {formatar_tempo(sem_interacao)} / "
                f"{formatar_tempo(self.tempo_sem_mouse_teclado)}\n"
                "Tempo sem áudio: 00:00\n"
                f"Tempo configurado: {formatar_tempo(tempo_configurado)}\n"
                f"Ação final: {self.acao_final}\n"
                f"Modo: {self.texto_modo_atual()}"
            )

        self.view.atualizar_status(mensagem_principal)
        self.view.atualizar_info(detalhes)

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

        self.atualizar_status_monitoramento(
            tem_audio=tem_audio,
            pico=pico,
            sem_interacao=sem_interacao,
            tempo_silencio_atual=tempo_silencio_atual,
        )

        self.root.after(1000, self.loop)

    # =====================================================
    # FECHAMENTO
    # =====================================================

    def fechar(self):
        # Fecha o programa.
        #
        # Ao fechar, o monitoramento para completamente.
        # Nada fica rodando em segundo plano.

        self.root.destroy()