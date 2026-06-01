"""Geracao de PDF para boletins de ocorrencia."""

from __future__ import annotations

from io import BytesIO
import re
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


NAO_INFORMADO = "Não informado"


def _texto(valor: Any, padrao: str = NAO_INFORMADO) -> str:
    texto = str(valor or "").strip()
    return texto or padrao


def _rotulo(valor: Any, prefixo: str = "") -> str:
    texto = _texto(valor, "")
    if prefixo and texto.lower().startswith(prefixo):
        texto = texto[len(prefixo):]
    texto = texto.replace("_", " ").replace("-", " ").strip()
    rotulos = {
        "vitima": "Vítima",
        "vítima": "Vítima",
        "suspeito": "Suspeito",
        "testemunha": "Testemunha",
        "subtraido": "Subtraído",
        "subtraído": "Subtraído",
        "recuperado": "Recuperado",
        "apreendido": "Apreendido",
        "danificado": "Danificado",
    }
    return rotulos.get(texto.lower(), texto.title() if texto else NAO_INFORMADO)


def _formatar_hora(valor: Any) -> str:
    texto = _texto(valor, "")
    partes = texto.split(":")
    if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit():
        return f"{int(partes[0]):02d}h{int(partes[1]):02d}"
    return texto


def _formatar_data(valor: Any) -> str:
    texto = _texto(valor, "")
    if not texto:
        return ""
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        return texto


def _formatar_data_hora(data: Any, hora: Any) -> str:
    data_formatada = _formatar_data(data)
    hora_formatada = _formatar_hora(hora)
    if data_formatada and hora_formatada:
        return f"{data_formatada} às {hora_formatada}"
    return data_formatada or hora_formatada or NAO_INFORMADO


def nome_arquivo_pdf(bo: dict[str, Any]) -> str:
    numero = _texto(bo.get("numero"), "boletim")
    seguro = re.sub(r"[^A-Za-z0-9_-]+", "_", numero).strip("_").lower()
    return f"{seguro or 'boletim'}_ocorrencia.pdf"


def _criar_estilos() -> dict[str, ParagraphStyle]:
    estilos = getSampleStyleSheet()
    estilos.add(
        ParagraphStyle(
            name="LogoAgora",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F4E79"),
            spaceAfter=4,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="TituloDocumento",
            parent=estilos["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#222222"),
            spaceAfter=12,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="Secao",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1F4E79"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="Corpo",
            parent=estilos["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=6,
        )
    )
    return estilos


def _p(texto: Any, estilo: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_texto(texto)).replace("\n", "<br/>"), estilo)


def _tabela(dados: list[list[Any]], larguras: list[float]) -> Table:
    estilo_header = ParagraphStyle(
        name="CelulaHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1F4E79"),
    )
    estilo_corpo = ParagraphStyle(name="CelulaCorpo", fontName="Helvetica", fontSize=8, leading=10)
    dados_formatados = []
    for linha_idx, linha in enumerate(dados):
        estilo = estilo_header if linha_idx == 0 else estilo_corpo
        dados_formatados.append([Paragraph(escape(_texto(celula)), estilo) for celula in linha])

    tabela = Table(dados_formatados, colWidths=larguras, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF1F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B8C4CE")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tabela


def _rodape(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    largura, _ = A4
    canvas.drawString(2 * cm, 1.2 * cm, "Documento gerado automaticamente pelo sistema ÁGORA.")
    canvas.drawRightString(largura - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


def gerar_pdf_bo(bo: dict[str, Any]) -> bytes:
    """Gera um PDF A4 profissional para o boletim informado."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title="Boletim de Ocorrência",
        author="ÁGORA",
    )
    estilos = _criar_estilos()
    largura_util = A4[0] - doc.leftMargin - doc.rightMargin

    historia = [
        Paragraph("ÁGORA", estilos["LogoAgora"]),
        Paragraph("Boletim de Ocorrência", estilos["TituloDocumento"]),
    ]

    localidade = ", ".join(filter(None, [bo.get("bairro"), bo.get("cidade"), bo.get("uf")])) or NAO_INFORMADO
    resumo = [
        ["Número do BO", _texto(bo.get("numero"), "Pendente de salvamento")],
        ["Tipo penal", _texto(bo.get("tipo_penal"))],
        ["Enquadramento jurídico", _texto(bo.get("artigo_penal"))],
        ["Data e hora", _formatar_data_hora(bo.get("data_fato"), bo.get("hora_fato"))],
        ["Localidade", localidade],
    ]
    historia.append(_tabela(resumo, [4.2 * cm, largura_util - 4.2 * cm]))
    historia.append(Spacer(1, 8))

    historia.append(Paragraph("Narrativa Oficial", estilos["Secao"]))
    historia.append(_p(bo.get("narrativa"), estilos["Corpo"]))

    historia.append(Paragraph("Partes Envolvidas", estilos["Secao"]))
    partes = bo.get("partes") if isinstance(bo.get("partes"), list) else []
    dados_partes = [["Papel", "Nome", "Documento", "Descrição"]]
    if partes:
        for parte in partes:
            if isinstance(parte, dict):
                dados_partes.append(
                    [
                        _rotulo(parte.get("papel"), "papel_"),
                        _texto(parte.get("nome")),
                        _texto(parte.get("documento")),
                        _texto(parte.get("descricao")),
                    ]
                )
    else:
        dados_partes.append([NAO_INFORMADO, NAO_INFORMADO, NAO_INFORMADO, NAO_INFORMADO])
    historia.append(_tabela(dados_partes, [3 * cm, 4 * cm, 3.5 * cm, largura_util - 10.5 * cm]))

    historia.append(Paragraph("Objetos Envolvidos", estilos["Secao"]))
    objetos = bo.get("objetos") if isinstance(bo.get("objetos"), list) else []
    dados_objetos = [["Descrição", "Status"]]
    if objetos:
        for objeto in objetos:
            if isinstance(objeto, dict):
                dados_objetos.append([_texto(objeto.get("descricao")), _rotulo(objeto.get("status"), "status_")])
    else:
        dados_objetos.append([NAO_INFORMADO, NAO_INFORMADO])
    historia.append(_tabela(dados_objetos, [largura_util - 4 * cm, 4 * cm]))

    historia.append(Paragraph("Análise de Classificação", estilos["Secao"]))
    historia.append(_p(bo.get("raciocinio_cot"), estilos["Corpo"]))

    doc.build(historia, onFirstPage=_rodape, onLaterPages=_rodape)
    return buffer.getvalue()
