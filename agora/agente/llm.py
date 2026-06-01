"""Wrapper centralizado para chamadas a OpenAI."""

import logging

from openai import OpenAI

from config import config

logger = logging.getLogger(__name__)

_cliente: OpenAI | None = None
_openai_cliente_logado = False

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
    api_key = config("OPENAI_API_KEY").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY precisa estar definido em st.secrets ou no .env")
    if not api_key.startswith("sk-"):
        raise ValueError("OPENAI_API_KEY foi lida, mas nao parece ter o formato esperado")

    global _cliente
    if _cliente is None:
        global _openai_cliente_logado
        verify_ssl = config("HTTPX_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}
        if not _openai_cliente_logado:
            logger.info(
                "Inicializando cliente OpenAI (verify_ssl=%s, chave_presente=%s, chave_tamanho=%d).",
                verify_ssl,
                bool(api_key),
                len(api_key),
            )
            _openai_cliente_logado = True
        if verify_ssl:
            _cliente = OpenAI(api_key=api_key)
        else:
            import httpx

            _cliente = OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))

    modelo_efetivo = modelo or config("MODELO_GERAL", "gpt-4o-mini")
    temperatura_padrao = float(config("TEMPERATURA_GERAL", "0.3"))
    temperatura_efetiva = temperatura if temperatura is not None else temperatura_padrao

    mensagens = []
    if sistema:
        mensagens.append({"role": "system", "content": sistema})
    mensagens.append({"role": "user", "content": prompt})

    logger.info(
        "Chamando OpenAI: modelo=%s temperatura=%.1f system_message=%s prompt_caracteres=%d.",
        modelo_efetivo,
        temperatura_efetiva,
        bool(sistema),
        len(prompt),
    )

    resposta = _cliente.chat.completions.create(
        model=modelo_efetivo,
        messages=mensagens,
        temperature=temperatura_efetiva,
    )

    texto = resposta.choices[0].message.content or ""
    logger.info("OpenAI respondeu com sucesso: %d caracteres.", len(texto))
    return texto


def chamar_modelo_geracao(prompt: str, sistema: str | None = None) -> str:
    """Atalho para o modelo de geração de BO (maior qualidade)."""
    return chamar_modelo(
        prompt,
        modelo=config("MODELO_GERACAO_BO", "gpt-4o"),
        temperatura=float(config("TEMPERATURA_GERACAO", "0.4")),
        sistema=sistema,
    )
