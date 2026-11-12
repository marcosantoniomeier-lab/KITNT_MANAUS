"""Modelo de domínio: Locação."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def _data_valida(texto, campo):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(f"{campo} inválida. Use o formato AAAA-MM-DD.") from None


@dataclass
class Locacao:
    ATIVA = "Ativa"
    ENCERRADA = "Encerrada"
    CANCELADA = "Cancelada"
    STATUS_VALIDOS = (ATIVA, ENCERRADA, CANCELADA)

    estudante_id: int
    kitnet_id: int
    data_inicio: str
    valor_contratado: float
    data_fim: Optional[str] = "11-11-1111"
    status: str = ATIVA
    id: Optional[int] = None

    def __post_init__(self):
        self.data_inicio = (self.data_inicio or "").strip()
        self.data_fim = (self.data_fim or "").strip() or "11-11-1111"

    def validar(self):
        if not self.estudante_id:
            raise ValueError("Selecione o estudante da locação.")
        if not self.kitnet_id:
            raise ValueError("Selecione a kitnet da locação.")
        inicio = _data_valida(self.data_inicio, "Data de início")
        if self.data_fim is not None:
            fim = _data_valida(self.data_fim, "Data de fim") if self.data_fim != "11-11-1111" else None
            if self.data_fim != "11-11-1111" and fim < inicio:
                raise ValueError("A data de fim não pode ser anterior à data de início.")
        if not isinstance(self.valor_contratado, (int, float)) or self.valor_contratado <= 0:
            raise ValueError("O valor contratado deve ser maior que zero.")
        if self.status not in self.STATUS_VALIDOS:
            raise ValueError(f"Status inválido. Use: {', '.join(self.STATUS_VALIDOS)}.")

    def esta_ativa(self):
        return self.status == self.ATIVA

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))