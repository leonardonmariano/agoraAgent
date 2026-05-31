"""Interface principal do ÁGORA — entrada do Streamlit."""

import streamlit as st

st.set_page_config(
    page_title="ÁGORA — Segurança Pública",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from componentes import exibir_bo, exibir_passos_agente
from i18n import t

# ── Dados de demonstração ────────────────────────────────────────────────────

_BO_DEMO = {
    "tipo_penal": "Roubo Majorado (Emprego de Arma de Fogo)",
    "artigo_penal": "Art. 157, § 2º, I do CP",
    "data_fato": "2026-05-05",
    "hora_fato": "22:30",
    "cidade": "São Paulo",
    "uf": "SP",
    "bairro": "Bela Vista",
    "endereco": "Av. Paulista, altura do nº 1578",
    "narrativa": (
        "Na data e hora supracitadas, a vítima trafegava pela Av. Paulista quando dois indivíduos, "
        "em motocicleta de cor preta, emparelharam-se ao seu veículo. O condutor manteve o motor em "
        "funcionamento enquanto o carona exibiu arma de fogo e, mediante grave ameaça, exigiu a entrega "
        "do aparelho celular e da carteira. A vítima cedeu aos objetos e os suspeitos evadiram-se em "
        "direção à Rua da Consolação. O Corpo de Bombeiros foi acionado e não houve feridos."
    ),
    "partes": [
        {
            "papel": "vitima",
            "nome": "João Silva",
            "documento": "CPF 123.456.789-00",
            "descricao": "Homem, 34 anos, motorista de aplicativo.",
        },
        {
            "papel": "suspeito",
            "nome": "Não identificado",
            "documento": None,
            "descricao": "Dois indivíduos em motocicleta preta, capacetes escuros. Carona portava arma de fogo.",
        },
    ],
    "objetos": [
        {"descricao": "Aparelho celular iPhone 14 Pro, cor prata", "status": "subtraido"},
        {"descricao": "Carteira de couro marrom com R$ 150,00 e documentos", "status": "subtraido"},
    ],
    "pendencias": [
        "Placa da motocicleta não informada — solicitar imagens de câmeras de segurança",
        "Marca/calibre da arma não especificados",
    ],
    "raciocinio_cot": (
        "1) Houve subtração? Sim — celular e carteira foram levados.\n"
        "2) Houve violência ou grave ameaça? Sim — arma de fogo exibida.\n"
        "3) Emprego de arma? Sim — configura majorante do § 2º, I.\n"
        "4) Concurso de agentes? Sim — dois suspeitos — configura majorante do § 2º, II.\n"
        "Conclusão: Roubo Majorado, enquadramento no Art. 157, § 2º, I e II do CP."
    ),
}

_PASSOS_DEMO = [
    {
        "thought": "O usuário quer gerar um BO a partir de um relato de roubo. Devo usar a ferramenta gerar_bo.",
        "action": "gerar_bo",
        "observation": "BO gerado com sucesso. Tipo penal identificado: Roubo Majorado.",
    },
    {
        "thought": "Agora preciso validar o BO gerado usando a Chain of Verification.",
        "action": "validar_bo",
        "observation": "Validação concluída. 2 pendências identificadas (placa e calibre da arma).",
        "final_answer": "BO estruturado e validado com sucesso. Duas pendências registradas para investigação.",
    },
]

_CONSULTA_DEMO = {
    "sql_gerado": (
        "SELECT bairro, COUNT(*) AS total\n"
        "FROM boletins\n"
        "WHERE cidade = 'São Paulo'\n"
        "  AND tipo_penal ILIKE '%furto%'\n"
        "  AND data_fato >= NOW() - INTERVAL '30 days'\n"
        "GROUP BY bairro\n"
        "HAVING COUNT(*) > 5\n"
        "ORDER BY total DESC;"
    ),
    "resultados": [
        {"bairro": "Vila Madalena", "total": 12},
        {"bairro": "Pinheiros", "total": 9},
        {"bairro": "Mooca", "total": 7},
        {"bairro": "Tatuapé", "total": 6},
    ],
    "resposta_natural": (
        "Nos últimos 30 dias, 4 bairros de São Paulo registraram mais de 5 ocorrências de furto. "
        "Vila Madalena lidera com 12 casos, seguida de Pinheiros (9), Mooca (7) e Tatuapé (6). "
        "Recomenda-se intensificação do policiamento ostensivo nessas áreas, especialmente em Vila Madalena."
    ),
}

_RELATORIO_DEMO = """# Relatório Executivo de Criminalidade
## Belo Horizonte — Últimos 30 dias

---

### 1. Panorama Geral

No período analisado, foram registrados **47 boletins de ocorrência** em Belo Horizonte, representando
aumento de 12% em relação ao mês anterior.

---

### 2. Incidência por Tipo Penal

| Tipo Penal | Ocorrências | % |
|---|---|---|
| Furto Simples | 18 | 38,3% |
| Roubo | 12 | 25,5% |
| Lesão Corporal | 8 | 17,0% |
| Ameaça | 5 | 10,6% |
| Outros | 4 | 8,5% |

---

### 3. Padrões Identificados

- **Concentração geográfica:** Savassi e Centro respondem por 61% das ocorrências de roubo.
- **Faixa horária crítica:** 73% dos roubos ocorrem entre 20h e 01h.
- **Perfil do suspeito:** Em 68% dos casos envolvendo roubo, os suspeitos atuam em dupla.
- **Alvo preferencial:** Aparelhos celulares foram o objeto subtraído em 54% das ocorrências.

---

### 4. Recomendações

1. Ampliar rondas ostensivas na Savassi e Centro no período noturno (20h–01h).
2. Acionar inteligência policial para mapeamento de receptadores de celulares na região.
3. Instalar câmeras adicionais nos pontos de maior incidência levantados neste relatório.
4. Realizar blitz de verificação de motos na Av. Afonso Pena — veículo usado em 42% dos roubos.
"""


# ── Sidebar ──────────────────────────────────────────────────────────────────

def _sidebar() -> tuple[str, bool]:
    with st.sidebar:
        st.markdown("# 🏛️ ÁGORA")
        st.caption("Inteligência em Segurança Pública")
        st.divider()

        idioma_label = st.selectbox("Idioma / Language", ["Português", "English"])
        idioma = "pt" if idioma_label == "Português" else "en"

        mostrar_logs = st.toggle(t("mostrar_logs", idioma), value=True)

        st.divider()
        st.markdown("**Base de dados**")

        # Tenta buscar estatísticas reais; cai para demo se banco não estiver configurado
        try:
            from db.repositorio import contar_bos
            total = contar_bos()
            st.metric(t("total_bos", idioma), total)
        except Exception as exc:
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(t("total_bos", idioma), "150")
            with col_b:
                st.metric(t("ultima_atualizacao", idioma), "—")
            st.caption("⚠️ " + t("banco_desconectado", idioma))
            st.sidebar.error(str(exc))

    return idioma, mostrar_logs


# ── Aba 1: Lavrar BO ─────────────────────────────────────────────────────────

def _aba_lavrar(idioma: str, mostrar_logs: bool) -> None:
    st.markdown("### Lavrar Boletim de Ocorrência")
    st.caption("Cole ou digite abaixo as notas livres do atendimento. O ÁGORA estrutura automaticamente.")

    resumo = st.text_area(
        t("resumo_label", idioma),
        placeholder=t("resumo_placeholder", idioma),
        height=160,
        key="resumo_input",
    )

    col_btn, col_demo = st.columns([2, 1])
    with col_btn:
        gerar = st.button(t("btn_gerar_bo", idioma), type="primary", use_container_width=True)
    with col_demo:
        demo = st.button("Ver exemplo (demo)", use_container_width=True)

    if demo:
        st.session_state["bo_gerado"] = _BO_DEMO
        st.session_state["passos_gerado"] = _PASSOS_DEMO

    if gerar:
        if not resumo.strip():
            st.warning(t("resumo_vazio", idioma))
        else:
            with st.spinner(t("gerando_bo", idioma)):
                try:
                    from agente.ferramentas import gerar_bo
                    resultado = gerar_bo(resumo)
                    st.session_state["bo_gerado"] = resultado
                    st.session_state["passos_gerado"] = resultado.get("passos", [])
                except Exception as exc:
                    st.error(f"{t('erro_generico', idioma)}\n\n`{exc}`")

    bo = st.session_state.get("bo_gerado")
    if bo:
        st.divider()
        exibir_bo(bo, idioma)

        with st.expander(t("ver_raciocinio", idioma)):
            st.markdown(bo.get("raciocinio_cot", "—"))

        if mostrar_logs:
            with st.expander(t("ver_passos_agente", idioma)):
                exibir_passos_agente(st.session_state.get("passos_gerado", []))

        st.divider()
        if st.button(t("btn_salvar_bo", idioma), type="secondary"):
            try:
                from db.repositorio import salvar_bo
                numero = salvar_bo(bo)
                st.success(f"{t('bo_salvo', idioma)} — Nº {numero}")
                st.session_state.pop("bo_gerado", None)
            except Exception as exc:
                st.error(f"{t('erro_supabase', idioma)}\n\n`{exc}`")


# ── Aba 2: Consultar ─────────────────────────────────────────────────────────

_SUGESTOES = {
    "pt": [
        "Quantos BOs foram registrados nos últimos 30 dias?",
        "Top 5 bairros mais perigosos em São Paulo",
        "Quais bairros de BH tiveram mais de 5 furtos este mês?",
        "Compare roubos e furtos no Rio nos últimos 60 dias",
    ],
    "en": [
        "How many reports in the last 30 days?",
        "Top 5 most dangerous neighborhoods in São Paulo",
        "Which BH neighborhoods had more than 5 thefts this month?",
        "Compare robberies and thefts in Rio over last 60 days",
    ],
}


def _aba_consultar(idioma: str, mostrar_logs: bool) -> None:
    st.markdown("### Consultar Inteligência Operacional")
    st.caption("Faça perguntas sobre a base de BOs em linguagem natural.")

    st.markdown(f"**{t('sugestoes_titulo', idioma)}**")
    sugestoes = _SUGESTOES.get(idioma, _SUGESTOES["pt"])
    cols = st.columns(2)
    for i, sug in enumerate(sugestoes):
        if cols[i % 2].button(sug, key=f"sug_{i}", use_container_width=True):
            st.session_state["pergunta_input"] = sug

    pergunta = st.text_input(
        t("pergunta_label", idioma),
        placeholder=t("pergunta_placeholder", idioma),
        key="pergunta_input",
    )

    col_btn2, col_demo2 = st.columns([2, 1])
    with col_btn2:
        consultar = st.button(t("btn_consultar", idioma), type="primary", use_container_width=True)
    with col_demo2:
        demo2 = st.button("Ver exemplo (demo)", key="demo_consulta", use_container_width=True)

    if demo2:
        st.session_state["resultado_consulta"] = _CONSULTA_DEMO

    if consultar:
        if not pergunta.strip():
            st.warning(t("pergunta_vazia", idioma))
        else:
            with st.spinner(t("consultando", idioma)):
                try:
                    from agente.ferramentas import consultar_base
                    resultado = consultar_base(pergunta)
                    st.session_state["resultado_consulta"] = resultado
                except Exception as exc:
                    st.error(f"{t('erro_generico', idioma)}\n\n`{exc}`")

    resultado = st.session_state.get("resultado_consulta")
    if resultado:
        st.divider()
        st.info(resultado.get("resposta_natural", t("sem_resultados", idioma)))

        with st.expander(t("ver_sql", idioma)):
            st.code(resultado.get("sql_gerado", "—"), language="sql")

        dados = resultado.get("resultados", [])
        if dados:
            with st.expander(t("ver_dados_brutos", idioma)):
                st.dataframe(dados, use_container_width=True)

        if mostrar_logs:
            with st.expander(t("ver_passos_agente", idioma)):
                exibir_passos_agente(resultado.get("passos", []))


# ── Aba 3: Relatório ─────────────────────────────────────────────────────────

def _aba_relatorio(idioma: str) -> None:
    st.markdown("### Relatório Executivo de Criminalidade")
    st.caption("Gera relatório analítico a partir dos BOs registrados, usando decomposição em sub-tarefas (Least-to-Most).")

    col1, col2 = st.columns(2)
    with col1:
        cidade = st.selectbox(t("cidade_label", idioma), t("cidades", idioma))
    with col2:
        periodo = st.selectbox(t("periodo_label", idioma), t("periodos", idioma))

    col_btn3, col_demo3 = st.columns([2, 1])
    with col_btn3:
        gerar_rel = st.button(t("btn_gerar_relatorio", idioma), type="primary", use_container_width=True)
    with col_demo3:
        demo3 = st.button("Ver exemplo (demo)", key="demo_relatorio", use_container_width=True)

    if demo3:
        st.session_state["relatorio_gerado"] = _RELATORIO_DEMO

    if gerar_rel:
        with st.spinner(t("gerando_relatorio", idioma)):
            try:
                from agente.ferramentas import gerar_relatorio
                resultado = gerar_relatorio(cidade, periodo)
                st.session_state["relatorio_gerado"] = resultado.get("relatorio_markdown", "")
            except Exception as exc:
                st.error(f"{t('erro_generico', idioma)}\n\n`{exc}`")

    relatorio = st.session_state.get("relatorio_gerado")
    if relatorio:
        st.divider()
        st.markdown(relatorio)
        st.download_button(
            label=t("btn_baixar_relatorio", idioma),
            data=relatorio,
            file_name=f"relatorio_{cidade.lower().replace(' ', '_')}_{periodo.split()[1]}_dias.md",
            mime="text/markdown",
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    idioma, mostrar_logs = _sidebar()

    aba1, aba2, aba3 = st.tabs([
        t("aba_lavrar", idioma),
        t("aba_consultar", idioma),
        t("aba_relatorio", idioma),
    ])

    with aba1:
        _aba_lavrar(idioma, mostrar_logs)

    with aba2:
        _aba_consultar(idioma, mostrar_logs)

    with aba3:
        _aba_relatorio(idioma)


if __name__ == "__main__":
    main()
