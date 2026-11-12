"""Modelo de domínio: Despesa."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Despesa:
    CATEGORIAS_SUGERIDAS = ("Manutenção", "Limpeza", "Impostos", "Água/Energia", "Outros")

    kitnet_id: int
    descricao: str
    categoria: str
    valor: float
    data: str
    manutencao_id: Optional[int] = None
    id: Optional[int] = None

    def __post_init__(self):
        self.descricao = (self.descricao or "").strip()
        self.categoria = (self.categoria or "").strip()
        self.data = (self.data or "").strip()

    def validar(self):
        if not self.kitnet_id:
            raise ValueError("A despesa precisa estar vinculada a uma kitnet.")
        if not self.descricao:
            raise ValueError("Informe a descrição da despesa.")
        if not self.categoria:
            raise ValueError("Informe a categoria da despesa.")
        if not isinstance(self.valor, (int, float)) or self.valor <= 0:
            raise ValueError("O valor da despesa deve ser maior que zero.")
        try:
            datetime.strptime(self.data, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Data da despesa inválida. Use o formato AAAA-MM-DD.") from None

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))