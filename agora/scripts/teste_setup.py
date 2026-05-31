"""Verifica se a conexao com OpenAI e Supabase esta funcionando."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agente.llm import chamar_modelo


def testar_openai() -> None:
    resposta = chamar_modelo("Diga apenas: ola")
    if not resposta:
        raise RuntimeError("OpenAI retornou resposta vazia")
    print(f"  OpenAI OK - resposta: {resposta.strip()[:60]}")


def testar_supabase() -> None:
    from db.repositorio import contar_bos

    total = contar_bos()
    print(f"  Supabase OK - tabela boletins acessivel ({total} registros)")


def main() -> None:
    print("Testando configuracao do AGORA...\n")
    erros = []

    print("1. OpenAI")
    try:
        testar_openai()
    except Exception as exc:
        erros.append(f"OpenAI: {exc}")
        print(f"  ERRO: {exc}")

    print("2. Supabase")
    try:
        testar_supabase()
    except Exception as exc:
        erros.append(f"Supabase: {exc}")
        print(f"  ERRO: {exc}")

    print()
    if erros:
        print("Setup com erros:")
        for erro in erros:
            print(f"   - {erro}")
        sys.exit(1)

    print("Setup OK")


if __name__ == "__main__":
    main()
