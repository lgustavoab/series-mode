import ctypes


# =====================================================
# DETECÇÃO DE INATIVIDADE DO WINDOWS
# =====================================================
# Esta parte usa funções do próprio Windows para descobrir
# há quanto tempo o usuário não mexe no mouse ou teclado.
#
# O programa usa essa informação como uma camada extra de segurança:
# ele só age se estiver sem áudio E sem interação do usuário.


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