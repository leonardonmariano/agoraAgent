from db import repositorio


def test_normalizar_data_fato_formatos_aceitos():
    assert repositorio.normalizar_data_fato("31/05/2026") == "2026-05-31"
    assert repositorio.normalizar_data_fato("31-05-2026") == "2026-05-31"
    assert repositorio.normalizar_data_fato("2026-05-31") == "2026-05-31"
    assert repositorio.normalizar_data_fato(None) is None
    assert repositorio.normalizar_data_fato("") is None


def test_normalizar_hora_fato_formatos_aceitos():
    assert repositorio.normalizar_hora_fato("21h30") == "21:30"
    assert repositorio.normalizar_hora_fato("21:30") == "21:30"
    assert repositorio.normalizar_hora_fato("21:30:00") == "21:30"
    assert repositorio.normalizar_hora_fato(None) is None
    assert repositorio.normalizar_hora_fato("") is None


def test_salvar_bo_normaliza_data_e_hora_no_payload(monkeypatch):
    chamadas = []

    class RespostaFake:
        headers = {}

        def json(self):
            return [{"id": "boletim-1"}]

    def request_fake(metodo, tabela, **kwargs):
        chamadas.append((metodo, tabela, kwargs))
        return RespostaFake()

    monkeypatch.setattr(repositorio, "request", request_fake)

    numero = repositorio.salvar_bo(
        {
            "numero": "BO-TESTE",
            "tipo_penal": "Roubo",
            "data_fato": "31/05/2026",
            "hora_fato": "21h30",
            "narrativa": "Teste.",
            "partes": [],
            "objetos": [],
        }
    )

    assert numero == "BO-TESTE"
    payload = chamadas[0][2]["json"]
    assert payload["data_fato"] == "2026-05-31"
    assert payload["hora_fato"] == "21:30"


def test_data_hora_invalidas_sao_ignoradas_com_warning(caplog):
    caplog.set_level("WARNING")

    assert repositorio.normalizar_data_fato("31/31/2026") is None
    assert repositorio.normalizar_hora_fato("25h99") is None
    assert "data_fato invalida" in caplog.text
    assert "hora_fato invalida" in caplog.text
