"""Regras de negócio de Pagamentos."""
import calendar
from datetime import date, datetime

from database.conexao import Conexao
from models.locacao import Locacao
from models.pagamento import Pagamento
from services import ErroNegocio
from services.usuario_service import HistoricoService


def _validar_data(texto, campo):
    try:
        return datetime.strptime((texto or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ErroNegocio(f"{campo} inválida. Use o formato AAAA-MM-DD.") from None


def _somar_meses(data, meses):
    total = data.month - 1 + meses
    ano = data.year + total // 12
    mes = total % 12 + 1
    dia = min(data.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


class PagamentoService:
    def atualizar_atrasados(self):
        """Marca como 'Atrasado' todo pagamento pendente já vencido."""
        with Conexao.transacao() as conn:
            conn.execute(
                "UPDATE pagamentos SET status = ? WHERE status = ? AND vencimento < ?",
                (Pagamento.ATRASADO, Pagamento.PENDENTE, date.today().isoformat()))

    def registrar(self, pagamento, usuario_id):
        """Cria uma cobrança (parcela) para uma locação."""
        pagamento.status = Pagamento.PENDENTE
        pagamento.data_pagamento = None
        pagamento.validar()
        with Conexao.transacao() as conn:
            loc = conn.execute("SELECT id, status FROM locacoes WHERE id = ?",
                               (pagamento.locacao_id,)).fetchone()
            if loc is None:
                raise ErroNegocio("Locação não encontrada.")
            if loc["status"] == Locacao.CANCELADA:
                raise ErroNegocio("Não é possível lançar pagamentos em locação cancelada.")
            status = (Pagamento.ATRASADO if pagamento.vencimento < date.today().isoformat()
                      else Pagamento.PENDENTE)
            cur = conn.execute(
                "INSERT INTO pagamentos (locacao_id, valor, vencimento, status) VALUES (?, ?, ?, ?)",
                (pagamento.locacao_id, pagamento.valor, pagamento.vencimento, status))
            novo_id = cur.lastrowid
            HistoricoService.registrar(
                usuario_id, "NOVO_PAGAMENTO",
                f"Pagamento #{novo_id} (locação #{pagamento.locacao_id}) com vencimento em {pagamento.vencimento}.",
                conn)
        return novo_id

    def gerar_mensalidades(self, locacao_id, quantidade, primeiro_vencimento, usuario_id):
        """Gera 'quantidade' parcelas mensais com o valor contratado da locação."""
        if not 1 <= quantidade <= 60:
            raise ErroNegocio("Informe de 1 a 60 mensalidades.")
        inicio = _validar_data(primeiro_vencimento, "Data do primeiro vencimento")
        with Conexao.transacao() as conn:
            loc = conn.execute(
                "SELECT id, valor_contratado, status FROM locacoes WHERE id = ?",
                (locacao_id,)).fetchone()
            if loc is None:
                raise ErroNegocio("Locação não encontrada.")
            if loc["status"] != Locacao.ATIVA:
                raise ErroNegocio("Só é possível gerar mensalidades para locações ativas.")
            hoje = date.today().isoformat()
            for i in range(quantidade):
                venc = _somar_meses(inicio, i).isoformat()
                status = Pagamento.ATRASADO if venc < hoje else Pagamento.PENDENTE
                conn.execute(
                    "INSERT INTO pagamentos (locacao_id, valor, vencimento, status) VALUES (?, ?, ?, ?)",
                    (locacao_id, loc["valor_contratado"], venc, status))
            HistoricoService.registrar(
                usuario_id, "GERAR_MENSALIDADES",
                f"{quantidade} mensalidade(s) geradas para a locação #{locacao_id}.", conn)
        return quantidade

    def baixar(self, pagamento_id, data_pagamento, usuario_id):
        """Registra o recebimento de um pagamento."""
        data = _validar_data(data_pagamento, "Data do pagamento").isoformat()
        with Conexao.transacao() as conn:
            atual = conn.execute("SELECT status FROM pagamentos WHERE id = ?",
                                 (pagamento_id,)).fetchone()
            if atual is None:
                raise ErroNegocio("Pagamento não encontrado.")
            if atual["status"] == Pagamento.PAGO:
                raise ErroNegocio("Este pagamento já foi baixado.")
            conn.execute("UPDATE pagamentos SET status = ?, data_pagamento = ? WHERE id = ?",
                         (Pagamento.PAGO, data, pagamento_id))
            HistoricoService.registrar(
                usuario_id, "BAIXA_PAGAMENTO",
                f"Pagamento #{pagamento_id} recebido em {data}.", conn)

    def excluir(self, pagamento_id, usuario_id):
        with Conexao.transacao() as conn:
            atual = conn.execute("SELECT status FROM pagamentos WHERE id = ?",
                                 (pagamento_id,)).fetchone()
            if atual is None:
                raise ErroNegocio("Pagamento não encontrado.")
            if atual["status"] == Pagamento.PAGO:
                raise ErroNegocio("Pagamentos já recebidos não podem ser excluídos.")
            conn.execute("DELETE FROM pagamentos WHERE id = ?", (pagamento_id,))
            HistoricoService.registrar(
                usuario_id, "EXCLUSAO_PAGAMENTO", f"Pagamento #{pagamento_id} excluído.", conn)

    def listar(self, status=None, locacao_id=None):
        self.atualizar_atrasados()
        return Conexao.consultar(
            """SELECT p.id, p.locacao_id, e.nome AS estudante, k.endereco AS kitnet,
                      p.valor, p.vencimento, p.data_pagamento, p.status
               FROM pagamentos p
               JOIN locacoes l ON l.id = p.locacao_id
               JOIN estudantes e ON e.id = l.estudante_id
               JOIN kitnets k ON k.id = l.kitnet_id
               WHERE (? IS NULL OR p.status = ?) AND (? IS NULL OR p.locacao_id = ?)
               ORDER BY p.vencimento DESC, p.id DESC""",
            (status, status, locacao_id, locacao_id),
        )