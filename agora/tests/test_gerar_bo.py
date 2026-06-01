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


def test_falha_openai_nao_vaza_erro_tecnico(monkeypatch, caplog):
    monkeypatch.setattr("agente.ferramentas._tem_openai", lambda: True)

    def falhar(*args, **kwargs):
        raise RuntimeError("Incorrect API key provided: sk-abc")

    monkeypatch.setattr("agente.ferramentas.chamar_modelo_geracao", falhar)

    caplog.set_level("WARNING")
    bo = gerar_bo(RELATO_ROUBO)
    texto = " ".join(bo["pendencias"])
    logs = caplog.text

    assert "Incorrect API key" not in texto
    assert "sk-" not in texto
    assert "Incorrect API key" not in logs
    assert "sk-" not in logs
    assert "Modo local de contingencia ativado" in logs
    assert "falha nao classificada" in logs
    assert "IA indisponivel" in texto


def test_gerar_bo_rejeita_resumo_vazio():
    try:
        gerar_bo("   ")
    except ValueError as exc:
        assert "vazio" in str(exc)
    else:
        raise AssertionError("gerar_bo deveria rejeitar resumo vazio")


def test_chave_openai_malformada_desativa_ia(monkeypatch):
    monkeypatch.setattr("agente.ferramentas.config", lambda nome, padrao="": "abc" if nome == "OPENAI_API_KEY" else padrao)
    monkeypatch.setattr("agente.ferramentas._openai_config_logada", False)

    from agente import ferramentas

    assert ferramentas._tem_openai() is False
