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