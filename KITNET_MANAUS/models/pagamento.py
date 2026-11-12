"""Modelo de domínio: Pagamento."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def _data_valida(texto, campo):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(f"{campo} inválida. Use o formato AAAA-MM-DD.") from None


@dataclass
class Pagamento:
    PENDENTE = "Pendente"
    PAGO = "Pago"
    ATRASADO = "Atrasado"
    STATUS_VALIDOS = (PENDENTE, PAGO, ATRASADO)

    locacao_id: int
    valor: float
    vencimento: str
    data_pagamento: Optional[str] = None
    status: str = PENDENTE
    id: Optional[int] = None

    def __post_init__(self):
        self.vencimento = (self.vencimento or "").strip()
        self.data_pagamento = (self.data_pagamento or "").strip() or None

    def validar(self):
        if not self.locacao_id:
            raise ValueError("Selecione a locação do pagamento.")
        if not isinstance(self.valor, (int, float)) or self.valor <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")
        _data_valida(self.vencimento, "Data de vencimento")
        if self.status not in self.STATUS_VALIDOS:
            raise ValueError(f"Status inválido. Use: {', '.join(self.STATUS_VALIDOS)}.")
        if self.status == self.PAGO:
            _data_valida(self.data_pagamento, "Data de pagamento")
        elif self.data_pagamento:
            raise ValueError("Somente pagamentos com status 'Pago' possuem data de pagamento.")

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))