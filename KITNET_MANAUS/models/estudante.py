"""Modelo de domínio: Estudante."""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Estudante:
    nome: str
    cpf: str
    telefone: str
    email: str
    curso: str
    instituicao: str
    id: Optional[int] = None

    def __post_init__(self):
        self.nome = (self.nome or "").strip()
        self.cpf = re.sub(r"\D", "", self.cpf or "")
        self.telefone = re.sub(r"\D", "", self.telefone or "")
        self.email = (self.email or "").strip().lower()
        self.curso = (self.curso or "").strip()
        self.instituicao = (self.instituicao or "").strip()

    def validar(self):
        if not self.nome:
            raise ValueError("Informe o nome do estudante.")
        if len(self.cpf) != 11 or len(set(self.cpf)) == 1:
            raise ValueError("CPF inválido: informe 11 dígitos.")
        if len(self.telefone) not in (10, 11):
            raise ValueError("Telefone inválido: informe DDD + número (10 ou 11 dígitos).")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.email):
            raise ValueError("E-mail inválido.")
        if not self.curso:
            raise ValueError("Informe o curso do estudante.")
        if not self.instituicao:
            raise ValueError("Informe a instituição de ensino.")

    def cpf_formatado(self):
        c = self.cpf
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c) == 11 else c

    def telefone_formatado(self):
        t = self.telefone
        if len(t) == 11:
            return f"({t[:2]}) {t[2:7]}-{t[7:]}"
        if len(t) == 10:
            return f"({t[:2]}) {t[2:6]}-{t[6:]}"
        return t

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))