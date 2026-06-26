import os
import subprocess


# =====================================================
# AÇÕES DE ENERGIA DO WINDOWS
# =====================================================
# Este arquivo concentra as ações finais do programa.
#
# A interface e o controller não precisam saber o comando exato do Windows.
# Eles apenas chamam executar_acao_final("Desligar"), por exemplo.


def desligar() -> None:
    # Desliga o computador imediatamente.

    subprocess.run(["shutdown", "/s", "/t", "0"], check=False)


def hibernar() -> None:
    # Coloca o computador em hibernação.

    subprocess.run(["shutdown", "/h"], check=False)


def suspender() -> None:
    # Tenta suspender o computador.
    #
    # Observação:
    # Em alguns computadores, este comando pode hibernar em vez de suspender,
    # dependendo da configuração de energia do Windows.

    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


def executar_acao_final(acao_final: str) -> bool:
    # Executa a ação final escolhida.
    #
    # Retorna True se a ação foi reconhecida.
    # Retorna False se a ação for inválida.

    if acao_final == "Desligar":
        desligar()
        return True

    if acao_final == "Hibernar":
        hibernar()
        return True

    if acao_final == "Suspender":
        suspender()
        return True

    return False