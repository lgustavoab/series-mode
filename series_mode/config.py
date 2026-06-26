import json
import sys
from pathlib import Path

from series_mode.constants import ACOES_VALIDAS


# =====================================================
# ARQUIVO DE CONFIGURAÇÃO
# =====================================================
# O config.json guarda as últimas configurações usadas.
#
# Quando o programa roda pelo Python, o arquivo fica na raiz do projeto.
#
# Quando o programa virar .exe, o arquivo ficará ao lado do executável.
# Isso evita que ele tente salvar configuração dentro de uma pasta temporária.


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


CONFIG_FILE = caminho_base_app() / "config.json"


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