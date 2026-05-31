"""Nucleo simples de orquestracao do agente AGORA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agente.ferramentas import consultar_base, gerar_bo, gerar_relatorio


@dataclass
class AgenteAgora:
    """Despachante de intencoes para as ferramentas do projeto."""

    def executar(self, comando: str, **kwargs: Any) -> Any:
        comando_normalizado = comando.strip().lower()
        if comando_normalizado in {"gerar_bo", "lavrar_bo"}:
            return gerar_bo(kwargs.get("resumo") or kwargs.get("texto") or "")
        if comando_normalizado in {"consultar_base", "consultar"}:
            return consultar_base(kwargs.get("pergunta") or kwargs.get("texto") or "")
        if comando_normalizado in {"gerar_relatorio", "relatorio"}:
            return gerar_relatorio(kwargs.get("cidade", "Todas"), kwargs.get("periodo", "Ultimos 30 dias"))
        raise ValueError(f"Comando desconhecido: {comando}")
