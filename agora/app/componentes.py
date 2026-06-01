"""Componentes reutilizaveis da interface Streamlit."""

from datetime import datetime
import unicodedata

import streamlit as st

from app.i18n import t

NAO_INFORMADO = "Não informado"

_ICONE_PAPEL = {
    "vitima": "Pessoa",
    "suspeito": "Suspeito",
    "testemunha": "Testemunha",
}

_COR_STATUS = {
    "subtraido": "#CF222E",
    "recuperado": "#1A7F37",
    "apreendido": "#9A6700",
    "danificado": "#6E40C9",
}


def _chave_amigavel(valor: object, prefixo: str = "") -> str:
    texto = str(valor or "").strip()
    if prefixo and texto.lower().startswith(prefixo):
        texto = texto[len(prefixo):]
    texto = texto.strip(" _-")
    texto_sem_acento = unicodedata.normalize("NFKD", texto)
    texto_sem_acento = "".join(ch for ch in texto_sem_acento if not unicodedata.combining(ch))
    return texto_sem_acento.lower().replace(" ", "_").replace("-", "_")


def _rotulo_papel(papel: object, idioma: str) -> str:
    chave = _chave_amigavel(papel, "papel_")
    if not chave:
        return NAO_INFORMADO

    rotulos = {
        "vitima": t("papel_vitima", idioma),
        "suspeito": t("papel_suspeito", idioma),
        "testemunha": t("papel_testemunha", idioma),
    }
    return rotulos.get(chave, str(papel).replace("papel_", "").replace("Papel_", "").strip().title())


def _rotulo_status(status: object, idioma: str) -> str:
    chave = _chave_amigavel(status, "status_")
    if not chave:
        return NAO_INFORMADO

    rotulos = {
        "subtraido": t("status_subtraido", idioma),
        "recuperado": t("status_recuperado", idioma),
        "apreendido": t("status_apreendido", idioma),
        "danificado": t("status_danificado", idioma),
    }
    return rotulos.get(chave, str(status).replace("status_", "").replace("Status_", "").strip().title())


def _formatar_hora(valor: object) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return ""
    partes = texto.split(":")
    if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit():
        return f"{int(partes[0]):02d}h{int(partes[1]):02d}"
    return texto


def _formatar_data(valor: object) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return ""
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        return texto


def _formatar_data_e_hora(data: object, hora: object) -> str:
    data_formatada = _formatar_data(data)
    hora_formatada = _formatar_hora(hora)
    if data_formatada and hora_formatada:
        return f"{data_formatada} às {hora_formatada}"
    return data_formatada or hora_formatada or NAO_INFORMADO


def exibir_bo(bo: dict, idioma: str = "pt") -> None:
    """Renderiza um BO formatado em secoes organizadas."""
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        with st.container(border=True):
            st.caption("Tipo penal")
            st.markdown(f"### {bo.get('tipo_penal') or NAO_INFORMADO}")
            st.caption(f"Enquadramento: {bo.get('artigo_penal') or NAO_INFORMADO}")
    with col2:
        with st.container(border=True):
            st.caption("Data e hora")
            st.markdown(f"**{_formatar_data_e_hora(bo.get('data_fato'), bo.get('hora_fato'))}**")
    with col3:
        local = ", ".join(filter(None, [bo.get("bairro"), bo.get("cidade"), bo.get("uf")]))
        with st.container(border=True):
            st.caption("Localidade")
            st.markdown(f"**{local or NAO_INFORMADO}**")

    st.divider()

    st.markdown(f"**{t('narrativa_titulo', idioma)}**")
    st.info(bo.get("narrativa") or NAO_INFORMADO)

    st.caption(f"Endereço informado: {bo.get('endereco') or NAO_INFORMADO}")

    pendencias = bo.get("pendencias") or []
    if isinstance(pendencias, str):
        pendencias = [pendencias] if pendencias else []
    if pendencias:
        st.warning(f"**{t('pendencias_titulo', idioma)}**\n\n" + "\n".join(f"- {p}" for p in pendencias))

    st.divider()

    partes = bo.get("partes", [])
    if partes:
        st.markdown(f"**{t('partes_titulo', idioma)}**")
        for parte in partes:
            papel = parte.get("papel", "")
            papel_chave = _chave_amigavel(papel, "papel_")
            icone = _ICONE_PAPEL.get(papel_chave, "Pessoa")
            papel_label = _rotulo_papel(papel, idioma)
            nome = parte.get("nome") or NAO_INFORMADO
            titulo = f"{papel_label} — {nome}" if nome != NAO_INFORMADO else f"{icone} — {papel_label}"
            with st.expander(titulo):
                st.write(f"**Documento:** {parte.get('documento') or NAO_INFORMADO}")
                st.write(parte.get("descricao") or NAO_INFORMADO)
    else:
        st.markdown(f"**{t('partes_titulo', idioma)}**")
        st.info(NAO_INFORMADO)

    objetos = bo.get("objetos", [])
    if objetos:
        st.markdown(f"**{t('objetos_titulo', idioma)}**")
        for obj in objetos:
            status = obj.get("status", "")
            status_chave = _chave_amigavel(status, "status_")
            cor = _COR_STATUS.get(status_chave, "#666")
            status_label = _rotulo_status(status, idioma)
            descricao = obj.get("descricao") or NAO_INFORMADO
            st.markdown(
                f"<span style='color:{cor}'>●</span> {descricao} — {status_label}",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(f"**{t('objetos_titulo', idioma)}**")
        st.info(NAO_INFORMADO)


def exibir_passos_agente(passos: list) -> None:
    """Renderiza os passos Thought/Action/Observation do agente."""
    if not passos:
        st.caption("Nenhum passo intermediário registrado.")
        return

    for i, passo in enumerate(passos, 1):
        thought = passo.get("thought", "")
        action = passo.get("action", "")
        observation = passo.get("observation", "")
        final = passo.get("final_answer", "")

        with st.expander(f"Etapa {i} | {action or 'Raciocínio'}"):
            if thought:
                st.markdown("**Thought**")
                st.markdown(f"> {thought}")
            if action:
                st.markdown("**Action**")
                st.code(action, language="text")
            if observation:
                st.markdown("**Observation**")
                st.markdown(observation)
            if final:
                st.markdown("**Final Answer**")
                st.success(final)
