"""Regras de negócio de Locações."""
import sqlite3
from datetime import date

from database.conexao import Conexao
from models.kitnet import Kitnet
from models.locacao import Locacao
from models.manutencao import Manutencao
from services import ErroNegocio
from services.usuario_service import HistoricoService


class LocacaoService:
    def criar(self, locacao, usuario_id):
        """Registra uma locação respeitando todas as regras de disponibilidade."""
        locacao.validar()
        try:
            with Conexao.transacao() as conn:
                estudante = conn.execute(
                    "SELECT id, nome FROM estudantes WHERE id = ?", (locacao.estudante_id,)).fetchone()
                if estudante is None:
                    raise ErroNegocio("Estudante não encontrado.")

                kitnet = conn.execute(
                    "SELECT id, endereco, status FROM kitnets WHERE id = ?", (locacao.kitnet_id,)).fetchone()
                if kitnet is None:
                    raise ErroNegocio("Kitnet não encontrada.")
                if kitnet["status"] == Kitnet.ALUGADA:
                    raise ErroNegocio("Esta kitnet já está alugada e não pode receber outra locação ativa.")
                if kitnet["status"] == Kitnet.EM_MANUTENCAO:
                    raise ErroNegocio("Esta kitnet está em manutenção e não pode ser alugada.")

                ativa = conn.execute(
                    "SELECT id FROM locacoes WHERE estudante_id = ? AND status = ?",
                    (locacao.estudante_id, Locacao.ATIVA)).fetchone()
                if ativa is not None:
                    raise ErroNegocio(
                        f"O estudante {estudante['nome']} já possui a locação ativa #{ativa['id']}.")

                cur = conn.execute(
                    """INSERT INTO locacoes
                       (estudante_id, kitnet_id, data_inicio, data_fim, valor_contratado, status)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (locacao.estudante_id, locacao.kitnet_id, locacao.data_inicio,
                     locacao.data_fim, locacao.valor_contratado, Locacao.ATIVA),
                )
                novo_id = cur.lastrowid
                conn.execute("UPDATE kitnets SET status = ? WHERE id = ?",
                             (Kitnet.ALUGADA, locacao.kitnet_id))
                HistoricoService.registrar(
                    usuario_id, "NOVA_LOCACAO",
                    f"Locação #{novo_id}: {estudante['nome']} -> {kitnet['endereco']}.", conn)
        except sqlite3.IntegrityError as erro:
            raise ErroNegocio(
                "Não foi possível registrar: a kitnet ou o estudante já possui locação ativa.") from erro
        return novo_id

    def encerrar(self, locacao_id, usuario_id):
        self._finalizar(locacao_id, Locacao.ENCERRADA, "ENCERRAMENTO_LOCACAO", usuario_id)

    def cancelar(self, locacao_id, usuario_id):
        self._finalizar(locacao_id, Locacao.CANCELADA, "CANCELAMENTO_LOCACAO", usuario_id)

    def _finalizar(self, locacao_id, novo_status, operacao, usuario_id):
        with Conexao.transacao() as conn:
            loc = conn.execute("SELECT * FROM locacoes WHERE id = ?", (locacao_id,)).fetchone()
            if loc is None:
                raise ErroNegocio("Locação não encontrada.")
            if loc["status"] != Locacao.ATIVA:
                raise ErroNegocio("Somente locações ativas podem ser encerradas ou canceladas.")

            data_fim = max(date.today().isoformat(), loc["data_inicio"])
            conn.execute("UPDATE locacoes SET status = ?, data_fim = ? WHERE id = ?",
                         (novo_status, data_fim, locacao_id))

            # A kitnet volta a ficar disponível, a menos que haja manutenção aberta.
            abertas = conn.execute(
                "SELECT COUNT(*) FROM manutencoes WHERE kitnet_id = ? AND status IN (?, ?)",
                (loc["kitnet_id"], *Manutencao.STATUS_ABERTOS)).fetchone()[0]
            status_kitnet = Kitnet.EM_MANUTENCAO if abertas else Kitnet.DISPONIVEL
            conn.execute("UPDATE kitnets SET status = ? WHERE id = ? AND status = ?",
                         (status_kitnet, loc["kitnet_id"], Kitnet.ALUGADA))
            HistoricoService.registrar(
                usuario_id, operacao,
                f"Locação #{locacao_id} ficou como '{novo_status}'. Kitnet #{loc['kitnet_id']} -> {status_kitnet}.",
                conn)

    def listar(self, status=None):
        return Conexao.consultar(
            """SELECT l.id, l.estudante_id, e.nome AS estudante,
                      l.kitnet_id, k.endereco AS kitnet,
                      l.data_inicio, l.data_fim, l.valor_contratado, l.status
               FROM locacoes l
               JOIN estudantes e ON e.id = l.estudante_id
               JOIN kitnets k ON k.id = l.kitnet_id
               WHERE (? IS NULL OR l.status = ?)
               ORDER BY l.id DESC""",
            (status, status),
        )

    def listar_ativas(self):
        return self.listar(Locacao.ATIVA)

    def buscar_por_id(self, locacao_id):
        linha = Conexao.consultar_um("SELECT * FROM locacoes WHERE id = ?", (locacao_id,))
        return Locacao.from_row(linha) if linha else None