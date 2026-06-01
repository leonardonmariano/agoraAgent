from app.pdf import gerar_pdf_bo, nome_arquivo_pdf


def test_gerar_pdf_bo_retorna_pdf_valido():
    bo = {
        "numero": "BO-20260601-ABC123",
        "tipo_penal": "Roubo",
        "artigo_penal": "Art. 157 do CP",
        "data_fato": "2026-05-31",
        "hora_fato": "21:30",
        "cidade": "São Paulo",
        "uf": "SP",
        "bairro": "Bela Vista",
        "narrativa": "Narrativa oficial do boletim.",
        "partes": [{"papel": "vitima", "nome": "João Silva", "documento": None, "descricao": "Vítima."}],
        "objetos": [{"descricao": "Aparelho celular", "status": "subtraido"}],
        "raciocinio_cot": "Classificação preliminar do fato.",
    }

    pdf = gerar_pdf_bo(bo)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
    assert nome_arquivo_pdf(bo) == "bo-20260601-abc123_ocorrencia.pdf"
