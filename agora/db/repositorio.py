"""Repositorio Supabase para boletins de ocorrencia."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any
from uuid import uuid4

from db.conexao import request


def _lista(valor: Any) -> list:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    if isinstance(valor, tuple):
        return list(valor)
    return [valor]


def _limpar_dict(dados: dict[str, Any]) -> dict[str, Any]:
    return {chave: valor for chave, valor in dados.items() if valor is not None}


def gerar_numero_bo() -> str:
    """Gera um numero amigavel e unico para o BO."""
    return f"BO-{date.today():%Y%m%d}-{uuid4().hex[:8].upper()}"


def salvar_bo(bo: dict[str, Any]) -> str:
    """Salva um BO e seus relacionamentos no Supabase.

    Retorna o numero gerado do boletim.
    """
    numero = bo.get("numero") or gerar_numero_bo()

    payload = _limpar_dict(
        {
            "numero": numero,
            "tipo_penal": bo.get("tipo_penal") or "Nao classificado",
            "artigo_penal": bo.get("artigo_penal"),
            "data_fato": bo.get("data_fato"),
            "hora_fato": bo.get("hora_fato"),
            "cidade": bo.get("cidade"),
            "uf": bo.get("uf"),
            "bairro": bo.get("bairro"),
            "endereco": bo.get("endereco"),
            "narrativa": bo.get("narrativa") or "",
            "pendencias": _lista(bo.get("pendencias")),
            "raciocinio_cot": bo.get("raciocinio_cot"),
            "passos": _lista(bo.get("passos")),
        }
    )

    resposta = request("POST", "boletins", json=payload, prefer="return=representation")
    data = resposta.json()
    if not data:
        raise RuntimeError("Supabase nao retornou o boletim inserido")
    boletim_id = data[0]["id"]

    partes = []
    for parte in _lista(bo.get("partes")):
        if isinstance(parte, dict):
            partes.append(
                _limpar_dict(
                    {
                        "boletim_id": boletim_id,
                        "papel": parte.get("papel") or "nao_informado",
                        "nome": parte.get("nome"),
                        "documento": parte.get("documento"),
                        "descricao": parte.get("descricao"),
                    }
                )
            )
    if partes:
        request("POST", "partes", json=partes)

    objetos = []
    for objeto in _lista(bo.get("objetos")):
        if isinstance(objeto, dict) and objeto.get("descricao"):
            objetos.append(
                _limpar_dict(
                    {
                        "boletim_id": boletim_id,
                        "descricao": objeto.get("descricao"),
                        "status": objeto.get("status") or "informado",
                    }
                )
            )
    if objetos:
        request("POST", "objetos", json=objetos)

    return numero


def contar_bos() -> int:
    """Retorna o total de boletins salvos."""
    resposta = db_select_boletins(limite=1, contar=True)
    return int(resposta.get("count") or 0)


def db_select_boletins(limite: int = 1000, contar: bool = False) -> dict[str, Any]:
    prefer = "count=exact" if contar else None
    resposta = request(
        "GET",
        "boletins",
        params={"select": "*", "order": "criado_em.desc", "limit": limite},
        prefer=prefer,
    )
    count = None
    content_range = resposta.headers.get("content-range") or resposta.headers.get("Content-Range")
    if content_range and "/" in content_range:
        total = content_range.rsplit("/", 1)[-1]
        count = int(total) if total.isdigit() else None
    return {"data": resposta.json(), "count": count}


def listar_bos(limite: int = 1000) -> list[dict[str, Any]]:
    """Lista BOs com partes e objetos agregados."""
    boletins = db_select_boletins(limite=limite)["data"]
    if not boletins:
        return []

    ids = [item["id"] for item in boletins]
    filtro_ids = f"in.({','.join(ids)})"
    partes = request("GET", "partes", params={"select": "*", "boletim_id": filtro_ids}).json()
    objetos = request("GET", "objetos", params={"select": "*", "boletim_id": filtro_ids}).json()

    partes_por_bo = defaultdict(list)
    for parte in partes:
        partes_por_bo[parte["boletim_id"]].append(
            {
                "papel": parte.get("papel"),
                "nome": parte.get("nome"),
                "documento": parte.get("documento"),
                "descricao": parte.get("descricao"),
            }
        )

    objetos_por_bo = defaultdict(list)
    for objeto in objetos:
        objetos_por_bo[objeto["boletim_id"]].append(
            {
                "descricao": objeto.get("descricao"),
                "status": objeto.get("status"),
            }
        )

    for boletim in boletins:
        boletim["partes"] = partes_por_bo.get(boletim["id"], [])
        boletim["objetos"] = objetos_por_bo.get(boletim["id"], [])
    return boletins


def apagar_todos() -> None:
    """Remove todos os registros das tabelas do projeto."""
    filtro = {"id": "neq.00000000-0000-0000-0000-000000000000"}
    request("DELETE", "objetos", params=filtro)
    request("DELETE", "partes", params=filtro)
    request("DELETE", "boletins", params=filtro)
