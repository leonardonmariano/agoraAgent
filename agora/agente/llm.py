"""Wrapper centralizado para chamadas a OpenAI."""

import logging

from openai import OpenAI

from config import config

logger = logging.getLogger(__name__)

_cliente: OpenAI | None = None

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
    api_key = config("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY precisa estar definido em st.secrets ou no .env")

    global _cliente
    if _cliente is None:
        _cliente = OpenAI(api_key=api_key)

    modelo_efetivo = modelo or config("MODELO_GERAL", "gpt-4o-mini")
    temperatura_padrao = float(config("TEMPERATURA_GERAL", "0.3"))
    temperatura_efetiva = temperatura if temperatura is not None else temperatura_padrao

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
        modelo=config("MODELO_GERACAO_BO", "gpt-4o"),
        temperatura=float(config("TEMPERATURA_GERACAO", "0.4")),
        sistema=sistema,
    )
