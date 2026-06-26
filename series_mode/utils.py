def formatar_tempo(segundos: float) -> str:
    # Converte segundos em formato MM:SS.

    segundos = int(max(0, segundos))
    minutos = segundos // 60
    resto = segundos % 60
    return f"{minutos:02d}:{resto:02d}"


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