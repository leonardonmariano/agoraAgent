from agente.ferramentas import gerar_bo
from tests.exemplos_entrada import RELATO_ROUBO


def test_gerar_bo_local_sem_openai(monkeypatch):
    monkeypatch.setattr("agente.ferramentas._tem_openai", lambda: False)

    bo = gerar_bo(RELATO_ROUBO)

    assert "Roubo" in bo["tipo_penal"]
    assert bo["cidade"] in {"Sao Paulo", "Sao Paulo"}
    assert bo["objetos"][0]["descricao"] == "Aparelho celular"
    assert bo["data_fato"] is None
    assert bo["narrativa"]
    assert bo["passos"]


def test_falha_openai_nao_vaza_erro_tecnico(monkeypatch):
    monkeypatch.setattr("agente.ferramentas._tem_openai", lambda: True)

    def falhar(*args, **kwargs):
        raise RuntimeError("Incorrect API key provided: sk-abc")

    monkeypatch.setattr("agente.ferramentas.chamar_modelo_geracao", falhar)

    bo = gerar_bo(RELATO_ROUBO)
    texto = " ".join(bo["pendencias"])

    assert "Incorrect API key" not in texto
    assert "sk-" not in texto
    assert "IA indisponivel" in texto


def test_gerar_bo_rejeita_resumo_vazio():
    try:
        gerar_bo("   ")
    except ValueError as exc:
        assert "vazio" in str(exc)
    else:
        raise AssertionError("gerar_bo deveria rejeitar resumo vazio")
