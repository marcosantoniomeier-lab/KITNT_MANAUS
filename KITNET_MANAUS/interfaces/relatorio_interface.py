from tkinter import filedialog, messagebox
from services.exportacao_service import ExportacaoService
"""Tela de Relatórios."""
import tkinter as tk
from tkinter import ttk

from interfaces import JanelaBase
from services.relatorio_service import RelatorioService


class RelatorioInterface(JanelaBase):
    def __init__(self, master, usuario):
        super().__init__(master, usuario, "Relatórios", "1100x650")
        self.service = RelatorioService()
        self.catalogo = self.service.catalogo()
        self.escolhido = tk.StringVar(value=next(iter(self.catalogo)))
        self.total = tk.StringVar(value="")
        self._montar()
        self.gerar()

    def _montar(self):
        barra = ttk.Frame(self.corpo)
        barra.pack(fill="x")
        ttk.Label(barra, text="Relatório:").pack(side="left")
        combo = ttk.Combobox(barra, textvariable=self.escolhido, state="readonly",
                             width=32, values=list(self.catalogo))
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.gerar())
        ttk.Button(barra, text="Gerar / Atualizar", command=self.gerar).pack(side="left", padx=6)
        ttk.Button(barra, text="Pagamentos (.xlsx/.xls)", command=self.exportar_pagamentos).pack(side="left", padx=3)
        ttk.Button(barra, text="Alunos (.txt)", command=self.exportar_alunos).pack(side="left", padx=3)
        ttk.Button(barra, text="Kitnets (.json)", command=self.exportar_kitnets).pack(side="left", padx=3)
        ttk.Label(barra, textvariable=self.total).pack(side="right")

        self.criar_tabela(self.corpo, [("c0", "", 100)]).pack(fill="both", expand=True, pady=(10, 0))

    def gerar(self):
        def acao():
            colunas, linhas = self.catalogo[self.escolhido.get()]()
            self.configurar_colunas([(f"c{i}", nome, 150) for i, nome in enumerate(colunas)])
            self.popular_tabela([(i, linha) for i, linha in enumerate(linhas)])
            self.total.set(f"{len(linhas)} registro(s)")
        self.executar(acao)

    def exportar_pagamentos(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar Planilha de Pagamentos",
            defaultextension=".xlsx",
            initialfile="pagamentos_kitnet_manaus.xlsx",
            filetypes=[("Excel Moderno (*.xlsx)", "*.xlsx"), ("Excel 97-2003 (*.xls)", "*.xls")],
            parent=self,
        )
        if not caminho:
            return
        try:
            total = ExportacaoService.exportar_pagamentos_excel(caminho)
            messagebox.showinfo("Sucesso", f"{total} pagamentos exportados com sucesso!", parent=self)
        except Exception as erro:
            messagebox.showerror("Erro", str(erro), parent=self)

    def exportar_alunos(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar Lista de Alunos (TXT)",
            defaultextension=".txt",
            initialfile="alunos_cadastrados.txt",
            filetypes=[("Arquivo de Texto (*.txt)", "*.txt")],
            parent=self,
        )
        if not caminho:
            return
        try:
            total = ExportacaoService.exportar_estudantes_txt(caminho)
            messagebox.showinfo("Sucesso", f"{total} alunos exportados com sucesso!", parent=self)
        except Exception as erro:
            messagebox.showerror("Erro", str(erro), parent=self)

    def exportar_kitnets(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar Kitnets (JSON)",
            defaultextension=".json",
            initialfile="kitnets_cadastradas.json",
            filetypes=[("Arquivo JSON (*.json)", "*.json")],
            parent=self,
        )
        if not caminho:
            return
        try:
            total = ExportacaoService.exportar_kitnets_json(caminho)
            messagebox.showinfo("Sucesso", f"{total} kitnets exportadas com sucesso!", parent=self)
        except Exception as erro:
            messagebox.showerror("Erro", str(erro), parent=self)