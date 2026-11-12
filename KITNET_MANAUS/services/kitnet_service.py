"""Regras de negócio de Kitnets."""
import sqlite3

from database.conexao import Conexao
from models.kitnet import Kitnet
from models.manutencao import Manutencao
from services import ErroNegocio
from services.usuario_service import HistoricoService


class KitnetService:
    def cadastrar(self, kitnet, usuario_id):
        kitnet.validar()
        if kitnet.status == Kitnet.ALUGADA:
            raise ErroNegocio("Uma kitnet só passa a 'Alugada' ao registrar uma locação.")
        try:
            with Conexao.transacao() as conn:
                cur = conn.execute(
                    """INSERT INTO kitnets (endereco, bairro, quartos, valor_aluguel, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (kitnet.endereco, kitnet.bairro, kitnet.quartos,
                     kitnet.valor_aluguel, kitnet.status),
                )
                novo_id = cur.lastrowid
                HistoricoService.registrar(
                    usuario_id, "CADASTRO_KITNET",
                    f"Kitnet #{novo_id} ({kitnet.endereco}) cadastrada.", conn)
        except sqlite3.IntegrityError as erro:
            raise ErroNegocio(self._traduzir_erro(erro)) from erro
        return novo_id

    def atualizar(self, kitnet, usuario_id):
        if not kitnet.id:
            raise ErroNegocio("Selecione uma kitnet para atualizar.")
        kitnet.validar()
        try:
            with Conexao.transacao() as conn:
                atual = conn.execute("SELECT status FROM kitnets WHERE id = ?", (kitnet.id,)).fetchone()
                if atual is None:
                    raise ErroNegocio("Kitnet não encontrada.")
                if kitnet.status != atual["status"]:
                    self._validar_mudanca_status(conn, kitnet.id, atual["status"], kitnet.status)
                conn.execute(
                    """UPDATE kitnets
                       SET endereco=?, bairro=?, quartos=?, valor_aluguel=?, status=?
                       WHERE id=?""",
                    (kitnet.endereco, kitnet.bairro, kitnet.quartos,
                     kitnet.valor_aluguel, kitnet.status, kitnet.id),
                )
                HistoricoService.registrar(
                    usuario_id, "ATUALIZACAO_KITNET",
                    f"Kitnet #{kitnet.id} ({kitnet.endereco}) atualizada. Status: {kitnet.status}.", conn)
        except sqlite3.IntegrityError as erro:
            raise ErroNegocio(self._traduzir_erro(erro)) from erro

    def excluir(self, kitnet_id, usuario_id):
        try:
            with Conexao.transacao() as conn:
                linha = conn.execute(
                    "SELECT endereco, status FROM kitnets WHERE id = ?", (kitnet_id,)).fetchone()
                if linha is None:
                    raise ErroNegocio("Kitnet não encontrada.")
                if linha["status"] == Kitnet.ALUGADA:
                    raise ErroNegocio("Não é possível excluir uma kitnet alugada.")
                conn.execute("DELETE FROM kitnets WHERE id = ?", (kitnet_id,))
                HistoricoService.registrar(
                    usuario_id, "EXCLUSAO_KITNET",
                    f"Kitnet #{kitnet_id} ({linha['endereco']}) excluída.", conn)
        except sqlite3.IntegrityError as erro:
            raise ErroNegocio(
                "Não é possível excluir: a kitnet possui locações, manutenções ou despesas vinculadas.") from erro

    def listar(self, status=None, busca=""):
        termo = f"%{busca.strip()}%"
        linhas = Conexao.consultar(
            """SELECT * FROM kitnets
               WHERE (? IS NULL OR status = ?) AND (endereco LIKE ? OR bairro LIKE ?)
               ORDER BY id""",
            (status, status, termo, termo),
        )
        return [Kitnet.from_row(l) for l in linhas]

    def listar_disponiveis(self):
        return self.listar(status=Kitnet.DISPONIVEL)

    def buscar_por_id(self, kitnet_id):
        linha = Conexao.consultar_um("SELECT * FROM kitnets WHERE id = ?", (kitnet_id,))
        return Kitnet.from_row(linha) if linha else None

    @staticmethod
    def _validar_mudanca_status(conn, kitnet_id, status_atual, novo_status):
        if status_atual == Kitnet.ALUGADA:
            raise ErroNegocio("Kitnet alugada: encerre ou cancele a locação para liberá-la.")
        if novo_status == Kitnet.ALUGADA:
            raise ErroNegocio("Uma kitnet só passa a 'Alugada' ao registrar uma locação.")
        if novo_status == Kitnet.DISPONIVEL:
            abertas = conn.execute(
                "SELECT COUNT(*) FROM manutencoes WHERE kitnet_id = ? AND status IN (?, ?)",
                (kitnet_id, *Manutencao.STATUS_ABERTOS),
            ).fetchone()[0]
            if abertas:
                raise ErroNegocio(
                    "Há manutenções abertas nesta kitnet. Conclua ou cancele-as antes de liberá-la.")

    @staticmethod
    def _traduzir_erro(erro):
        msg = str(erro)
        if "kitnets.endereco" in msg:
            return "Já existe uma kitnet com este endereço e bairro."
        return f"Não foi possível salvar a kitnet: {msg}"