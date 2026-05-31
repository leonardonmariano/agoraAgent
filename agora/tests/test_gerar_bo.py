from agente.ferramentas import gerar_bo
from tests.exemplos_entrada import RELATO_ROUBO


def test_gerar_bo_local_sem_openai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    bo = gerar_bo(RELATO_ROUBO)

    assert "Roubo" in bo["tipo_penal"]
    assert bo["cidade"] == "Sao Paulo"
    assert bo["objetos"][0]["descricao"] == "Aparelho celular"
    assert bo["narrativa"]
    assert bo["passos"]


def test_gerar_bo_rejeita_resumo_vazio():
    try:
        gerar_bo("   ")
    except ValueError as exc:
        assert "vazio" in str(exc)
    else:
        raise AssertionError("gerar_bo deveria rejeitar resumo vazio")
