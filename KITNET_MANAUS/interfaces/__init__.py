"""Pacote de interfaces Tkinter do KITNET MANAUS.

Contém a classe base JanelaBase, que reúne utilitários de formulário, tabela
(Treeview) e tratamento padronizado de erros, reutilizada por todas as telas.
"""
import sqlite3
from tkinter import messagebox, ttk
import tkinter as tk

from services import ErroNegocio


class JanelaBase(tk.Toplevel):
    def __init__(self, master, usuario, titulo, geometria="1000x680"):
        super().__init__(master)
        self.usuario = usuario
        self.title(f"KITNET MANAUS - {titulo}")
        self.geometry(geometria)
        self.minsize(820, 520)
        self.vars = {}
        self.widgets = {}
        self.opcoes = {}
        self.tree = None
        self.corpo = ttk.Frame(self, padding=10)
        self.corpo.pack(fill="both", expand=True)

    # ---------------------------------------------------------- formulário
    def criar_formulario(self, pai, campos, colunas=2, titulo="Dados"):
        """campos: lista de (chave, rótulo, opções). opções=None => Entry; lista => Combobox."""
        quadro = ttk.LabelFrame(pai, text=titulo, padding=10)
        for indice, (chave, rotulo, opcoes) in enumerate(campos):
            linha, coluna = divmod(indice, colunas)
            ttk.Label(quadro, text=rotulo).grid(
                row=linha, column=coluna * 2, sticky="e", padx=(8, 4), pady=4)
            variavel = tk.StringVar()
            if opcoes is None:
                widget = ttk.Entry(quadro, textvariable=variavel, width=32)
            else:
                self.opcoes[chave] = list(opcoes)
                widget = ttk.Combobox(quadro, textvariable=variavel,
                                      values=self.opcoes[chave], state="readonly", width=30)
            widget.grid(row=linha, column=coluna * 2 + 1, sticky="w", padx=(0, 12), pady=4)
            self.vars[chave] = variavel
            self.widgets[chave] = widget
        return quadro

    def criar_botoes(self, pai, botoes):
        quadro = ttk.Frame(pai)
        for texto, comando in botoes:
            ttk.Button(quadro, text=texto, command=comando).pack(side="left", padx=(0, 6))
        return quadro

    def obter_dados(self):
        return {chave: var.get().strip() for chave, var in self.vars.items()}

    def definir_valores(self, valores):
        for chave, valor in valores.items():
            if chave in self.vars:
                self.vars[chave].set("" if valor is None else str(valor))

    def limpar_formulario(self):
        for var in self.vars.values():
            var.set("")
        if self.tree is not None and self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def definir_opcoes(self, chave, opcoes):
        self.opcoes[chave] = list(opcoes)
        self.widgets[chave]["values"] = self.opcoes[chave]
        if self.vars[chave].get() not in self.opcoes[chave]:
            self.vars[chave].set("")

    def selecionar_opcao_por_id(self, chave, identificador):
        prefixo = f"{identificador} - "
        for opcao in self.opcoes.get(chave, []):
            if opcao.startswith(prefixo):
                self.vars[chave].set(opcao)
                return
        self.vars[chave].set("")

    @staticmethod
    def extrair_id(texto, campo="item"):
        """'12 - Fulano' -> 12."""
        try:
            return int(str(texto).split(" - ")[0])
        except ValueError:
            raise ValueError(f"Selecione um(a) {campo} válido(a).") from None

    # -------------------------------------------------------------- tabela
    def criar_tabela(self, pai, colunas):
        """colunas: lista de (id, título, largura)."""
        quadro = ttk.Frame(pai)
        self.tree = ttk.Treeview(quadro, show="headings", selectmode="browse")
        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra.set)
        self.tree.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.configurar_colunas(colunas)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self.ao_selecionar())
        return quadro

    def configurar_colunas(self, colunas):
        self.tree["columns"] = [c[0] for c in colunas]
        for cid, titulo, largura in colunas:
            self.tree.heading(cid, text=titulo)
            self.tree.column(cid, width=largura, anchor="w", stretch=True)

    def popular_tabela(self, linhas):
        """linhas: lista de (iid, valores) ou (iid, valores, tag)."""
        self.tree.delete(*self.tree.get_children())
        for item in linhas:
            iid, valores = item[0], item[1]
            tag = item[2] if len(item) > 2 else ""
            valores = ["" if v is None else v for v in valores]
            self.tree.insert("", "end", iid=str(iid), values=valores, tags=(tag,) if tag else ())

    def id_selecionado(self):
        selecao = self.tree.selection()
        return int(selecao[0]) if selecao else None

    def exigir_selecao(self, entidade):
        identificador = self.id_selecionado()
        if identificador is None:
            raise ErroNegocio(f"Selecione {entidade} na tabela.")
        return identificador

    def ao_selecionar(self):
        """Sobrescrever nas telas para reagir à seleção de uma linha."""

    # ------------------------------------------------------------- mensagens
    def executar(self, acao, mensagem_sucesso=None):
        """Executa 'acao' tratando erros de negócio/banco. Retorna True se deu certo."""
        try:
            acao()
        except (ErroNegocio, ValueError) as erro:
            messagebox.showwarning("Atenção", str(erro), parent=self)
            return False
        except sqlite3.Error as erro:
            messagebox.showerror("Erro de banco de dados", str(erro), parent=self)
            return False
        if mensagem_sucesso:
            messagebox.showinfo("Sucesso", mensagem_sucesso, parent=self)
        return True

    def confirmar(self, mensagem):
        return messagebox.askyesno("Confirmação", mensagem, parent=self)