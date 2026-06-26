from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation


# =====================================================
# DETECÇÃO DE ÁUDIO DO DISPOSITIVO PADRÃO
# =====================================================
# Esta parte acessa o dispositivo padrão de saída de áudio do Windows.
#
# Quando você seleciona, por exemplo:
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