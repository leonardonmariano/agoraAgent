"""Cliente REST simples para Supabase inicializado a partir do .env."""

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

_URL = os.getenv("SUPABASE_URL", "")
_KEY = os.getenv("SUPABASE_KEY", "")


def _credenciais() -> tuple[str, str]:
    if not _URL or not _KEY:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY precisam estar definidos no .env")
    return _URL.rstrip("/"), _KEY


def headers(prefer: str | None = None) -> dict[str, str]:
    _, key = _credenciais()
    base = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        base["Prefer"] = prefer
    return base


def rest_url(tabela: str) -> str:
    url, _ = _credenciais()
    return f"{url}/rest/v1/{tabela}"


def request(
    metodo: str,
    tabela: str,
    *,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    prefer: str | None = None,
    timeout: int = 20,
) -> httpx.Response:
    """Executa uma chamada REST ao Supabase e valida status HTTP."""
    verify_ssl = os.getenv("HTTPX_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}
    resposta = httpx.request(
        metodo,
        rest_url(tabela),
        headers=headers(prefer),
        params=params,
        json=json,
        timeout=timeout,
        verify=verify_ssl,
    )
    if resposta.status_code >= 400:
        raise RuntimeError(f"Supabase {resposta.status_code}: {resposta.text}")
    return resposta


def cliente() -> dict[str, str]:
    """Compatibilidade para scripts: retorna URL e headers prontos."""
    url, _ = _credenciais()
    return {"url": url, "headers": headers()}
