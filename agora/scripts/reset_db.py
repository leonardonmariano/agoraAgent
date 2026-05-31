"""Apaga todos os registros das tabelas do AGORA."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.repositorio import apagar_todos


def main() -> None:
    confirmacao = input("Digite APAGAR para remover todos os BOs do Supabase: ").strip()
    if confirmacao != "APAGAR":
        print("Operacao cancelada.")
        return
    apagar_todos()
    print("Banco limpo com sucesso.")


if __name__ == "__main__":
    main()
