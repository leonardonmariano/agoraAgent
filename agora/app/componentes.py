"""Componentes reutilizaveis da interface Streamlit."""

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


def exibir_bo(bo: dict, idioma: str = "pt") -> None:
    """Renderiza um BO formatado em secoes organizadas."""
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### {bo.get('tipo_penal') or NAO_INFORMADO}")
        st.caption(f"Enquadramento: {bo.get('artigo_penal') or NAO_INFORMADO}")
    with col2:
        data = bo.get("data_fato") or NAO_INFORMADO
        hora = bo.get("hora_fato") or NAO_INFORMADO
        st.metric("Data e hora", f"{data}  {hora}")
    with col3:
        local = ", ".join(filter(None, [bo.get("bairro"), bo.get("cidade"), bo.get("uf")]))
        st.metric("Localidade", local or NAO_INFORMADO)

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
            icone = _ICONE_PAPEL.get(papel, "Pessoa")
            papel_label = t(f"papel_{papel}", idioma) if papel else NAO_INFORMADO
            nome = parte.get("nome") or NAO_INFORMADO
            with st.expander(f"{icone} | {papel_label} | {nome}"):
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
            cor = _COR_STATUS.get(status, "#666")
            status_label = t(f"status_{status}", idioma) if status else NAO_INFORMADO
            descricao = obj.get("descricao") or NAO_INFORMADO
            st.markdown(
                f"<span style='color:{cor}'>●</span> {descricao} "
                f"<span style='font-size:0.8em;color:{cor}'>({status_label})</span>",
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
