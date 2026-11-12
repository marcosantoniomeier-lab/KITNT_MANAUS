"""Regras de negócio de Manutenções (e geração automática de despesas)."""
from datetime import date

from database.conexao import Conexao
from models.despesa import Despesa
from models.kitnet import Kitnet
from models.manutencao import Manutencao
from services import ErroNegocio
from services.usuario_service import HistoricoService


class ManutencaoService:
    def abrir(self, manutencao, usuario_id):
        manutencao.status = Manutencao.ABERTA
        manutencao.validar()
        with Conexao.transacao() as conn:
            kitnet = conn.execute("SELECT id, endereco, status FROM kitnets WHERE id = ?",
                                  (manutencao.kitnet_id,)).fetchone()
            if kitnet is None:
                raise ErroNegocio("Kitnet não encontrada.")
            cur = conn.execute(
                """INSERT INTO manutencoes (kitnet_id, descricao, categoria, custo, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (manutencao.kitnet_id, manutencao.descricao, manutencao.categoria,
                 manutencao.custo, Manutencao.ABERTA))
            novo_id = cur.lastrowid
            # Kitnet disponível passa a 'Em manutenção'. Kitnet alugada mantém o status.
            if kitnet["status"] == Kitnet.DISPONIVEL:
                conn.execute("UPDATE kitnets SET status = ? WHERE id = ?",
                             (Kitnet.EM_MANUTENCAO, manutencao.kitnet_id))
            HistoricoService.registrar(
                usuario_id, "ABERTURA_MANUTENCAO",
                f"Manutenção #{novo_id} aberta na kitnet #{kitnet['id']} ({kitnet['endereco']}).", conn)
        return novo_id

    def iniciar(self, manutencao_id, usuario_id):
        with Conexao.transacao() as conn:
            atual = self._buscar(conn, manutencao_id)
            if atual["status"] != Manutencao.ABERTA:
                raise ErroNegocio("Somente manutenções 'Aberta' podem ser iniciadas.")
            conn.execute("UPDATE manutencoes SET status = ? WHERE id = ?",
                         (Manutencao.EM_ANDAMENTO, manutencao_id))
            HistoricoService.registrar(
                usuario_id, "INICIO_MANUTENCAO", f"Manutenção #{manutencao_id} em andamento.", conn)

    def concluir(self, manutencao_id, custo, usuario_id):
        if custo < 0:
            raise ErroNegocio("O custo não pode ser negativo.")
        with Conexao.transacao() as conn:
            atual = self._buscar(conn, manutencao_id)
            if atual["status"] not in Manutencao.STATUS_ABERTOS:
                raise ErroNegocio("Esta manutenção já foi concluída ou cancelada.")
            conn.execute("UPDATE manutencoes SET status = ?, custo = ? WHERE id = ?",
                         (Manutencao.CONCLUIDA, custo, manutencao_id))
            if custo > 0:
                despesa = Despesa(
                    kitnet_id=atual["kitnet_id"],
                    descricao=f"Manutenção #{manutencao_id}: {atual['descricao']}",
                    categoria=atual["categoria"],
                    valor=custo,
                    data=date.today().isoformat(),
                    manutencao_id=manutencao_id)
                despesa.validar()
                conn.execute(
                    """INSERT INTO despesas (kitnet_id, manutencao_id, descricao, categoria, valor, data)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (despesa.kitnet_id, despesa.manutencao_id, despesa.descricao,
                     despesa.categoria, despesa.valor, despesa.data))
            self._liberar_kitnet(conn, atual["kitnet_id"])
            HistoricoService.registrar(
                usuario_id, "CONCLUSAO_MANUTENCAO",
                f"Manutenção #{manutencao_id} concluída. Custo: {custo:.2f}.", conn)

    def cancelar(self, manutencao_id, usuario_id):
        with Conexao.transacao() as conn:
            atual = self._buscar(conn, manutencao_id)
            if atual["status"] not in Manutencao.STATUS_ABERTOS:
                raise ErroNegocio("Esta manutenção já foi concluída ou cancelada.")
            conn.execute("UPDATE manutencoes SET status = ? WHERE id = ?",
                         (Manutencao.CANCELADA, manutencao_id))
            self._liberar_kitnet(conn, atual["kitnet_id"])
            HistoricoService.registrar(
                usuario_id, "CANCELAMENTO_MANUTENCAO", f"Manutenção #{manutencao_id} cancelada.", conn)

    def listar(self, status=None):
        return Conexao.consultar(
            """SELECT m.id, m.kitnet_id, k.endereco AS kitnet, m.descricao,
                      m.categoria, m.custo, m.status
               FROM manutencoes m
               JOIN kitnets k ON k.id = m.kitnet_id
               WHERE (? IS NULL OR m.status = ?)
               ORDER BY m.id DESC""",
            (status, status),
        )

    def buscar_por_id(self, manutencao_id):
        linha = Conexao.consultar_um("SELECT * FROM manutencoes WHERE id = ?", (manutencao_id,))
        return Manutencao.from_row(linha) if linha else None

    @staticmethod
    def _buscar(conn, manutencao_id):
        linha = conn.execute("SELECT * FROM manutencoes WHERE id = ?", (manutencao_id,)).fetchone()
        if linha is None:
            raise ErroNegocio("Manutenção não encontrada.")
        return linha

    @staticmethod
    def _liberar_kitnet(conn, kitnet_id):
        """Libera a kitnet se não restarem manutenções abertas nela."""
        restantes = conn.execute(
            "SELECT COUNT(*) FROM manutencoes WHERE kitnet_id = ? AND status IN (?, ?)",
            (kitnet_id, *Manutencao.STATUS_ABERTOS)).fetchone()[0]
        if restantes == 0:
            conn.execute("UPDATE kitnets SET status = ? WHERE id = ? AND status = ?",
                         (Kitnet.DISPONIVEL, kitnet_id, Kitnet.EM_MANUTENCAO))