"""Configuracao do projeto sem dependencias externas obrigatorias."""

from __future__ import annotations

import os
from pathlib import Path


def carregar_env_local() -> None:
    """Carrega .env local sem depender de python-dotenv."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def _streamlit_secret(nome: str) -> str:
    try:
        import streamlit as st

        valor = st.secrets.get(nome)
        if valor is None and "supabase" in st.secrets:
            valor = st.secrets["supabase"].get(nome)
        if valor is None and "openai" in st.secrets:
            valor = st.secrets["openai"].get(nome)
        return str(valor or "")
    except Exception:
        return ""


def config(nome: str, padrao: str = "") -> str:
    carregar_env_local()
    return _streamlit_secret(nome) or os.getenv(nome, padrao)
