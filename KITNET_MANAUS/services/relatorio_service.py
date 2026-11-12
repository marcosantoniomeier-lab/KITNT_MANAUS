"""Relatórios gerenciais. Cada relatório devolve (colunas, linhas)."""
from datetime import date

from database.conexao import Conexao
from models.kitnet import Kitnet
from services import formatar_moeda
from services.pagamento_service import PagamentoService
from services.usuario_service import HistoricoService


class RelatorioService:
    def catalogo(self):
        """Nome do relatório -> método que o gera."""
        return {
            "Resumo geral": self.resumo_geral,
            "Kitnets por status": self.kitnets_por_status,
            "Locações ativas": self.locacoes_ativas,
            "Pagamentos em aberto": self.pagamentos_em_aberto,
            "Receita mensal": self.receita_mensal,
            "Despesas por categoria": self.despesas_por_categoria,
            "Financeiro por kitnet": self.financeiro_por_kitnet,
            "Histórico de operações": self.historico_operacoes,
        }

    def resumo_geral(self):
        PagamentoService().atualizar_atrasados()
        with Conexao.transacao() as conn:
            def valor(sql, params=()):
                return conn.execute(sql, params).fetchone()[0]

            total = valor("SELECT COUNT(*) FROM kitnets")
            por_status = {s: valor("SELECT COUNT(*) FROM kitnets WHERE status = ?", (s,))
                          for s in Kitnet.STATUS_VALIDOS}
            estudantes = valor("SELECT COUNT(*) FROM estudantes")
            ativas = valor("SELECT COUNT(*) FROM locacoes WHERE status = 'Ativa'")
            recebido = valor("SELECT COALESCE(SUM(valor), 0) FROM pagamentos WHERE status = 'Pago'")
            pendente = valor("SELECT COALESCE(SUM(valor), 0) FROM pagamentos WHERE status = 'Pendente'")
            atrasado = valor("SELECT COALESCE(SUM(valor), 0) FROM pagamentos WHERE status = 'Atrasado'")
            despesas = valor("SELECT COALESCE(SUM(valor), 0) FROM despesas")

        ocupacao = (por_status[Kitnet.ALUGADA] / total * 100) if total else 0
        linhas = [
            ("Total de kitnets", total),
            ("Kitnets disponíveis", por_status[Kitnet.DISPONIVEL]),
            ("Kitnets alugadas", por_status[Kitnet.ALUGADA]),
            ("Kitnets em manutenção", por_status[Kitnet.EM_MANUTENCAO]),
            ("Taxa de ocupação", f"{ocupacao:.1f}%"),
            ("Estudantes cadastrados", estudantes),
            ("Locações ativas", ativas),
            ("Receita recebida", formatar_moeda(recebido)),
            ("A receber (pendente)", formatar_moeda(pendente)),
            ("Em atraso", formatar_moeda(atrasado)),
            ("Despesas totais", formatar_moeda(despesas)),
            ("Saldo (recebido - despesas)", formatar_moeda(recebido - despesas)),
        ]
        return ["Indicador", "Valor"], linhas

    def kitnets_por_status(self):
        rows = Conexao.consultar(
            """SELECT status, COUNT(*) AS qtd, COALESCE(SUM(valor_aluguel), 0) AS total
               FROM kitnets GROUP BY status ORDER BY status""")
        linhas = [(r["status"], r["qtd"], formatar_moeda(r["total"])) for r in rows]
        return ["Status", "Quantidade", "Soma dos aluguéis"], linhas

    def locacoes_ativas(self):
        rows = Conexao.consultar(
            """SELECT l.id, e.nome AS estudante, k.endereco AS kitnet,
                      l.data_inicio, l.data_fim, l.valor_contratado
               FROM locacoes l
               JOIN estudantes e ON e.id = l.estudante_id
               JOIN kitnets k ON k.id = l.kitnet_id
               WHERE l.status = 'Ativa'
               ORDER BY e.nome""")
        linhas = [(r["id"], r["estudante"], r["kitnet"], r["data_inicio"],
                   r["data_fim"] or "-", formatar_moeda(r["valor_contratado"])) for r in rows]
        return ["Locação", "Estudante", "Kitnet", "Início", "Fim previsto", "Valor"], linhas

    def pagamentos_em_aberto(self):
        PagamentoService().atualizar_atrasados()
        rows = Conexao.consultar(
            """SELECT p.id, e.nome AS estudante, k.endereco AS kitnet,
                      p.vencimento, p.valor, p.status
               FROM pagamentos p
               JOIN locacoes l ON l.id = p.locacao_id
               JOIN estudantes e ON e.id = l.estudante_id
               JOIN kitnets k ON k.id = l.kitnet_id
               WHERE p.status IN ('Pendente', 'Atrasado')
               ORDER BY p.vencimento""")
        hoje = date.today()
        linhas = []
        for r in rows:
            dias = max((hoje - date.fromisoformat(r["vencimento"])).days, 0)
            linhas.append((r["id"], r["estudante"], r["kitnet"], r["vencimento"],
                           formatar_moeda(r["valor"]), r["status"], dias))
        return ["Pagamento", "Estudante", "Kitnet", "Vencimento", "Valor", "Status", "Dias de atraso"], linhas

    def receita_mensal(self):
        rows = Conexao.consultar(
            """SELECT strftime('%Y-%m', data_pagamento) AS mes, COUNT(*) AS qtd, SUM(valor) AS total
               FROM pagamentos WHERE status = 'Pago'
               GROUP BY mes ORDER BY mes DESC""")
        linhas = [(r["mes"], r["qtd"], formatar_moeda(r["total"])) for r in rows]
        return ["Mês", "Pagamentos recebidos", "Total recebido"], linhas

    def despesas_por_categoria(self):
        rows = Conexao.consultar(
            """SELECT categoria, COUNT(*) AS qtd, SUM(valor) AS total
               FROM despesas GROUP BY categoria ORDER BY total DESC""")
        linhas = [(r["categoria"], r["qtd"], formatar_moeda(r["total"])) for r in rows]
        return ["Categoria", "Quantidade", "Total"], linhas

    def financeiro_por_kitnet(self):
        rows = Conexao.consultar(
            """SELECT k.id, k.endereco,
                 COALESCE((SELECT SUM(p.valor) FROM pagamentos p
                           JOIN locacoes l ON l.id = p.locacao_id
                           WHERE l.kitnet_id = k.id AND p.status = 'Pago'), 0) AS receita,
                 COALESCE((SELECT SUM(d.valor) FROM despesas d
                           WHERE d.kitnet_id = k.id), 0) AS despesa
               FROM kitnets k ORDER BY k.id""")
        linhas = [(r["id"], r["endereco"], formatar_moeda(r["receita"]),
                   formatar_moeda(r["despesa"]), formatar_moeda(r["receita"] - r["despesa"]))
                  for r in rows]
        return ["Kitnet", "Endereço", "Receita", "Despesas", "Resultado"], linhas

    def historico_operacoes(self):
        rows = HistoricoService.listar(200)
        linhas = [(r["data_hora"], r["usuario"], r["operacao"], r["descricao"]) for r in rows]
        return ["Data/Hora", "Usuário", "Operação", "Descrição"], linhas