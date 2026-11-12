"""Tela de cadastro e consulta de Estudantes."""

import tkinter as tk

from tkinter import ttk



from interfaces import JanelaBase

from models.estudante import Estudante

from services.estudante_service import EstudanteService





class EstudanteInterface(JanelaBase):

    CAMPOS = [

        ("nome", "Nome completo", None),

        ("cpf", "CPF (somente números)", None),

        ("telefone", "Telefone (com DDD)", None),

        ("email", "E-mail", None),

        ("curso", "Curso", None),

        ("instituicao", "Instituição", None),

    ]

    COLUNAS = [

        ("id", "ID", 50), ("nome", "Nome", 220), ("cpf", "CPF", 120),

        ("telefone", "Telefone", 130), ("email", "E-mail", 200),

        ("curso", "Curso", 140), ("instituicao", "Instituição", 140),

    ]



    def __init__(self, master, usuario):

        super().__init__(master, usuario, "Estudantes")

        self.service = EstudanteService()

        self.busca = tk.StringVar()

        self._montar()

        self.carregar()



    def _montar(self):

        self.criar_formulario(self.corpo, self.CAMPOS).pack(fill="x")

        self.criar_botoes(self.corpo, [

            ("Cadastrar", self.cadastrar),

            ("Atualizar", self.atualizar),

            ("Excluir", self.excluir),

            ("Limpar", self.limpar_formulario),

        ]).pack(fill="x", pady=8)



        barra = ttk.Frame(self.corpo)

        barra.pack(fill="x")

        ttk.Label(barra, text="Buscar (nome, CPF, curso, instituição):").pack(side="left")

        entrada = ttk.Entry(barra, textvariable=self.busca, width=32)

        entrada.pack(side="left", padx=6)

        entrada.bind("<Return>", lambda _e: self.carregar())

        ttk.Button(barra, text="Buscar", command=self.carregar).pack(side="left")



        self.criar_tabela(self.corpo, self.COLUNAS).pack(fill="both", expand=True, pady=(8, 0))



    def carregar(self):

        def acao():

            estudantes = self.service.listar(self.busca.get())

            self.popular_tabela([

                (e.id, (e.id, e.nome, e.cpf_formatado(), e.telefone_formatado(),

                        e.email, e.curso, e.instituicao))

                for e in estudantes

            ])

        self.executar(acao)



    def ao_selecionar(self):

        identificador = self.id_selecionado()

        if identificador is None:

            return

        estudante = self.service.buscar_por_id(identificador)

        if estudante:

            self.definir_valores({

                "nome": estudante.nome, "cpf": estudante.cpf, "telefone": estudante.telefone,

                "email": estudante.email, "curso": estudante.curso,

                "instituicao": estudante.instituicao,

            })



    def cadastrar(self):

        dados = self.obter_dados()

        ok = self.executar(

            lambda: self.service.cadastrar(Estudante(**dados), self.usuario["id"]),

            "Estudante cadastrado com sucesso!")

        if ok:

            self.limpar_formulario()

            self.carregar()



    def atualizar(self):

        dados = self.obter_dados()



        def acao():

            identificador = self.exigir_selecao("um estudante")

            self.service.atualizar(Estudante(id=identificador, **dados), self.usuario["id"])



        if self.executar(acao, "Estudante atualizado com sucesso!"):

            self.carregar()



    def excluir(self):

        def acao():

            identificador = self.exigir_selecao("um estudante")

            if not self.confirmar("Deseja realmente excluir o estudante selecionado?"):

                return

            self.service.excluir(identificador, self.usuario["id"])

            self.limpar_formulario()

            self.carregar()



        self.executar(acao)