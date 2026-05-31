"""Wrapper centralizado para chamadas a OpenAI."""

import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

_cliente: OpenAI | None = None

_MODELO_GERAL = os.getenv("MODELO_GERAL", "gpt-4o-mini")
_MODELO_GERACAO_BO = os.getenv("MODELO_GERACAO_BO", "gpt-4o")
_TEMPERATURA_GERAL = float(os.getenv("TEMPERATURA_GERAL", "0.3"))
_TEMPERATURA_GERACAO = float(os.getenv("TEMPERATURA_GERACAO", "0.4"))


def chamar_modelo(
    prompt: str,
    modelo: str | None = None,
    temperatura: float | None = None,
    sistema: str | None = None,
) -> str:
    """Chama a OpenAI e retorna o texto da resposta.

    Args:
        prompt: Mensagem do usuário.
        modelo: Identificador do modelo. Usa MODELO_GERAL por padrão.
        temperatura: Temperatura de amostragem. Usa TEMPERATURA_GERAL por padrão.
        sistema: Conteúdo do system message. Opcional.

    Returns:
        Texto gerado pelo modelo.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY precisa estar definido no .env")

    global _cliente
    if _cliente is None:
        verify_ssl = os.getenv("HTTPX_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}
        if verify_ssl:
            _cliente = OpenAI(api_key=api_key)
        else:
            import httpx

            _cliente = OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))

    modelo_efetivo = modelo or _MODELO_GERAL
    temperatura_efetiva = temperatura if temperatura is not None else _TEMPERATURA_GERAL

    mensagens = []
    if sistema:
        mensagens.append({"role": "system", "content": sistema})
    mensagens.append({"role": "user", "content": prompt})

    logger.debug("Chamando modelo=%s temperatura=%.1f", modelo_efetivo, temperatura_efetiva)

    resposta = _cliente.chat.completions.create(
        model=modelo_efetivo,
        messages=mensagens,
        temperature=temperatura_efetiva,
    )

    texto = resposta.choices[0].message.content or ""
    logger.debug("Resposta recebida: %d caracteres", len(texto))
    return texto


def chamar_modelo_geracao(prompt: str, sistema: str | None = None) -> str:
    """Atalho para o modelo de geração de BO (maior qualidade)."""
    return chamar_modelo(
        prompt,
        modelo=_MODELO_GERACAO_BO,
        temperatura=_TEMPERATURA_GERACAO,
        sistema=sistema,
    )
