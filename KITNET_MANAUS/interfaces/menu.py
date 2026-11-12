from interfaces.estilo import aplicar_estilo_minimalista
"""Tela de login e menu principal do KITNET MANAUS."""
import tkinter as tk
from tkinter import messagebox, ttk

from interfaces.estudante_interface import EstudanteInterface
from interfaces.kitnet_interface import KitnetInterface
from interfaces.locacao_interface import LocacaoInterface
from interfaces.manutencao_interface import ManutencaoInterface
from interfaces.pagamento_interface import PagamentoInterface
from interfaces.relatorio_interface import RelatorioInterface
from services import ErroNegocio
from services.usuario_service import UsuarioService


def _aplicar_tema():
    try:
        aplicar_estilo_minimalista(tk._default_root)
    except tk.TclError:
        pass


class LoginJanela(tk.Tk):
    """Janela de login. Ao autenticar, guarda o usuário em self.usuario e fecha."""

    def __init__(self):
        super().__init__()
        _aplicar_tema()
        self.title("KITNET MANAUS - Login")
        self.geometry("380x320")
        self.resizable(False, False)
        self.usuario = None
        self.var_login = tk.StringVar()
        self.var_senha = tk.StringVar()
        self._montar()
        self.bind("<Return>", lambda _e: self.entrar())

    def _montar(self):
        quadro = ttk.Frame(self, padding=25)
        quadro.pack(fill="both", expand=True)
        ttk.Label(quadro, text="KITNET MANAUS", font=("Segoe UI", 18, "bold")).pack(pady=(0, 4))
        ttk.Label(quadro, text="Sistema de gestão de kitnets para estudantes").pack(pady=(0, 18))

        ttk.Label(quadro, text="Login").pack(anchor="w")
        self.entrada_login = ttk.Entry(quadro, textvariable=self.var_login)
        self.entrada_login.pack(fill="x", pady=(0, 8))
        ttk.Label(quadro, text="Senha").pack(anchor="w")
        ttk.Entry(quadro, textvariable=self.var_senha, show="*").pack(fill="x", pady=(0, 14))

        ttk.Button(quadro, text="Entrar", command=self.entrar).pack(fill="x")
        ttk.Label(quadro, text="Primeiro acesso: admin / admin123", foreground="#757575").pack(pady=(14, 0))
        self.entrada_login.focus_set()

    def entrar(self):
        try:
            self.usuario = UsuarioService.autenticar(self.var_login.get(), self.var_senha.get())
        except ErroNegocio as erro:
            messagebox.showerror("Acesso negado", str(erro), parent=self)
            self.var_senha.set("")
            return
        self.destroy()


class MenuPrincipal(tk.Tk):
    MODULOS = [
        ("Estudantes", EstudanteInterface),
        ("Kitnets", KitnetInterface),
        ("Locações", LocacaoInterface),
        ("Pagamentos", PagamentoInterface),
        ("Manutenções", ManutencaoInterface),
        ("Relatórios", RelatorioInterface),
    ]

    def __init__(self, usuario):
        super().__init__()
        _aplicar_tema()
        self.usuario = usuario
        self.janelas = {}
        self.title("KITNET MANAUS - Menu Principal")
        self.geometry("560x420")
        self.minsize(480, 380)
        self._montar()

    def _montar(self):
        quadro = ttk.Frame(self, padding=20)
        quadro.pack(fill="both", expand=True)
        ttk.Label(quadro, text="KITNET MANAUS", font=("Segoe UI", 20, "bold")).pack()
        ttk.Label(
            quadro,
            text=f"Usuário: {self.usuario['nome']} ({self.usuario['perfil']})",
        ).pack(pady=(2, 16))

        grade = ttk.Frame(quadro)
        grade.pack(fill="both", expand=True)
        for coluna in range(2):
            grade.columnconfigure(coluna, weight=1)
        for indice, (nome, classe) in enumerate(self.MODULOS):
            linha, coluna = divmod(indice, 2)
            ttk.Button(
                grade, text=nome,
                command=lambda n=nome, c=classe: self.abrir_modulo(n, c),
            ).grid(row=linha, column=coluna, padx=8, pady=8, sticky="nsew", ipady=14)
            grade.rowconfigure(linha, weight=1)

        ttk.Button(quadro, text="Sair", command=self.sair).pack(fill="x", pady=(12, 0))

    def abrir_modulo(self, nome, classe):
        janela = self.janelas.get(nome)
        if janela is not None and janela.winfo_exists():
            janela.deiconify()
            janela.lift()
            janela.focus_force()
            return
        self.janelas[nome] = classe(self, self.usuario)

    def sair(self):
        if messagebox.askyesno("Sair", "Deseja encerrar o sistema?", parent=self):
            self.destroy()