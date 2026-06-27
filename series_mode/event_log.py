import json
import sys
from datetime import datetime
from pathlib import Path


# =====================================================
# REGISTRO DO ÚLTIMO EVENTO
# =====================================================
# Este arquivo cuida apenas do último evento relevante do programa.
#
# Ele não guarda histórico completo.
# Ele salva somente o último uso importante:
#   - aviso final iniciado
#   - ação cancelada
#   - ação simulada em modo teste
#   - ação real executada
#
# O objetivo é permitir que, ao abrir o programa no dia seguinte,
# o usuário veja quando o Series Mode chegou a agir ou tentou agir.


def caminho_base_app() -> Path:
    # Retorna a pasta base do aplicativo.
    #
    # Rodando como .exe:
    #   usa a pasta onde o executável está.
    #
    # Rodando como Python:
    #   usa a pasta raiz do projeto.

    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).resolve().parent.parent


LAST_EVENT_FILE = caminho_base_app() / "last_event.json"


def data_hora_atual_formatada() -> str:
    # Retorna data e hora em formato amigável para leitura.

    return datetime.now().strftime("%d/%m/%Y às %H:%M:%S")


def salvar_evento(
    *,
    status: str,
    acao_final: str,
    modo_teste: bool,
    mensagem: str,
) -> bool:
    # Salva o último evento relevante do programa.
    #
    # Retorna True se salvou corretamente.
    # Retorna False se houve algum erro ao salvar.

    evento = {
        "status": status,
        "acao_final": acao_final,
        "modo_teste": modo_teste,
        "data_hora": data_hora_atual_formatada(),
        "mensagem": mensagem,
    }

    try:
        with LAST_EVENT_FILE.open("w", encoding="utf-8") as file:
            json.dump(evento, file, ensure_ascii=False, indent=4)

        return True

    except OSError:
        return False


def carregar_ultimo_evento() -> dict | None:
    # Carrega o último evento salvo.
    #
    # Retorna None se o arquivo não existir ou estiver inválido.

    if not LAST_EVENT_FILE.exists():
        return None

    try:
        with LAST_EVENT_FILE.open("r", encoding="utf-8") as file:
            evento = json.load(file)

        if not isinstance(evento, dict):
            return None

        return evento

    except (OSError, json.JSONDecodeError):
        return None


def formatar_ultimo_evento(evento: dict | None) -> str:
    # Transforma o último evento em uma mensagem amigável para a interface.

    if not evento:
        return "Último evento: nenhum evento anterior registrado."

    status = evento.get("status", "")
    acao_final = evento.get("acao_final", "ação desconhecida")
    modo_teste = bool(evento.get("modo_teste", False))
    data_hora = evento.get("data_hora", "data/hora desconhecida")

    if status == "aviso_iniciado":
        return (
            f"Último evento: aviso final iniciado em {data_hora} "
            f"para {acao_final}."
        )

    if status == "acao_cancelada":
        return (
            f"Último evento: ação {acao_final} cancelada em {data_hora}."
        )

    if status == "acao_simulada":
        return (
            f"Último evento: ação {acao_final} simulada em modo teste "
            f"em {data_hora}."
        )

    if status == "acao_executada":
        return (
            f"Último evento: ação real {acao_final} executada em {data_hora}."
        )

    modo = "modo teste" if modo_teste else "modo real"

    return (
        f"Último evento: {acao_final} registrado em {data_hora} "
        f"({modo})."
    )