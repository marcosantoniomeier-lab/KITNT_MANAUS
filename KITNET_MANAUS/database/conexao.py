"""Gerenciamento de conexões com o banco SQLite (módulo nativo sqlite3)."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "kitnet_manaus.db"


class Conexao:
    """Fábrica de conexões e utilitários de consulta."""

    caminho = DB_PATH

    @classmethod
    def conectar(cls):
        conn = sqlite3.connect(cls.caminho)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @classmethod
    @contextmanager
    def transacao(cls):
        """Abre conexão, faz commit no sucesso, rollback no erro e sempre fecha."""
        conn = cls.conectar()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @classmethod
    def consultar(cls, sql, parametros=()):
        """Executa um SELECT e devolve todas as linhas."""
        with cls.transacao() as conn:
            return conn.execute(sql, parametros).fetchall()

    @classmethod
    def consultar_um(cls, sql, parametros=()):
        """Executa um SELECT e devolve a primeira linha (ou None)."""
        with cls.transacao() as conn:
            return conn.execute(sql, parametros).fetchone()