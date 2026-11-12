"""Tela de Manutenções."""
import tkinter as tk
from tkinter import ttk

from interfaces import JanelaBase
from models.manutencao import Manutencao
from services import converter_valor, formatar_moeda
from services.kitnet_service import KitnetService
from services.manutencao_service import ManutencaoService


class ManutencaoInterface(JanelaBase):
    CAMPOS = [
        ("kitnet", "Kitnet", []),
        ("categoria", "Categoria", Manutencao.CATEGORIAS),
        ("descricao", "Descrição", None),
        ("custo", "Custo (R$)", None),
    ]
    COLUNAS = [
        ("id", "ID", 50), ("kitnet", "Kitnet", 230), ("descricao", "Descrição", 260),
        ("categoria", "Categoria", 110), ("custo", "Custo", 100), ("status", "Status", 100),
    ]

    def __init__(self, master, usuario):
        super().__init__(master, usuario, "Manutenções")
        self.service = ManutencaoService()
        self.filtro = tk.StringVar(value="Todos")
        self._montar()
        self.novo()

    def _montar(self):
        self.criar_formulario(self.corpo, self.CAMPOS).pack(fill="x")
        self.criar_botoes(self.corpo, [
            ("Abrir manutenção", self.abrir),
            ("Iniciar (selecionada)", self.iniciar),
            ("Concluir (selecionada)", self.concluir),
            ("Cancelar (selecionada)", self.cancelar),
            ("Novo / Atualizar", self.novo),
        ]).pack(fill="x", pady=8)

        barra = ttk.Frame(self.corpo)
        barra.pack(fill="x")
        ttk.Label(barra, text="Filtrar por status:").pack(side="left")
        combo = ttk.Combobox(barra, textvariable=self.filtro, state="readonly", width=16,
                             values=("Todos",) + Manutencao.STATUS_VALIDOS)
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.carregar())
        ttk.Label(
            barra,
            text="Dica: ao concluir, informe o custo final no campo 'Custo' (gera uma despesa).",
        ).pack(side="left", padx=12)

        self.criar_tabela(self.corpo, self.COLUNAS).pack(fill="both", expand=True, pady=(8, 0))
        self.tree.tag_configure("Concluída", foreground="#1b5e20")
        self.tree.tag_configure("Cancelada", foreground="#757575")

    def novo(self):
        self.limpar_formulario()
        self.carregar_opcoes()
        self.definir_valores({"custo": "0,00"})
        self.carregar()

    def carregar_opcoes(self):
        def acao():
            kitnets = KitnetService().listar()
            self.definir_opcoes("kitnet", [f"{k.id} - {k.endereco} [{k.status}]" for k in kitnets])
        self.executar(acao)

    def carregar(self):
        def acao():
            status = None if self.filtro.get() == "Todos" else self.filtro.get()
            linhas = self.service.listar(status)
            self.popular_tabela([
                (r["id"], (r["id"], r["kitnet"], r["descricao"], r["categoria"],
                           formatar_moeda(r["custo"]), r["status"]),
                 r["status"])
                for r in linhas
            ])
        self.executar(acao)

    def ao_selecionar(self):
        identificador = self.id_selecionado()
        if identificador is None:
            return
        m = self.service.buscar_por_id(identificador)
        if m:
            self.selecionar_opcao_por_id("kitnet", m.kitnet_id)
            self.definir_valores({
                "categoria": m.categoria, "descricao": m.descricao,
                "custo": f"{m.custo:.2f}".replace(".", ","),
            })

    def _custo(self):
        texto = self.obter_dados()["custo"]
        return converter_valor(texto) if texto else 0.0

    def abrir(self):
        d = self.obter_dados()

        def acao():
            manutencao = Manutencao(
                kitnet_id=self.extrair_id(d["kitnet"], "kitnet"),
                descricao=d["descricao"],
                categoria=d["categoria"],
                custo=self._custo(),
            )
            self.service.abrir(manutencao, self.usuario["id"])

        if self.executar(acao, "Manutenção aberta com sucesso!"):
            self.novo()

    def iniciar(self):
        def acao():
            self.service.iniciar(self.exigir_selecao("uma manutenção"), self.usuario["id"])

        if self.executar(acao, "Manutenção iniciada."):
            self.novo()

    def concluir(self):
        def acao():
            identificador = self.exigir_selecao("uma manutenção")
            self.service.concluir(identificador, self._custo(), self.usuario["id"])

        if self.executar(acao, "Manutenção concluída. A kitnet foi liberada, se não houver outras abertas."):
            self.novo()

    def cancelar(self):
        def acao():
            identificador = self.exigir_selecao("uma manutenção")
            if not self.confirmar(f"Cancelar a manutenção #{identificador}?"):
                return
            self.service.cancelar(identificador, self.usuario["id"])

        if self.executar(acao):
            self.novo()