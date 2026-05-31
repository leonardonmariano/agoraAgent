"""Cliente REST simples para Supabase.

Em producao no Streamlit Cloud, as credenciais podem vir de st.secrets. Em
desenvolvimento local, elas sao lidas de variaveis de ambiente/.env.
"""

import os
import json as json_lib
import ssl
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()


def _ler_streamlit_secret(nome: str) -> str:
    """Le uma chave de st.secrets quando o codigo roda dentro do Streamlit."""
    try:
        import streamlit as st

        valor = st.secrets.get(nome)
        if valor is None and "supabase" in st.secrets:
            valor = st.secrets["supabase"].get(nome)
        return str(valor or "")
    except Exception:
        return ""


def _config(nome: str, padrao: str = "") -> str:
    return _ler_streamlit_secret(nome) or os.getenv(nome, padrao)


def _credenciais() -> tuple[str, str]:
    url = _config("SUPABASE_URL")
    key = _config("SUPABASE_KEY")
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL e SUPABASE_KEY precisam estar definidos em st.secrets ou no .env"
        )
    return url.rstrip("/"), key


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
) -> "RestResponse":
    """Executa uma chamada REST ao Supabase e valida status HTTP."""
    verify_ssl = _config("HTTPX_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}
    url = rest_url(tabela)
    if params:
        url = f"{url}?{urlencode(params)}"

    body = None
    if json is not None:
        body = json_lib.dumps(json).encode("utf-8")

    req = Request(
        url,
        data=body,
        headers=headers(prefer),
        method=metodo.upper(),
    )
    contexto = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()

    try:
        with urlopen(req, timeout=timeout, context=contexto) as resp:
            resposta = RestResponse(
                status_code=resp.status,
                text=resp.read().decode("utf-8"),
                headers=dict(resp.headers.items()),
            )
    except HTTPError as exc:
        resposta = RestResponse(
            status_code=exc.code,
            text=exc.read().decode("utf-8"),
            headers=dict(exc.headers.items()),
        )

    if resposta.status_code >= 400:
        raise RuntimeError(f"Supabase {resposta.status_code}: {resposta.text}")
    return resposta


def cliente() -> dict[str, str]:
    """Compatibilidade para scripts: retorna URL e headers prontos."""
    url, _ = _credenciais()
    return {"url": url, "headers": headers()}


class RestResponse:
    """Resposta minima compatível com o uso do repositorio."""

    def __init__(self, status_code: int, text: str, headers: dict[str, str]) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers

    def json(self) -> Any:
        if not self.text:
            return []
        return json_lib.loads(self.text)
