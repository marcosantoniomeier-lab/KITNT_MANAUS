"""Modelo de domínio: Kitnet."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Kitnet:
    DISPONIVEL = "Disponível"
    ALUGADA = "Alugada"
    EM_MANUTENCAO = "Em manutenção"
    STATUS_VALIDOS = (DISPONIVEL, ALUGADA, EM_MANUTENCAO)

    endereco: str
    bairro: str
    quartos: int
    valor_aluguel: float
    status: str = DISPONIVEL
    id: Optional[int] = None

    def __post_init__(self):
        self.endereco = (self.endereco or "").strip()
        self.bairro = (self.bairro or "").strip()
        self.status = (self.status or self.DISPONIVEL).strip()

    def validar(self):
        if not self.endereco:
            raise ValueError("Informe o endereço da kitnet.")
        if not self.bairro:
            raise ValueError("Informe o bairro da kitnet.")
        if not isinstance(self.quartos, int) or self.quartos < 1:
            raise ValueError("A quantidade de quartos deve ser um inteiro maior ou igual a 1.")
        if not isinstance(self.valor_aluguel, (int, float)) or self.valor_aluguel <= 0:
            raise ValueError("O valor do aluguel deve ser maior que zero.")
        if self.status not in self.STATUS_VALIDOS:
            raise ValueError(f"Status inválido. Use: {', '.join(self.STATUS_VALIDOS)}.")

    def pode_ser_alugada(self):
        return self.status == self.DISPONIVEL

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))