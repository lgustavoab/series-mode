import tkinter as tk

from series_mode.controller import SeriesModeController


# =====================================================
# PONTO DE ENTRADA DO PROGRAMA
# =====================================================
# O main.py apenas inicia a aplicação.
#
# A lógica principal fica em:
#   series_mode/controller.py
#
# A interface fica em:
#   series_mode/view.py
#
# Os serviços auxiliares ficam em:
#   series_mode/audio_monitor.py
#   series_mode/idle_monitor.py
#   series_mode/power_actions.py
#   series_mode/config.py


if __name__ == "__main__":
    root = tk.Tk()
    app = SeriesModeController(root)
    root.mainloop()