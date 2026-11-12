"""Camada de serviços (regras de negócio) do KITNET MANAUS.

Também concentra utilitários comuns usados por serviços e interfaces.
"""


class ErroNegocio(ValueError):
    """Violação de uma regra de negócio (mostrada ao usuário como aviso)."""


def formatar_moeda(valor):
    """1234.5 -> 'R$ 1.234,50'."""
    texto = f"{float(valor or 0):,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def converter_valor(texto):
    """Converte '1.200,50', '1200,50' ou '1200.50' para float."""
    t = str(texto or "").strip().replace("R$", "").replace(" ", "")
    if not t:
        raise ValueError("Informe um valor numérico.")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        raise ValueError(f"Valor inválido: '{texto}'. Use números, com vírgula nos centavos.") from None


def converter_inteiro(texto, campo="Valor"):
    try:
        return int(str(texto or "").strip())
    except ValueError:
        raise ValueError(f"{campo} deve ser um número inteiro.") from None