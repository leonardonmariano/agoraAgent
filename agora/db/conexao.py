"""Cliente Supabase inicializado a partir do .env."""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_URL = os.getenv("SUPABASE_URL", "")
_KEY = os.getenv("SUPABASE_KEY", "")


def obter_cliente() -> Client:
    """Retorna o cliente Supabase configurado.

    Raises:
        ValueError: Se as variáveis de ambiente não estiverem definidas.
    """
    if not _URL or not _KEY:
        raise ValueError(
            "SUPABASE_URL e SUPABASE_KEY precisam estar definidos no .env"
        )
    return create_client(_URL, _KEY)


_cliente_singleton: Client | None = None


def cliente() -> Client:
    """Retorna instância singleton do cliente Supabase."""
    global _cliente_singleton
    if _cliente_singleton is None:
        _cliente_singleton = obter_cliente()
    return _cliente_singleton
