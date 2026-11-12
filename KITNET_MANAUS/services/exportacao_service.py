"""Serviço de exportação de dados para Excel (.xlsx/.xls), TXT e JSON."""
import json
from pathlib import Path
import openpyxl
from openpyxl.styles import Font
import xlwt

from database.conexao import Conexao


class ExportacaoService:
    @staticmethod
    def exportar_pagamentos_excel(caminho_arquivo: str) -> int:
        sql = """
            SELECT p.id,
                   e.nome AS estudante,
                   k.endereco || ' - ' || k.bairro AS kitnet,
                   p.vencimento,
                   p.valor,
                   p.status,
                   p.data_pagamento
              FROM pagamentos p
              JOIN locacoes l ON l.id = p.locacao_id
              JOIN estudantes e ON e.id = l.estudante_id
              JOIN kitnets k ON k.id = l.kitnet_id
             ORDER BY p.vencimento DESC
        """
        registros = Conexao.consultar(sql)
        cabecalhos = [
            "ID", "Estudante", "Kitnet", "Vencimento",
            "Valor (R$)", "Status", "Data Pagamento"
        ]

        ext = Path(caminho_arquivo).suffix.lower()

        if ext == ".xls":
            wb = xlwt.Workbook(encoding="utf-8")
            ws = wb.add_sheet("Pagamentos")
            estilo_cab = xlwt.easyxf("font: bold on;")
            for col_idx, titulo in enumerate(cabecalhos):
                ws.write(0, col_idx, titulo, estilo_cab)

            for row_idx, reg in enumerate(registros, start=1):
                valores = [
                    reg["id"], reg["estudante"], reg["kitnet"],
                    reg["vencimento"], float(reg["valor"]),
                    reg["status"], reg["data_pagamento"] or ""
                ]
                for col_idx, val in enumerate(valores):
                    ws.write(row_idx, col_idx, val)
            wb.save(caminho_arquivo)
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Pagamentos"
            ws.append(cabecalhos)
            for cell in ws:
                cell.font = Font(bold=True)

            for reg in registros:
                ws.append([
                    reg["id"], reg["estudante"], reg["kitnet"],
                    reg["vencimento"], float(reg["valor"]),
                    reg["status"], reg["data_pagamento"] or ""
                ])
            wb.save(caminho_arquivo)

        return len(registros)

    @staticmethod
    def exportar_estudantes_txt(caminho_arquivo: str) -> int:
        registros = Conexao.consultar(
            "SELECT id, nome, cpf, telefone, email, curso, instituicao FROM estudantes ORDER BY nome"
        )
        linhas = [
            "============================================================",
            "             KITNET MANAUS - ALUNOS CADASTRADOS             ",
            "============================================================\n",
        ]
        for reg in registros:
            linhas.append(f"ID: {reg['id']} | Nome: {reg['nome']}")
            linhas.append(f"CPF: {reg['cpf']} | Telefone: {reg['telefone']} | E-mail: {reg['email']}")
            linhas.append(f"Curso: {reg['curso']} | Instituição: {reg['instituicao']}")
            linhas.append("-" * 60)

        linhas.append(f"\nTotal de alunos cadastrados: {len(registros)}")

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))

        return len(registros)

    @staticmethod
    def exportar_kitnets_json(caminho_arquivo: str) -> int:
        registros = Conexao.consultar(
            "SELECT id, endereco, bairro, quartos, valor_aluguel, status FROM kitnets ORDER BY id"
        )
        dados = [dict(reg) for reg in registros]

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)

        return len(dados)