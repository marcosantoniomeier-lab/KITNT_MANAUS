"""Tela de cadastro e consulta de Kitnets."""
import tkinter as tk
from tkinter import ttk

from interfaces import JanelaBase
from models.kitnet import Kitnet
from services import converter_inteiro, converter_valor, formatar_moeda
from services.kitnet_service import KitnetService


class KitnetInterface(JanelaBase):
    CAMPOS = [
        ("endereco", "Endereço", None),
        ("bairro", "Bairro", None),
        ("quartos", "Quartos", None),
        ("valor_aluguel", "Valor do aluguel (R$)", None),
        ("status", "Status", Kitnet.STATUS_VALIDOS),
    ]
    COLUNAS = [
        ("id", "ID", 50), ("endereco", "Endereço", 280), ("bairro", "Bairro", 150),
        ("quartos", "Quartos", 70), ("valor", "Aluguel", 110), ("status", "Status", 120),
    ]

    def __init__(self, master, usuario):
        super().__init__(master, usuario, "Kitnets")
        self.service = KitnetService()
        self.busca = tk.StringVar()
        self.filtro = tk.StringVar(value="Todos")
        self._montar()
        self.limpar()
        self.carregar()

    def _montar(self):
        self.criar_formulario(self.corpo, self.CAMPOS).pack(fill="x")
        self.criar_botoes(self.corpo, [
            ("Cadastrar", self.cadastrar),
            ("Atualizar", self.atualizar),
            ("Excluir", self.excluir),
            ("Limpar", self.limpar),
        ]).pack(fill="x", pady=8)

        barra = ttk.Frame(self.corpo)
        barra.pack(fill="x")
        ttk.Label(barra, text="Buscar (endereço/bairro):").pack(side="left")
        entrada = ttk.Entry(barra, textvariable=self.busca, width=28)
        entrada.pack(side="left", padx=6)
        entrada.bind("<Return>", lambda _e: self.carregar())
        ttk.Label(barra, text="Status:").pack(side="left", padx=(12, 4))
        combo = ttk.Combobox(barra, textvariable=self.filtro, state="readonly", width=16,
                             values=("Todos",) + Kitnet.STATUS_VALIDOS)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _e: self.carregar())
        ttk.Button(barra, text="Buscar", command=self.carregar).pack(side="left", padx=6)

        self.criar_tabela(self.corpo, self.COLUNAS).pack(fill="both", expand=True, pady=(8, 0))

    def limpar(self):
        self.limpar_formulario()
        self.definir_valores({"quartos": "1", "status": Kitnet.DISPONIVEL})

    def carregar(self):
        def acao():
            status = None if self.filtro.get() == "Todos" else self.filtro.get()
            kitnets = self.service.listar(status, self.busca.get())
            self.popular_tabela([
                (k.id, (k.id, k.endereco, k.bairro, k.quartos,
                        formatar_moeda(k.valor_aluguel), k.status))
                for k in kitnets
            ])
        self.executar(acao)

    def ao_selecionar(self):
        identificador = self.id_selecionado()
        if identificador is None:
            return
        kitnet = self.service.buscar_por_id(identificador)
        if kitnet:
            self.definir_valores({
                "endereco": kitnet.endereco, "bairro": kitnet.bairro,
                "quartos": kitnet.quartos,
                "valor_aluguel": f"{kitnet.valor_aluguel:.2f}".replace(".", ","),
                "status": kitnet.status,
            })

    def _montar_kitnet(self, identificador=None):
        d = self.obter_dados()
        return Kitnet(
            id=identificador,
            endereco=d["endereco"],
            bairro=d["bairro"],
            quartos=converter_inteiro(d["quartos"], "Quartos"),
            valor_aluguel=converter_valor(d["valor_aluguel"]),
            status=d["status"] or Kitnet.DISPONIVEL,
        )

    def cadastrar(self):
        ok = self.executar(
            lambda: self.service.cadastrar(self._montar_kitnet(), self.usuario["id"]),
            "Kitnet cadastrada com sucesso!")
        if ok:
            self.limpar()
            self.carregar()

    def atualizar(self):
        def acao():
            identificador = self.exigir_selecao("uma kitnet")
            self.service.atualizar(self._montar_kitnet(identificador), self.usuario["id"])

        if self.executar(acao, "Kitnet atualizada com sucesso!"):
            self.carregar()

    def excluir(self):
        def acao():
            identificador = self.exigir_selecao("uma kitnet")
            if not self.confirmar("Deseja realmente excluir a kitnet selecionada?"):
                return
            self.service.excluir(identificador, self.usuario["id"])
            self.limpar()
            self.carregar()

        self.executar(acao)