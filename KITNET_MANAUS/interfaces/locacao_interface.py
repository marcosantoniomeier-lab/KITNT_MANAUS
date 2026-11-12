"""Tela de Locações."""
from datetime import date
import tkinter as tk
from tkinter import ttk

from interfaces import JanelaBase
from models.locacao import Locacao
from services import converter_valor, formatar_moeda
from services.estudante_service import EstudanteService
from services.kitnet_service import KitnetService
from services.locacao_service import LocacaoService


class LocacaoInterface(JanelaBase):
    CAMPOS = [
        ("estudante", "Estudante (sem locação ativa)", []),
        ("kitnet", "Kitnet disponível", []),
        ("data_inicio", "Início (AAAA-MM-DD)", None),
        ("data_fim", "Fim previsto (opcional)", None),
        ("valor_contratado", "Valor contratado (R$)", None),
    ]
    COLUNAS = [
        ("id", "ID", 50), ("estudante", "Estudante", 200), ("kitnet", "Kitnet", 240),
        ("inicio", "Início", 95), ("fim", "Fim", 95), ("valor", "Valor", 100),
        ("status", "Status", 90),
    ]

    def __init__(self, master, usuario):
        super().__init__(master, usuario, "Locações")
        self.service = LocacaoService()
        self.kitnets = {}
        self.filtro = tk.StringVar(value="Todos")
        self._montar()
        self.novo()
        self.carregar()

    def _montar(self):
        self.criar_formulario(self.corpo, self.CAMPOS).pack(fill="x")
        self.widgets["kitnet"].bind("<<ComboboxSelected>>", self._kitnet_escolhida)
        self.criar_botoes(self.corpo, [
            ("Registrar locação", self.registrar),
            ("Encerrar selecionada", self.encerrar),
            ("Cancelar selecionada", self.cancelar),
            ("Novo / Limpar", self.novo),
        ]).pack(fill="x", pady=8)

        barra = ttk.Frame(self.corpo)
        barra.pack(fill="x")
        ttk.Label(barra, text="Filtrar por status:").pack(side="left")
        combo = ttk.Combobox(barra, textvariable=self.filtro, state="readonly", width=14,
                             values=("Todos",) + Locacao.STATUS_VALIDOS)
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.carregar())

        self.criar_tabela(self.corpo, self.COLUNAS).pack(fill="both", expand=True, pady=(8, 0))
        self.tree.tag_configure("Ativa", foreground="#1b5e20")
        self.tree.tag_configure("Cancelada", foreground="#757575")

    def novo(self):
        self.limpar_formulario()
        self.carregar_opcoes()
        self.definir_valores({"data_inicio": date.today().isoformat()})

    def carregar_opcoes(self):
        def acao():
            estudantes = EstudanteService().listar_sem_locacao_ativa()
            self.kitnets = {k.id: k for k in KitnetService().listar_disponiveis()}
            self.definir_opcoes("estudante", [f"{e.id} - {e.nome}" for e in estudantes])
            self.definir_opcoes("kitnet", [f"{k.id} - {k.endereco} ({k.bairro})"
                                           for k in self.kitnets.values()])
        self.executar(acao)

    def _kitnet_escolhida(self, _evento=None):
        try:
            kitnet = self.kitnets.get(self.extrair_id(self.vars["kitnet"].get(), "kitnet"))
        except ValueError:
            return
        if kitnet:
            self.definir_valores({"valor_contratado": f"{kitnet.valor_aluguel:.2f}".replace(".", ",")})

    def carregar(self):
        def acao():
            status = None if self.filtro.get() == "Todos" else self.filtro.get()
            linhas = self.service.listar(status)
            self.popular_tabela([
                (r["id"], (r["id"], r["estudante"], r["kitnet"], r["data_inicio"],
                           r["data_fim"], formatar_moeda(r["valor_contratado"]), r["status"]),
                 r["status"])
                for r in linhas
            ])
        self.executar(acao)

    def registrar(self):
        d = self.obter_dados()

        def acao():
            locacao = Locacao(
                estudante_id=self.extrair_id(d["estudante"], "estudante"),
                kitnet_id=self.extrair_id(d["kitnet"], "kitnet"),
                data_inicio=d["data_inicio"],
                data_fim=d["data_fim"],
                valor_contratado=converter_valor(d["valor_contratado"]),
            )
            self.service.criar(locacao, self.usuario["id"])

        if self.executar(acao, "Locação registrada com sucesso!"):
            self.novo()
            self.carregar()

    def encerrar(self):
        def acao():
            identificador = self.exigir_selecao("uma locação")
            if not self.confirmar(f"Encerrar a locação #{identificador} e liberar a kitnet?"):
                return
            self.service.encerrar(identificador, self.usuario["id"])
            self.novo()
            self.carregar()

        self.executar(acao)

    def cancelar(self):
        def acao():
            identificador = self.exigir_selecao("uma locação")
            if not self.confirmar(f"Cancelar a locação #{identificador} e liberar a kitnet?"):
                return
            self.service.cancelar(identificador, self.usuario["id"])
            self.novo()
            self.carregar()

        self.executar(acao)