import sys
import types

from agente import ferramentas
from tests.exemplos_entrada import BOS_EXEMPLO


def test_consultar_base_agrega_bairros(monkeypatch):
    monkeypatch.setattr(ferramentas, "_periodo_para_data", lambda pergunta: None)
    repositorio_fake = types.SimpleNamespace(listar_bos=lambda: BOS_EXEMPLO)
    monkeypatch.setitem(sys.modules, "db.repositorio", repositorio_fake)

    resultado = ferramentas.consultar_base("Top bairros com furto em Sao Paulo")

    assert resultado["resultados"][0]["bairro"] == "Pinheiros"
    assert resultado["resultados"][0]["total"] == 2
    assert "SELECT bairro" in resultado["sql_gerado"]


def test_gerar_relatorio_markdown(monkeypatch):
    repositorio_fake = types.SimpleNamespace(listar_bos=lambda: BOS_EXEMPLO)
    monkeypatch.setitem(sys.modules, "db.repositorio", repositorio_fake)
    relatorio = ferramentas.gerar_relatorio("Todas", "Ultimos 30 dias")

    assert "# Relatorio Executivo" in relatorio["relatorio_markdown"]
    assert "Incidencia por tipo penal" in relatorio["relatorio_markdown"]
    assert relatorio["passos"]
