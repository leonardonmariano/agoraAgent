"""Ferramentas do agente AGORA.

As funcoes abaixo sao chamadas diretamente pela interface Streamlit. Elas tentam
usar OpenAI quando a chave esta configurada e mantem um fallback local para que
o projeto continue demonstravel em sala de aula sem rede ou sem credito de API.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from agente.llm import chamar_modelo, chamar_modelo_geracao
from config import config

logger = logging.getLogger(__name__)
_openai_config_logada = False


def _tem_openai() -> bool:
    """Valida a leitura da chave da OpenAI sem expor segredo em logs."""
    global _openai_config_logada

    api_key = config("OPENAI_API_KEY").strip()
    if not api_key:
        if not _openai_config_logada:
            logger.warning(
                "OpenAI desativada: OPENAI_API_KEY nao foi encontrada em st.secrets, variaveis de ambiente ou .env."
            )
            _openai_config_logada = True
        return False

    if not api_key.startswith("sk-"):
        if not _openai_config_logada:
            logger.warning(
                "OpenAI desativada: OPENAI_API_KEY foi lida, mas nao parece ter o formato esperado."
            )
            _openai_config_logada = True
        return False

    if not _openai_config_logada:
        logger.info(
            "OpenAI configurada: OPENAI_API_KEY lida com sucesso (prefixo=%s..., tamanho=%d).",
            api_key[:7],
            len(api_key),
        )
        _openai_config_logada = True
    return True


def _motivo_falha_openai(exc: Exception) -> str:
    """Classifica uma falha da OpenAI em uma mensagem segura para log."""
    nome = exc.__class__.__name__.lower()
    status = getattr(exc, "status_code", None)

    if status in {401, 403} or "auth" in nome or "permission" in nome:
        return "credencial recusada ou sem permissao"
    if status == 429 or "rate" in nome:
        return "limite de requisicoes ou cota atingido"
    if status and 500 <= int(status) <= 599:
        return "servico da OpenAI indisponivel temporariamente"
    if "timeout" in nome:
        return "tempo limite excedido"
    if "connection" in nome or "network" in nome or "api connection" in nome:
        return "falha de conectividade com a OpenAI"
    if "json" in nome:
        return "resposta da IA nao veio em JSON valido"
    return "falha nao classificada na chamada da OpenAI"


def _extrair_json(texto: str) -> dict[str, Any]:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?", "", texto, flags=re.I).strip()
        texto = re.sub(r"```$", "", texto).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fim = texto.rfind("}")
        if inicio >= 0 and fim > inicio:
            return json.loads(texto[inicio : fim + 1])
        raise


def _normalizar_bo(bo: dict[str, Any]) -> dict[str, Any]:
    partes = bo.get("partes") if isinstance(bo.get("partes"), list) else []
    objetos = bo.get("objetos") if isinstance(bo.get("objetos"), list) else []
    pendencias = bo.get("pendencias") if isinstance(bo.get("pendencias"), list) else []
    passos = bo.get("passos") if isinstance(bo.get("passos"), list) else []

    return {
        "tipo_penal": bo.get("tipo_penal") or "Não informado",
        "artigo_penal": bo.get("artigo_penal"),
        "data_fato": bo.get("data_fato"),
        "hora_fato": bo.get("hora_fato"),
        "cidade": bo.get("cidade"),
        "uf": bo.get("uf"),
        "bairro": bo.get("bairro"),
        "endereco": bo.get("endereco"),
        "narrativa": bo.get("narrativa") or "",
        "partes": partes,
        "objetos": objetos,
        "pendencias": pendencias,
        "raciocinio_cot": bo.get("raciocinio_cot") or "",
        "passos": passos,
    }


def _classificar_tipo(texto: str) -> tuple[str, str]:
    t = texto.lower()
    arma = any(p in t for p in ["arma", "revolver", "pistola", "faca"])
    violencia = any(p in t for p in ["ameac", "forca", "agred", "violencia", "roub"])
    subtracao = any(p in t for p in ["levou", "subtraiu", "furt", "roub", "celular", "carteira"])
    if subtracao and violencia:
        artigo = "Art. 157 do CP"
        if arma:
            artigo += " - majorado pelo emprego de arma"
        return "Roubo majorado" if arma else "Roubo", artigo
    if subtracao:
        return "Furto", "Art. 155 do CP"
    if any(p in t for p in ["agred", "lesao", "ferimento", "soco"]):
        return "Lesao corporal", "Art. 129 do CP"
    if any(p in t for p in ["ameac", "prometeu matar", "intimid"]):
        return "Ameaca", "Art. 147 do CP"
    return "Fato atípico ou a classificar", None


def _extrair_objetos(texto: str) -> list[dict[str, str]]:
    candidatos = []
    mapa = {
        "celular": "Aparelho celular",
        "telefone": "Aparelho celular",
        "carteira": "Carteira",
        "dinheiro": "Dinheiro",
        "moto": "Motocicleta",
        "carro": "Veículo",
        "bicicleta": "Bicicleta",
        "notebook": "Notebook",
    }
    baixo = texto.lower()
    for chave, descricao in mapa.items():
        if chave in baixo and descricao not in candidatos:
            candidatos.append(descricao)
    return [{"descricao": item, "status": "subtraido"} for item in candidatos]


def _inferir_local(texto: str) -> dict[str, str | None]:
    cidade = None
    uf = None
    bairro = None
    endereco = None

    padroes_cidade = {
        "sao paulo": ("Sao Paulo", "SP"),
        "são paulo": ("Sao Paulo", "SP"),
        "rio de janeiro": ("Rio de Janeiro", "RJ"),
        "belo horizonte": ("Belo Horizonte", "MG"),
    }
    baixo = texto.lower()
    for chave, valor in padroes_cidade.items():
        if chave in baixo:
            cidade, uf = valor
            break

    match_end = re.search(r"(?:na|no|em)\s+((?:rua|avenida|av\.|r\.)[^,.]+)", texto, re.I)
    if match_end:
        endereco = match_end.group(1).strip()

    match_bairro = re.search(r"bairro\s+([A-Za-zÀ-ÿ\s]+?)(?:[,.]|$)", texto, re.I)
    if match_bairro:
        bairro = match_bairro.group(1).strip()

    return {"cidade": cidade, "uf": uf, "bairro": bairro, "endereco": endereco}


def _gerar_bo_local(resumo: str) -> dict[str, Any]:
    tipo, artigo = _classificar_tipo(resumo)
    local = _inferir_local(resumo)
    pendencias = []
    if not local.get("cidade"):
        pendencias.append("Cidade não informada.")
    if not local.get("endereco"):
        pendencias.append("Endereço exato não informado.")
    if "arma" in resumo.lower() and not any(p in resumo.lower() for p in ["calibre", "revolver", "pistola"]):
        pendencias.append("Características da arma não detalhadas.")

    bo = {
        "tipo_penal": tipo,
        "artigo_penal": artigo,
        "data_fato": None,
        "hora_fato": None,
        **local,
        "narrativa": (
            "Conforme relato apresentado, registra-se a ocorrencia nos seguintes termos: "
            + resumo.strip()
        ),
        "partes": [
            {
                "papel": "vitima",
                "nome": "Não informado",
                "documento": None,
                "descricao": "Dados qualificativos pendentes de complementacao.",
            }
        ],
        "objetos": _extrair_objetos(resumo),
        "pendencias": pendencias,
        "raciocinio_cot": (
            "1) O relato foi analisado quanto a subtracao, violencia e ameaca. "
            "2) A classificacao penal foi inferida por palavras-chave. "
            f"3) Resultado preliminar: {tipo}."
        ),
        "passos": [
            {
                "thought": "Analisar relato livre e identificar elementos juridicos essenciais.",
                "action": "gerar_bo_local",
                "observation": f"Classificacao preliminar: {tipo}.",
                "final_answer": "BO estruturado em modo local de contingencia.",
            }
        ],
    }
    return _normalizar_bo(bo)


def gerar_bo(resumo: str) -> dict[str, Any]:
    """Gera um BO estruturado a partir de um relato livre."""
    if not resumo.strip():
        raise ValueError("Resumo da ocorrencia nao pode estar vazio")

    if not _tem_openai():
        return _gerar_bo_local(resumo)

    prompt = f"""
Voce e um assistente para lavratura de boletins de ocorrencia no Brasil.
Transforme o relato em JSON valido, sem markdown, com as chaves:
tipo_penal, artigo_penal, data_fato, hora_fato, cidade, uf, bairro, endereco,
narrativa, partes, objetos, pendencias, raciocinio_cot.
partes deve conter papel, nome, documento, descricao.
objetos deve conter descricao e status.
Use null quando nao houver dado.

Relato:
{resumo}
"""
    try:
        dados = _extrair_json(chamar_modelo_geracao(prompt))
        dados["passos"] = [
            {
                "thought": "Interpretar relato e estruturar campos do BO.",
                "action": "gerar_bo_ia",
                "observation": "JSON retornado e normalizado.",
                "final_answer": "BO gerado.",
            }
        ]
        return _normalizar_bo(dados)
    except Exception as exc:
        logger.warning(
            "Modo local de contingencia ativado na geracao de BO: %s.",
            _motivo_falha_openai(exc),
        )
        bo = _gerar_bo_local(resumo)
        bo["pendencias"].append("IA indisponivel no momento. Utilizando modo local de contingencia.")
        return bo


def _periodo_para_data(pergunta: str) -> date | None:
    t = pergunta.lower()
    match = re.search(r"(\d+)\s+dias", t)
    if match:
        return date.today() - timedelta(days=int(match.group(1)))
    if "mes" in t or "mês" in t or "30 dias" in t:
        return date.today() - timedelta(days=30)
    if "semana" in t or "7 dias" in t:
        return date.today() - timedelta(days=7)
    return None


def _filtrar_bos(bos: list[dict[str, Any]], pergunta: str) -> list[dict[str, Any]]:
    t = pergunta.lower()
    inicio = _periodo_para_data(pergunta)
    saida = []
    for bo in bos:
        if inicio and bo.get("data_fato"):
            try:
                if datetime.fromisoformat(str(bo["data_fato"])).date() < inicio:
                    continue
            except ValueError:
                pass
        tipo = (bo.get("tipo_penal") or "").lower()
        cidade = (bo.get("cidade") or "").lower()
        if "furto" in t and "furto" not in tipo:
            continue
        if "roubo" in t and "roubo" not in tipo:
            continue
        if "sao paulo" in t or "são paulo" in t:
            if "sao paulo" not in cidade and "são paulo" not in cidade:
                continue
        if "belo horizonte" in t or " bh" in f" {t}":
            if "belo horizonte" not in cidade:
                continue
        if "rio" in t and "rio de janeiro" not in cidade:
            continue
        saida.append(bo)
    return saida


def consultar_base(pergunta: str) -> dict[str, Any]:
    """Consulta a base de BOs em linguagem natural com agregacoes simples."""
    if not pergunta.strip():
        raise ValueError("Pergunta nao pode estar vazia")

    try:
        from db.repositorio import listar_bos

        bos = _filtrar_bos(listar_bos(), pergunta)
        erro = None
    except Exception:
        logger.exception("Falha ao consultar a base de BOs.")
        bos = []
        erro = True

    t = pergunta.lower()
    sql = "SELECT * FROM boletins ORDER BY criado_em DESC;"
    resultados: list[dict[str, Any]]

    if "bairro" in t or "top" in t or "perigos" in t:
        contagem = Counter((bo.get("bairro") or "Não informado") for bo in bos)
        resultados = [{"bairro": bairro, "total": total} for bairro, total in contagem.most_common(5)]
        sql = "SELECT bairro, COUNT(*) AS total FROM boletins GROUP BY bairro ORDER BY total DESC LIMIT 5;"
    elif "compare" in t or "compar" in t:
        contagem = Counter((bo.get("tipo_penal") or "Não informado") for bo in bos)
        resultados = [{"tipo_penal": tipo, "total": total} for tipo, total in contagem.most_common()]
        sql = "SELECT tipo_penal, COUNT(*) AS total FROM boletins GROUP BY tipo_penal ORDER BY total DESC;"
    else:
        resultados = [{"total": len(bos)}]
        sql = "SELECT COUNT(*) AS total FROM boletins;"

    if erro:
        resposta = "Base de dados indisponivel no momento. Tente novamente em instantes."
    elif not bos:
        resposta = "Nenhum BO encontrado para os filtros informados."
    elif "bairro" in t or "top" in t or "perigos" in t:
        lider = resultados[0]
        resposta = f"Foram encontrados {len(bos)} BOs. Maior concentracao: {lider['bairro']} ({lider['total']} casos)."
    else:
        resposta = f"Foram encontrados {len(bos)} BOs para a consulta."

    return {
        "sql_gerado": sql,
        "resultados": resultados,
        "resposta_natural": resposta,
        "passos": [
            {
                "thought": "Interpretar pergunta e aplicar filtros/agrupamentos seguros em Python.",
                "action": "consultar_base",
                "observation": f"{len(resultados)} linhas de resultado.",
                "final_answer": resposta,
            }
        ],
    }


def _dias_periodo(periodo: str) -> int:
    match = re.search(r"(\d+)", periodo)
    return int(match.group(1)) if match else 30


def gerar_relatorio(cidade: str, periodo: str) -> dict[str, Any]:
    """Gera relatorio executivo em Markdown a partir da base de BOs."""
    try:
        from db.repositorio import listar_bos

        bos = listar_bos()
        erro = None
    except Exception:
        logger.exception("Falha ao carregar BOs para relatorio.")
        bos = []
        erro = True

    dias = _dias_periodo(periodo)
    inicio = date.today() - timedelta(days=dias)
    filtrados = []
    for bo in bos:
        if cidade not in ("Todas", "All") and (bo.get("cidade") or "").lower() != cidade.lower():
            continue
        try:
            data_bo = datetime.fromisoformat(str(bo.get("data_fato"))).date()
            if data_bo < inicio:
                continue
        except (TypeError, ValueError):
            pass
        filtrados.append(bo)

    por_tipo = Counter((bo.get("tipo_penal") or "Não informado") for bo in filtrados)
    por_bairro = Counter((bo.get("bairro") or "Não informado") for bo in filtrados)

    linhas_tipo = "\n".join(f"| {tipo} | {total} |" for tipo, total in por_tipo.most_common()) or "| Não informado | 0 |"
    linhas_bairro = "\n".join(f"| {bairro} | {total} |" for bairro, total in por_bairro.most_common(10)) or "| Não informado | 0 |"
    obs = "\n\n> Aviso: base de dados indisponivel. Relatorio gerado sem dados reais." if erro else ""

    relatorio = f"""# Relatorio Executivo de Criminalidade

## Escopo

- Cidade: {cidade}
- Periodo: ultimos {dias} dias
- Total de BOs analisados: {len(filtrados)}

## Incidencia por tipo penal

| Tipo penal | Ocorrencias |
|---|---:|
{linhas_tipo}

## Concentracao por bairro

| Bairro | Ocorrencias |
|---|---:|
{linhas_bairro}

## Leitura operacional

Os dados indicam os tipos penais e territorios com maior concentracao no periodo.
Priorize patrulhamento preventivo nos bairros de maior incidencia e revise os BOs
com pendencias para melhorar a qualidade da inteligencia.
{obs}
"""

    if _tem_openai() and filtrados:
        try:
            prompt = (
                "Escreva uma analise executiva curta em portugues, com recomendacoes, "
                f"baseada neste resumo JSON: {json.dumps({'tipos': por_tipo, 'bairros': por_bairro}, default=str)}"
            )
            analise = chamar_modelo(prompt)
            relatorio += f"\n## Analise gerada por IA\n\n{analise}\n"
        except Exception as exc:
            logger.warning(
                "Analise executiva por IA ignorada: %s.",
                _motivo_falha_openai(exc),
            )

    return {
        "relatorio_markdown": relatorio,
        "passos": [
            {
                "thought": "Decompor relatorio em escopo, incidencia, territorio e recomendacoes.",
                "action": "gerar_relatorio",
                "observation": f"{len(filtrados)} BOs analisados.",
                "final_answer": "Relatorio executivo gerado.",
            }
        ],
    }
