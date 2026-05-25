"""Componentes reutilizáveis da interface Streamlit."""

import streamlit as st

from i18n import t

_ICONE_PAPEL = {
    "vitima": "🧑",
    "suspeito": "🚨",
    "testemunha": "👁️",
}

_COR_STATUS = {
    "subtraido": "#CF222E",
    "recuperado": "#1A7F37",
    "apreendido": "#9A6700",
    "danificado": "#6E40C9",
}


def exibir_bo(bo: dict, idioma: str = "pt") -> None:
    """Renderiza um BO formatado em seções organizadas."""
    # Cabeçalho com classificação penal
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### {bo.get('tipo_penal', '—')}")
        if artigo := bo.get("artigo_penal"):
            st.caption(artigo)
    with col2:
        data = bo.get("data_fato") or "—"
        hora = bo.get("hora_fato") or "—"
        st.metric("Data / Hora", f"{data}  {hora}")
    with col3:
        local = ", ".join(filter(None, [bo.get("bairro"), bo.get("cidade"), bo.get("uf")]))
        st.metric("Local", local or "—")

    st.divider()

    # Narrativa em destaque
    st.markdown(f"**{t('narrativa_titulo', idioma)}**")
    st.info(bo.get("narrativa", "—"))

    # Endereço completo
    if endereco := bo.get("endereco"):
        st.caption(f"Endereço: {endereco}")

    # Pendências
    pendencias = bo.get("pendencias") or []
    if isinstance(pendencias, str):
        pendencias = [pendencias] if pendencias else []
    if pendencias:
        st.warning(f"**{t('pendencias_titulo', idioma)}**\n\n" + "\n".join(f"- {p}" for p in pendencias))

    st.divider()

    # Partes envolvidas
    partes = bo.get("partes", [])
    if partes:
        st.markdown(f"**{t('partes_titulo', idioma)}**")
        for parte in partes:
            papel = parte.get("papel", "")
            icone = _ICONE_PAPEL.get(papel, "👤")
            papel_label = t(f"papel_{papel}", idioma) if papel else papel
            with st.expander(f"{icone} {papel_label} — {parte.get('nome') or 'Não identificado'}"):
                if doc := parte.get("documento"):
                    st.write(f"**Documento:** {doc}")
                if desc := parte.get("descricao"):
                    st.write(desc)

    # Objetos envolvidos
    objetos = bo.get("objetos", [])
    if objetos:
        st.markdown(f"**{t('objetos_titulo', idioma)}**")
        for obj in objetos:
            status = obj.get("status", "")
            cor = _COR_STATUS.get(status, "#666")
            status_label = t(f"status_{status}", idioma) if status else status
            st.markdown(
                f"<span style='color:{cor}'>●</span> {obj.get('descricao', '—')} "
                f"<span style='font-size:0.8em;color:{cor}'>({status_label})</span>",
                unsafe_allow_html=True,
            )


def exibir_passos_agente(passos: list) -> None:
    """Renderiza os passos Thought/Action/Observation do agente ReAct."""
    if not passos:
        st.caption("Nenhum passo intermediário registrado.")
        return

    for i, passo in enumerate(passos, 1):
        thought = passo.get("thought", "")
        action = passo.get("action", "")
        observation = passo.get("observation", "")
        final = passo.get("final_answer", "")

        with st.expander(f"Passo {i} — {action or 'Raciocínio'}"):
            if thought:
                st.markdown("🤔 **Thought**")
                st.markdown(f"> {thought}")
            if action:
                st.markdown("🔧 **Action**")
                st.code(action, language="text")
            if observation:
                st.markdown("👁️ **Observation**")
                st.markdown(observation)
            if final:
                st.markdown("✅ **Final Answer**")
                st.success(final)
