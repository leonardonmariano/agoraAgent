"""Casos de teste reutilizaveis."""

RELATO_ROUBO = (
    "Vitima relatou que estava na Avenida Paulista em Sao Paulo quando dois "
    "individuos em uma moto levaram seu celular mediante ameaca com arma."
)

BOS_EXEMPLO = [
    {
        "tipo_penal": "Furto",
        "data_fato": "2026-05-20",
        "cidade": "Sao Paulo",
        "uf": "SP",
        "bairro": "Pinheiros",
        "narrativa": "Furto de celular.",
    },
    {
        "tipo_penal": "Furto",
        "data_fato": "2026-05-21",
        "cidade": "Sao Paulo",
        "uf": "SP",
        "bairro": "Pinheiros",
        "narrativa": "Furto de carteira.",
    },
    {
        "tipo_penal": "Roubo",
        "data_fato": "2026-05-22",
        "cidade": "Belo Horizonte",
        "uf": "MG",
        "bairro": "Savassi",
        "narrativa": "Roubo em via publica.",
    },
]
