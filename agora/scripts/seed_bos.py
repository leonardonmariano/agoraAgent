"""Popula o Supabase com BOs sinteticos."""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.repositorio import salvar_bo


TIPOS = [
    ("Furto", "Art. 155 do CP"),
    ("Roubo", "Art. 157 do CP"),
    ("Ameaca", "Art. 147 do CP"),
    ("Lesao corporal", "Art. 129 do CP"),
]
CIDADES = [
    ("Sao Paulo", "SP", ["Centro", "Pinheiros", "Mooca", "Bela Vista"]),
    ("Rio de Janeiro", "RJ", ["Copacabana", "Centro", "Tijuca", "Botafogo"]),
    ("Belo Horizonte", "MG", ["Savassi", "Centro", "Funcionarios", "Pampulha"]),
]
OBJETOS = ["Aparelho celular", "Carteira", "Notebook", "Bicicleta", "Dinheiro"]


def criar_bo(indice: int) -> dict:
    tipo, artigo = random.choice(TIPOS)
    cidade, uf, bairros = random.choice(CIDADES)
    bairro = random.choice(bairros)
    data_fato = date.today() - timedelta(days=random.randint(0, 90))
    objeto = random.choice(OBJETOS)
    return {
        "tipo_penal": tipo,
        "artigo_penal": artigo,
        "data_fato": data_fato.isoformat(),
        "hora_fato": f"{random.randint(0, 23):02d}:{random.choice([0, 15, 30, 45]):02d}",
        "cidade": cidade,
        "uf": uf,
        "bairro": bairro,
        "endereco": f"Rua Exemplo, {100 + indice}",
        "narrativa": f"Registro sintetico de {tipo.lower()} envolvendo {objeto.lower()} no bairro {bairro}.",
        "partes": [
            {
                "papel": "vitima",
                "nome": f"Vitima {indice}",
                "documento": None,
                "descricao": "Pessoa envolvida em registro sintetico.",
            }
        ],
        "objetos": [{"descricao": objeto, "status": "subtraido" if tipo in {"Furto", "Roubo"} else "informado"}],
        "pendencias": [],
        "raciocinio_cot": "BO sintetico para demonstracao academica.",
        "passos": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quantidade", type=int, default=150)
    args = parser.parse_args()

    for indice in range(1, args.quantidade + 1):
        numero = salvar_bo(criar_bo(indice))
        print(f"{indice:03d}/{args.quantidade:03d} salvo: {numero}")


if __name__ == "__main__":
    main()
