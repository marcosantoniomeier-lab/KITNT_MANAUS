import tkinter as tk
from tkinter import ttk


def aplicar_estilo_minimalista(root: tk.Misc) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    BG_JANELA = "#F8FAFC"
    BG_CARD = "#FFFFFF"
    TEXTO = "#1E293B"
    TEXTO_SUAVE = "#64748B"
    BORDA = "#CBD5E1"
    PRIMARIA = "#0F172A"
    PRIMARIA_HOVER = "#334155"
    SECUNDARIA = "#E2E8F0"
    SECUNDARIA_HOVER = "#CBD5E1"

    root.configure(bg=BG_JANELA)

    fonte_padrao = ("Segoe UI", 9)
    fonte_negrito = ("Segoe UI", 9, "bold")
    fonte_titulo = ("Segoe UI", 10, "bold")

    style.configure(".", background=BG_JANELA, foreground=TEXTO, font=fonte_padrao)
    style.configure("TFrame", background=BG_JANELA)
    style.configure("TLabelframe", background=BG_JANELA, bordercolor=BORDA, relief="solid")
    style.configure("TLabelframe.Label", background=BG_JANELA, foreground=TEXTO_SUAVE, font=fonte_titulo)
    style.configure("TLabel", background=BG_JANELA, foreground=TEXTO)

    style.configure(
        "TButton",
        font=fonte_padrao,
        padding=(8, 3),
        background=SECUNDARIA,
        foreground=TEXTO,
        borderwidth=0,
        focusthickness=0,
    )
    style.map(
        "TButton",
        background=[("active", SECUNDARIA_HOVER), ("pressed", BORDA)],
    )

    style.configure(
        "Primario.TButton",
        font=fonte_negrito,
        padding=(10, 3),
        background=PRIMARIA,
        foreground="#FFFFFF",
        borderwidth=0,
    )
    style.map(
        "Primario.TButton",
        background=[("active", PRIMARIA_HOVER)],
    )

    style.configure(
        "TEntry",
        fieldbackground=BG_CARD,
        bordercolor=BORDA,
        lightcolor=BORDA,
        darkcolor=BORDA,
        padding=(5, 2),
    )
    style.configure(
        "TCombobox",
        fieldbackground=BG_CARD,
        bordercolor=BORDA,
        padding=(5, 2),
    )

    style.configure(
        "Treeview",
        background=BG_CARD,
        fieldbackground=BG_CARD,
        foreground=TEXTO,
        rowheight=22,
        bordercolor=BORDA,
        borderwidth=1,
        font=fonte_padrao,
    )
    style.configure(
        "Treeview.Heading",
        background="#F1F5F9",
        foreground=TEXTO,
        font=fonte_negrito,
        padding=(5, 3),
        borderwidth=0,
    )
    style.map("Treeview", background=[("selected", "#E0F2FE")], foreground=[("selected", "#0369A1")])