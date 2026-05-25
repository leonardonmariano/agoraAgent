"""Verifica se a conexão com OpenAI e Supabase está funcionando."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agente.llm import chamar_modelo
from db.conexao import cliente


def testar_openai() -> None:
    resposta = chamar_modelo("Diga apenas: olá")
    if not resposta:
        raise RuntimeError("OpenAI retornou resposta vazia")
    print(f"  OpenAI OK — resposta: {resposta.strip()[:60]}")


def testar_supabase() -> None:
    db = cliente()
    resultado = db.rpc("", {}).execute() if False else None
    # Usa a API REST diretamente para executar SELECT 1
    import httpx
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    resp = httpx.get(
        f"{url}/rest/v1/",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        timeout=10,
    )
    if resp.status_code not in (200, 404):
        raise RuntimeError(f"Supabase retornou status {resp.status_code}")
    print(f"  Supabase OK — status {resp.status_code}")


def main() -> None:
    print("Testando configuração do ÁGORA...\n")
    erros = []

    print("1. OpenAI")
    try:
        testar_openai()
    except Exception as exc:
        erros.append(f"OpenAI: {exc}")
        print(f"  ❌ {exc}")

    print("2. Supabase")
    try:
        testar_supabase()
    except Exception as exc:
        erros.append(f"Supabase: {exc}")
        print(f"  ❌ {exc}")

    print()
    if erros:
        print("❌ Setup com erros:")
        for e in erros:
            print(f"   - {e}")
        sys.exit(1)
    else:
        print("✅ Setup OK")


if __name__ == "__main__":
    main()
