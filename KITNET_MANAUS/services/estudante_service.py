"""Regras de negócio de Estudantes."""
import sqlite3

from database.conexao import Conexao
from models.estudante import Estudante
from services import ErroNegocio
from services.usuario_service import HistoricoService


class EstudanteService:
    def cadastrar(self, estudante, usuario_id):
        estudante.validar()
        try:
            with Conexao.transacao() as conn:
                cur = conn.execute(
                    """INSERT INTO estudantes (nome, cpf, telefone, email, curso, instituicao)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (estudante.nome, estudante.cpf, estudante.telefone,
                     estudante.email, estudante.curso, estudante.instituicao),
                )
                novo_id = cur.lastrowid
                HistoricoService.registrar(
                    usuario_id, "CADASTRO_ESTUDANTE",
                    f"Estudante #{novo_id} ({estudante.nome}) cadastrado.", conn)
        except sqlite3.IntegrityError as erro:
            raise ErroNegocio(self._traduzir_erro(erro)) from erro
        return novo_id

    def atualizar(self, estudante, usuario_id):
        if not estudante.id:
            raise ErroNegocio("Selecione um estudante para atualizar.")
        estudante.validar()
        try:
            with Conexao.transacao() as conn:
                cur = conn.execute(
                    """UPDATE estudantes
                       SET nome=?, cpf=?, telefone=?, email=?, curso=?, instituicao=?
                       WHERE id=?""",
                    (estudante.nome, estudante.cpf, estudante.telefone, estudante.email,
                     estudante.curso, estudante.instituicao, estudante.id),
                )
                if cur.rowcount == 0:
                    raise ErroNegocio("Estudante não encontrado.")
                HistoricoService.registrar(
                    usuario_id, "ATUALIZACAO_ESTUDANTE",
                    f"Estudante #{estudante.id} ({estudante.nome}) atualizado.", conn)
        except sqlite3.IntegrityError as erro:
            raise ErroNegocio(self._traduzir_erro(erro)) from erro

    def excluir(self, estudante_id, usuario_id):
        try:
            with Conexao.transacao() as conn:
                linha = conn.execute("SELECT nome FROM estudantes WHERE id = ?", (estudante_id,)).fetchone()
                if linha is None:
                    raise ErroNegocio("Estudante não encontrado.")
                conn.execute("DELETE FROM estudantes WHERE id = ?", (estudante_id,))
                HistoricoService.registrar(
                    usuario_id, "EXCLUSAO_ESTUDANTE",
                    f"Estudante #{estudante_id} ({linha['nome']}) excluído.", conn)
        except sqlite3.IntegrityError as erro:
            raise ErroNegocio(
                "Não é possível excluir: o estudante possui locações registradas.") from erro

    def listar(self, busca=""):
        termo = f"%{busca.strip()}%"
        linhas = Conexao.consultar(
            """SELECT * FROM estudantes
               WHERE nome LIKE ? OR cpf LIKE ? OR curso LIKE ? OR instituicao LIKE ?
               ORDER BY nome""",
            (termo, termo, termo, termo),
        )
        return [Estudante.from_row(l) for l in linhas]

    def listar_sem_locacao_ativa(self):
        linhas = Conexao.consultar(
            """SELECT * FROM estudantes e
               WHERE NOT EXISTS (
                   SELECT 1 FROM locacoes l
                   WHERE l.estudante_id = e.id AND l.status = 'Ativa')
               ORDER BY e.nome""")
        return [Estudante.from_row(l) for l in linhas]

    def buscar_por_id(self, estudante_id):
        linha = Conexao.consultar_um("SELECT * FROM estudantes WHERE id = ?", (estudante_id,))
        return Estudante.from_row(linha) if linha else None

    def possui_locacao_ativa(self, estudante_id):
        linha = Conexao.consultar_um(
            "SELECT 1 FROM locacoes WHERE estudante_id = ? AND status = 'Ativa'", (estudante_id,))
        return linha is not None

    @staticmethod
    def _traduzir_erro(erro):
        msg = str(erro)
        if "estudantes.cpf" in msg:
            return "Já existe um estudante cadastrado com este CPF."
        if "estudantes.email" in msg:
            return "Já existe um estudante cadastrado com este e-mail."
        return f"Não foi possível salvar o estudante: {msg}"