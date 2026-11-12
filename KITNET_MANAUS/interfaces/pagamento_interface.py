"""Tela de Pagamentos."""
from datetime import date
import tkinter as tk
from tkinter import ttk

from interfaces import JanelaBase
from models.pagamento import Pagamento
from services import converter_inteiro, converter_valor, formatar_moeda
from services.locacao_service import LocacaoService
from services.pagamento_service import PagamentoService


class PagamentoInterface(JanelaBase):
    CAMPOS = [
        ("locacao", "Locação ativa", []),
        ("valor", "Valor da parcela (R$)", None),
        ("vencimento", "Vencimento (AAAA-MM-DD)", None),
        ("quantidade", "Qtde. de mensalidades", None),
        ("data_pagamento", "Data do pagamento (baixa)", None),
    ]
    COLUNAS = [
        ("id", "ID", 50), ("locacao", "Locação", 70), ("estudante", "Estudante", 190),
        ("kitnet", "Kitnet", 220), ("valor", "Valor", 100), ("vencimento", "Vencimento", 95),
        ("pagamento", "Pago em", 95), ("status", "Status", 80),
    ]

    def __init__(self, master, usuario):
        super().__init__(master, usuario, "Pagamentos")
        self.service = PagamentoService()
        self.locacoes = {}
        self.filtro = tk.StringVar(value="Todos")
        self._montar()
        self.novo()
        self.carregar()

    def _montar(self):
        self.criar_formulario(self.corpo, self.CAMPOS).pack(fill="x")
        self.widgets["locacao"].bind("<<ComboboxSelected>>", self._locacao_escolhida)
        self.criar_botoes(self.corpo, [
            ("Registrar parcela", self.registrar),
            ("Gerar mensalidades", self.gerar_mensalidades),
            ("Dar baixa (selecionado)", self.dar_baixa),
            ("Excluir (selecionado)", self.excluir),
            ("Novo / Atualizar", self.novo),
        ]).pack(fill="x", pady=8)

        barra = ttk.Frame(self.corpo)
        barra.pack(fill="x")
        ttk.Label(barra, text="Filtrar por status:").pack(side="left")
        combo = ttk.Combobox(barra, textvariable=self.filtro, state="readonly", width=14,
                             values=("Todos",) + Pagamento.STATUS_VALIDOS)
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.carregar())

        self.criar_tabela(self.corpo, self.COLUNAS).pack(fill="both", expand=True, pady=(8, 0))
        self.tree.tag_configure("Atrasado", foreground="#b00020")
        self.tree.tag_configure("Pago", foreground="#1b5e20")

    def novo(self):
        self.limpar_formulario()
        self.carregar_opcoes()
        hoje = date.today().isoformat()
        self.definir_valores({"vencimento": hoje, "quantidade": "6", "data_pagamento": hoje})
        self.carregar()

    def carregar_opcoes(self):
        def acao():
            self.locacoes = {r["id"]: r for r in LocacaoService().listar_ativas()}
            self.definir_opcoes("locacao", [
                f"{r['id']} - {r['estudante']} / {r['kitnet']}" for r in self.locacoes.values()])
        self.executar(acao)

    def _locacao_escolhida(self, _evento=None):
        try:
            loc = self.locacoes.get(self.extrair_id(self.vars["locacao"].get(), "locação"))
        except ValueError:
            return
        if loc:
            self.definir_valores({"valor": f"{loc['valor_contratado']:.2f}".replace(".", ",")})

    def carregar(self):
        def acao():
            status = None if self.filtro.get() == "Todos" else self.filtro.get()
            linhas = self.service.listar(status)
            self.popular_tabela([
                (r["id"], (r["id"], r["locacao_id"], r["estudante"], r["kitnet"],
                           formatar_moeda(r["valor"]), r["vencimento"],
                           r["data_pagamento"], r["status"]),
                 r["status"])
                for r in linhas
            ])
        self.executar(acao)

    def registrar(self):
        d = self.obter_dados()

        def acao():
            pagamento = Pagamento(
                locacao_id=self.extrair_id(d["locacao"], "locação"),
                valor=converter_valor(d["valor"]),
                vencimento=d["vencimento"],
            )
            self.service.registrar(pagamento, self.usuario["id"])

        if self.executar(acao, "Parcela registrada com sucesso!"):
            self.carregar()

    def gerar_mensalidades(self):
        d = self.obter_dados()
        resultado = {}

        def acao():
            resultado["qtd"] = self.service.gerar_mensalidades(
                self.extrair_id(d["locacao"], "locação"),
                converter_inteiro(d["quantidade"], "Quantidade de mensalidades"),
                d["vencimento"],
                self.usuario["id"])

        if self.executar(acao):
            self.carregar()
            self.executar(lambda: None, f"{resultado['qtd']} mensalidade(s) gerada(s) com sucesso!")

    def dar_baixa(self):
        data = self.obter_dados()["data_pagamento"]

        def acao():
            identificador = self.exigir_selecao("um pagamento")
            self.service.baixar(identificador, data, self.usuario["id"])

        if self.executar(acao, "Pagamento baixado com sucesso!"):
            self.carregar()

    def excluir(self):
        def acao():
            identificador = self.exigir_selecao("um pagamento")
            if not self.confirmar(f"Excluir o pagamento #{identificador}?"):
                return
            self.service.excluir(identificador, self.usuario["id"])
            self.carregar()

        self.executar(acao)