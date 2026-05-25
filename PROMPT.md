# PROMPT.md — Projeto ÁGORA

> **Para o Claude Code:** este documento é o briefing completo do projeto. Você vai executá-lo **por fases**, na ordem. Ao final de cada fase, **pare**, mostre o que foi feito e aguarde o usuário validar antes de seguir pra próxima. Não pule fases. Não tente fazer tudo de uma vez.

---

## 1. Contexto do Projeto

**ÁGORA** é um agente de IA especializado em segurança pública brasileira, desenvolvido como trabalho acadêmico das disciplinas de Engenharia de Prompt + Fundamentos de IA.

**O que ele faz:**
1. Recebe um **resumo livre** de uma ocorrência (texto digitado por um agente policial após atendimento humano ao cidadão)
2. Gera automaticamente um **Boletim de Ocorrência estruturado e padronizado**
3. Armazena os BOs em banco de dados
4. Permite **consultas em linguagem natural** sobre a base ("quais bairros tiveram mais furtos no último mês?")
5. Gera **relatórios executivos** sob demanda

**O contato com o cidadão permanece humano** — o ÁGORA atua só na camada pós-atendimento.

**Princípio do projeto:** demonstrar variedade de técnicas de engenharia de prompt em um agente real, com integração a banco de dados.

---

## 2. Stack Tecnológico (fixo)

- **Linguagem:** Python 3.11+
- **LLM:** OpenAI API
  - `gpt-4o-mini` — uso geral (consultas, classificação, validação)
  - `gpt-4o` — geração de BO (vale a qualidade extra)
  - Configurável via `.env`
- **Orquestração:** LangChain (agente ReAct com ferramentas customizadas)
- **Banco de dados:** Supabase (PostgreSQL)
- **Interface:** Streamlit
- **Idioma do código:** **português** (variáveis, funções, comentários). Strings de UI também em português. Suportar i18n simples pra inglês via dicionário (implementar na Fase 6).

---

## 3. Estrutura de Pastas

```
agora/
├── .env.example              # template das variáveis de ambiente
├── .env                      # local, no .gitignore
├── .gitignore
├── README.md
├── requirements.txt
├── agente/
│   ├── __init__.py
│   ├── nucleo.py             # AgenteAgora — classe principal com ReAct
│   ├── ferramentas.py        # ferramentas LangChain expostas ao agente
│   └── llm.py                # wrapper de chamadas OpenAI (centraliza modelo, temperatura, logs)
├── prompts/
│   ├── __init__.py
│   ├── sistema.py            # role prompt base
│   ├── gerar_bo.py           # few-shot + CoT pra gerar BO
│   ├── validar_bo.py         # chain of verification
│   ├── consultar_base.py     # NL → SQL com step-back
│   └── gerar_relatorio.py    # least-to-most pra relatórios
├── db/
│   ├── __init__.py
│   ├── schema.sql            # DDL das tabelas
│   ├── conexao.py            # cliente Supabase
│   └── repositorio.py        # funções de CRUD (salvar_bo, listar_bos, executar_query)
├── app/
│   ├── streamlit_app.py      # entrada principal da UI
│   ├── i18n.py               # dicionário pt/en
│   └── componentes.py        # componentes reutilizáveis (logs do agente, exibição de BO)
├── scripts/
│   ├── seed_bos.py           # gera BOs sintéticos via OpenAI e popula banco
│   └── reset_db.py           # limpa banco (usar com cuidado)
└── tests/
    ├── test_gerar_bo.py
    ├── test_consultar.py
    └── exemplos_entrada.py   # casos de teste reutilizáveis
```

---

## 4. Variáveis de Ambiente (`.env.example`)

```env
# OpenAI
OPENAI_API_KEY=sk-...
MODELO_GERAL=gpt-4o-mini
MODELO_GERACAO_BO=gpt-4o
TEMPERATURA_GERAL=0.3
TEMPERATURA_GERACAO=0.4

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJ...

# App
IDIOMA_PADRAO=pt
LOG_AGENTE_VISIVEL=true
```

---

## 5. Modelo de Dados (PostgreSQL / Supabase)

```sql
CREATE TABLE boletins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  numero_bo VARCHAR(20) UNIQUE NOT NULL,
  data_fato DATE,
  hora_fato TIME,
  tipo_penal VARCHAR(200) NOT NULL,
  artigo_penal VARCHAR(50),
  cidade VARCHAR(100),
  uf CHAR(2),
  bairro VARCHAR(100),
  endereco TEXT,
  narrativa TEXT NOT NULL,
  resumo_original TEXT,
  pendencias TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE partes_envolvidas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  boletim_id UUID REFERENCES boletins(id) ON DELETE CASCADE,
  papel VARCHAR(20) CHECK (papel IN ('vitima', 'suspeito', 'testemunha')),
  nome VARCHAR(200),
  documento VARCHAR(50),
  descricao TEXT
);

CREATE TABLE objetos_envolvidos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  boletim_id UUID REFERENCES boletins(id) ON DELETE CASCADE,
  descricao TEXT NOT NULL,
  status VARCHAR(20) CHECK (status IN ('subtraido', 'recuperado', 'apreendido', 'danificado'))
);

CREATE INDEX idx_boletins_data ON boletins(data_fato);
CREATE INDEX idx_boletins_tipo ON boletins(tipo_penal);
CREATE INDEX idx_boletins_local ON boletins(cidade, bairro);
```

---

## 6. Técnicas de Prompt — Onde Cada Uma Vive

| Técnica | Arquivo | Função |
|---|---|---|
| **Role Prompt** | `prompts/sistema.py` | Identidade do ÁGORA — usado em todas as chamadas |
| **Few-shot** | `prompts/gerar_bo.py` | 2-3 exemplos de resumo→BO antes do novo input |
| **Chain of Thought** | `prompts/gerar_bo.py` | Raciocínio passo a passo pra classificar tipo penal |
| **Chain of Verification** | `prompts/validar_bo.py` | Checklist de completude após geração |
| **Step Back** | `prompts/consultar_base.py` | "Antes de gerar SQL, pense na estrutura da resposta" |
| **Least-to-Most** | `prompts/gerar_relatorio.py` | Decomposição em sub-tarefas |
| **ReAct** | `agente/nucleo.py` | Orquestração do agente via LangChain |

Cada arquivo de prompt deve exportar uma constante (`PROMPT_GERAR_BO`, `PROMPT_VALIDAR_BO`, etc.) e, quando aplicável, uma função que monta o prompt final com variáveis interpoladas.

---

# FASES DE EXECUÇÃO

> **Importante:** ao terminar cada fase, exiba um resumo do que foi feito, peça pro usuário rodar/testar, e **só siga pra próxima fase quando ele confirmar**.

---

## FASE 1 — Setup do Ambiente e Estrutura Base

**Objetivo:** ter o esqueleto do projeto rodando, com Supabase conectado e uma chamada de teste à OpenAI funcionando.

**Tarefas:**

1. Criar toda a estrutura de pastas listada na seção 3 (com `__init__.py` vazios e arquivos placeholders quando aplicável)
2. Criar `requirements.txt` com:
   ```
   openai>=1.30.0
   langchain>=0.2.0
   langchain-openai>=0.1.0
   supabase>=2.4.0
   streamlit>=1.35.0
   python-dotenv>=1.0.0
   pydantic>=2.0
   ```
3. Criar `.env.example` (conteúdo da seção 4) e `.gitignore` (incluir `.env`, `__pycache__`, `.venv`)
4. Criar `README.md` com instruções de setup
5. Implementar `agente/llm.py` com uma função `chamar_modelo(prompt, modelo=None, temperatura=None)` que retorna a resposta da OpenAI
6. Implementar `db/conexao.py` com cliente Supabase inicializado a partir do `.env`
7. **Antes de prosseguir**, instrua o usuário a:
   - Criar uma conta no Supabase (https://supabase.com) se ainda não tiver
   - Criar um novo projeto (anotar URL e anon key)
   - Copiar `.env.example` pra `.env` e preencher
   - Rodar `pip install -r requirements.txt` (sugerir venv)
8. Criar `scripts/teste_setup.py` que:
   - Faz uma chamada simples à OpenAI ("diga olá")
   - Faz um `select 1` no Supabase
   - Imprime "✅ Setup OK" se ambos passarem

**Critério de pronto:** `python scripts/teste_setup.py` imprime "✅ Setup OK".

**Pare aqui. Aguarde validação do usuário antes de seguir.**

---

## FASE 2 — Schema do Banco e Seed de BOs Sintéticos

**Objetivo:** banco populado com ~150 BOs realistas pra alimentar as consultas das próximas fases.

**Tarefas:**

1. Implementar `db/schema.sql` (DDL da seção 5)
2. Instruir o usuário a executar o SQL no editor SQL do Supabase (mostrar passo a passo: Dashboard → SQL Editor → New Query → colar → Run)
3. Implementar `db/repositorio.py` com:
   - `salvar_bo(dados_bo: dict) -> str` — insere em `boletins`, `partes_envolvidas` e `objetos_envolvidos`, retorna o `numero_bo`
   - `listar_bos(filtros: dict = None) -> list`
   - `executar_query_select(sql: str) -> list` — executa SELECT arbitrário (usado pela ferramenta de consulta). **IMPORTANTE: aceitar SOMENTE SELECT, rejeitar qualquer outro comando** (validação por regex no início da string)
4. Implementar `scripts/seed_bos.py` que:
   - Define uma lista de **cenários** (dicts com tipo_penal, cidade, bairro, características) cobrindo:
     - **Tipos penais:** furto simples, furto qualificado, roubo, lesão corporal, ameaça, dano, receptação, estelionato, perturbação do sossego, vias de fato
     - **Cidades:** Belo Horizonte, São Paulo, Rio de Janeiro
     - **Bairros realistas por cidade:**
       - BH: Savassi, Centro, Pampulha, Barreiro, Cidade Nova, Floresta
       - SP: Vila Madalena, Bela Vista, Pinheiros, Mooca, Tatuapé, Santo Amaro
       - RJ: Copacabana, Tijuca, Méier, Botafogo, Madureira, Barra da Tijuca
   - Para cada cenário, chama a OpenAI pedindo pra gerar um **resumo livre** realista (como se fosse um agente digitando notas rápidas após o atendimento) — variar tom, ortografia, completude
   - Distribui as **datas dos fatos** ao longo dos últimos 90 dias (variar bastante pra permitir consultas temporais interessantes)
   - Para cada resumo, chama o pipeline de geração de BO (que vai existir só na Fase 3 — então a Fase 2 só monta a estrutura, e o seed é executado **no final da Fase 3**)
   - **IMPORTANTE:** estruture o script pra aceitar `--quantidade N` (default 150) e `--dry-run` (não grava, só imprime)

5. Implementar `scripts/reset_db.py` que apaga todas as linhas das 3 tabelas (com confirmação interativa "tem certeza? digite SIM")

**Critério de pronto:** schema executado no Supabase com sucesso (verificável no Table Editor); script de seed implementado mas ainda não executado (depende da Fase 3).

**Pare aqui. Aguarde validação.**

---

## FASE 3 — Geração de BO (Role + Few-shot + CoT + CoVe)

**Objetivo:** ter a ferramenta de geração de BO funcionando ponta a ponta. Esta é a fase mais importante da engenharia de prompt do projeto.

**Tarefas:**

1. Implementar `prompts/sistema.py` com a constante `PROMPT_SISTEMA`:
   ```
   Você é o ÁGORA, um assistente especializado em segurança pública brasileira.
   Você atua como apoio a escrivães e agentes da Polícia Civil, Polícia Militar,
   Polícia Federal e PRF na lavratura de Boletins de Ocorrência e na geração de
   inteligência operacional.

   Sua linguagem é técnica, objetiva e segue os padrões formais da documentação
   policial brasileira. Use voz ativa, terceira pessoa e sequência cronológica.

   Você nunca inventa fatos. Trabalha estritamente com base nas informações
   fornecidas pelo agente humano. Quando informações importantes estiverem
   ausentes, sinalize como pendência — nunca preencha por conta própria.
   ```

2. Implementar `prompts/gerar_bo.py` com:
   - Constante `EXEMPLOS_FEW_SHOT` — lista de 3 pares (resumo_livre, bo_estruturado_em_json) cobrindo: um furto simples, um roubo com arma, e uma ameaça (variar pra mostrar o padrão)
   - Função `montar_prompt_gerar_bo(resumo_livre: str) -> str` que retorna o prompt completo:
     - Instrução de Chain of Thought ("Antes de classificar o tipo penal, analise: 1) houve subtração? 2) houve violência ou grave ameaça? 3) houve emprego de arma? 4) ...")
     - Os 3 exemplos few-shot
     - O resumo livre novo
     - Instrução pra retornar **JSON estruturado** seguindo o schema do BO

   **Schema JSON de saída do BO:**
   ```json
   {
     "tipo_penal": "string",
     "artigo_penal": "string",
     "data_fato": "YYYY-MM-DD ou null",
     "hora_fato": "HH:MM ou null",
     "cidade": "string ou null",
     "uf": "string (2 letras) ou null",
     "bairro": "string ou null",
     "endereco": "string ou null",
     "narrativa": "string (texto técnico em prosa)",
     "partes": [{"papel": "vitima|suspeito|testemunha", "nome": "...", "documento": "...", "descricao": "..."}],
     "objetos": [{"descricao": "...", "status": "subtraido|recuperado|apreendido|danificado"}],
     "raciocinio_cot": "string com o passo a passo da classificação"
   }
   ```

3. Implementar `prompts/validar_bo.py` com função `montar_prompt_validar_bo(bo_json: dict) -> str`:
   - Instrução de Chain of Verification: lista de 8 perguntas de checagem (data, hora, local, vítima, suspeito, narrativa coerente, tipo penal coerente, objetos quando aplicável)
   - Retorna JSON: `{"completo": bool, "pendencias": [str], "observacoes": str}`

4. Implementar `agente/ferramentas.py` com a primeira ferramenta:
   ```python
   def gerar_bo(resumo_livre: str) -> dict:
       """
       Gera um Boletim de Ocorrência estruturado a partir de um resumo livre.
       Aplica Role Prompt + Few-shot + CoT, depois Chain of Verification.
       Retorna o BO em formato dict pronto pra persistência.
       """
   ```
   - Chama OpenAI com prompt de geração (modelo `MODELO_GERACAO_BO`)
   - Parseia o JSON retornado (tratamento de erro: se não vier JSON válido, tenta de novo uma vez com instrução mais firme)
   - Chama OpenAI com prompt de validação (modelo `MODELO_GERAL`)
   - Retorna dict combinando os dois (BO + pendências)

5. Implementar `tests/test_gerar_bo.py` com 3 casos de teste em `tests/exemplos_entrada.py`:
   - Caso A: roubo com arma na Av. Paulista (o do documento)
   - Caso B: furto de bicicleta com pouca informação (testa pendências)
   - Caso C: ameaça envolvendo ex-companheiro (testa classificação correta como ameaça e não lesão)

6. **Após implementar e testar a geração**, executar `python scripts/seed_bos.py --quantidade 150` pra popular o banco.

**Critério de pronto:**
- Os 3 casos de teste rodam e retornam BOs estruturados coerentes
- Banco populado com ~150 BOs (verificável no Table Editor do Supabase)
- BOs gerados têm distribuição razoável entre tipos penais e cidades

**Pare aqui. Aguarde validação.**

---

## FASE 4 — Consultas em Linguagem Natural (Step Back + NL→SQL)

**Objetivo:** ferramenta que recebe pergunta em português, gera SQL válido e retorna resposta sintetizada.

**Tarefas:**

1. Implementar `prompts/consultar_base.py`:
   - Constante com o **schema do banco em texto** (descrição das 3 tabelas e campos), pra incluir no prompt
   - Função `montar_prompt_nl_para_sql(pergunta: str) -> str`:
     - Aplica **Step Back**: "Antes de escrever a query, pense: que tipo de resposta o usuário espera? (lista? número único? agrupamento? comparação temporal?)"
     - Inclui o schema
     - Pede SQL retornado em bloco markdown ```sql
     - Restrições explícitas: SOMENTE SELECT, sem DROP/UPDATE/DELETE/INSERT
   - Função `montar_prompt_sintetizar_resposta(pergunta: str, sql: str, resultados: list) -> str`:
     - Instrui o modelo a gerar resposta em prosa natural
     - Se resultados vazios, explicar isso ao invés de inventar

2. Adicionar ferramenta em `agente/ferramentas.py`:
   ```python
   def consultar_base(pergunta_natural: str) -> dict:
       """
       Responde uma pergunta sobre o banco de BOs em linguagem natural.
       Aplica Step Back + NL→SQL.
       Retorna {"sql_gerado": str, "resultados": list, "resposta_natural": str}.
       """
   ```
   - Gera SQL via OpenAI
   - **Valida** que começa com SELECT (regex), rejeita se não
   - Executa via `repositorio.executar_query_select`
   - Sintetiza resposta natural

3. Casos de teste em `tests/test_consultar.py`:
   - "Quantos BOs foram registrados nos últimos 30 dias?" → número
   - "Quais os 3 tipos de crime mais frequentes em Belo Horizonte?" → ranking
   - "Liste os bairros de São Paulo com mais de 5 ocorrências de furto" → lista
   - "Compare o número de roubos no Rio entre as duas semanas mais recentes" → comparação

**Critério de pronto:** os 4 casos retornam respostas coerentes e os SQLs gerados são corretos.

**Pare aqui. Aguarde validação.**

---

## FASE 5 — Relatórios Executivos + Agente ReAct

**Objetivo:** unificar tudo em um agente ReAct que decide qual ferramenta usar, e adicionar a ferramenta de relatórios executivos com Least-to-Most.

**Tarefas:**

1. Implementar `prompts/gerar_relatorio.py`:
   - Função `decompor_relatorio(escopo: str, periodo: str) -> list[str]` que pede pro modelo retornar as **sub-tarefas** necessárias (Least-to-Most)
   - Função `sintetizar_relatorio_final(sub_resultados: list[dict]) -> str` que monta o relatório executivo final em formato markdown estruturado (Panorama / Incidência / Padrões / Recomendações)

2. Adicionar ferramenta em `agente/ferramentas.py`:
   ```python
   def gerar_relatorio(escopo: str, periodo: str) -> dict:
       """
       Gera um relatório executivo de criminalidade.
       Aplica Least-to-Most: decompõe em sub-tarefas, executa cada uma
       (consultando o banco), e sintetiza relatório final.
       Retorna {"sub_tarefas": [...], "relatorio_markdown": str}.
       """
   ```

3. Implementar `agente/nucleo.py`:
   - Classe `AgenteAgora`
   - Construtor recebe LLM e lista de ferramentas
   - Usa `langchain.agents.create_react_agent` com prompt customizado em **português** (template ReAct adaptado: Thought/Action/Observation/Final Answer)
   - Método `executar(pergunta: str) -> dict` que retorna:
     ```python
     {
       "resposta_final": str,
       "passos_intermediarios": list[dict],  # cada passo com thought, action, observation
       "ferramentas_usadas": list[str]
     }
     ```
   - **Importante:** capturar o callback handler do LangChain pra extrair os passos intermediários (será exibido na UI)

4. Casos de teste em `tests/test_agente.py`:
   - "Gere um BO desse relato: [resumo livre]" → deve usar `gerar_bo`
   - "Quais bairros tiveram mais ocorrências este mês?" → deve usar `consultar_base`
   - "Faça um relatório executivo de criminalidade em Belo Horizonte do último mês" → deve usar `gerar_relatorio` (que internamente usa `consultar_base` várias vezes)
   - "Compare furtos e roubos em SP nos últimos 60 dias" → deve usar `consultar_base` (escolha do agente)

**Critério de pronto:** o agente escolhe corretamente a ferramenta em cada caso e os passos intermediários são capturados.

**Pare aqui. Aguarde validação.**

---

## FASE 6 — Interface Streamlit + Polimento

**Objetivo:** UI completa, polida, pronta pra demonstração no pitch.

**Tarefas:**

1. Implementar `app/i18n.py` com dicionário pt/en de todas as strings da UI
2. Implementar `app/componentes.py`:
   - `exibir_bo(bo: dict)` — renderiza um BO formatado em colunas (cabeçalho com classificação penal, narrativa em destaque, tabelas pra partes e objetos, alerta amarelo pras pendências)
   - `exibir_passos_agente(passos: list)` — renderiza Thought/Action/Observation em expanders, com ícones (🤔 thought, 🔧 action, 👁️ observation, ✅ final answer)
3. Implementar `app/streamlit_app.py` com 3 abas:

   **Aba 1 — Lavrar BO:**
   - Text area grande pra resumo livre
   - Botão "Gerar Boletim de Ocorrência"
   - Mostra spinner enquanto processa
   - Exibe BO estruturado via `exibir_bo`
   - Botão "Salvar no banco" (chama `repositorio.salvar_bo`)
   - Expander "Ver raciocínio do agente" mostrando o CoT da classificação penal

   **Aba 2 — Consultar Inteligência:**
   - Input de pergunta em linguagem natural
   - Sugestões de perguntas (chips clicáveis): "Quantos BOs no último mês?", "Top 5 bairros mais perigosos em SP", etc.
   - Resposta natural em destaque
   - Expander "Ver SQL gerado" + "Ver dados brutos" (tabela)
   - Expander "Ver passos do agente" (se LOG_AGENTE_VISIVEL=true)

   **Aba 3 — Relatório Executivo:**
   - Selectbox de cidade (BH/SP/RJ/Todas)
   - Selectbox de período (Últimos 7/30/60/90 dias)
   - Botão "Gerar relatório"
   - Mostra relatório em markdown
   - Botão "Baixar como .md"

4. **Sidebar:**
   - Logo/nome do projeto ("ÁGORA")
   - Seletor de idioma (pt/en) — recarrega strings via `i18n`
   - Toggle "Mostrar logs do agente"
   - Mini-painel com estatísticas do banco (total de BOs, última atualização) — query simples

5. **Polimento:**
   - Tema customizado em `.streamlit/config.toml` — paleta institucional (azul escuro #1F3864, cinza neutro)
   - Favicon e título da aba
   - Mensagens de erro amigáveis (try/except em volta das chamadas do agente)
   - Loading states em tudo

**Critério de pronto:**
- `streamlit run app/streamlit_app.py` abre uma UI funcional, bonita e estável
- As 3 abas funcionam ponta a ponta
- Trocar idioma funciona
- Logs do agente aparecem corretamente

**Pare aqui. Sucesso!**

---

## 7. Convenções de Código

- **Imports** sempre absolutos (`from agente.ferramentas import gerar_bo`, não `from ..ferramentas import`)
- **Docstrings** em todas as funções públicas — em português
- **Type hints** em todas as assinaturas
- **Pydantic** pra validar entradas/saídas estruturadas (BO, resultado de consulta)
- **Tratamento de erros**: nunca deixe exceção crua chegar na UI. Sempre logar e exibir mensagem amigável.
- **Logs**: usar `logging` do Python, não `print` (exceto nos scripts de teste/seed)
- **Sem hardcode de chaves** — sempre via `os.getenv`

---

## 8. Critérios de Qualidade Acadêmica

Este é um trabalho avaliado. Algumas coisas pesam pra nota:

- **Variedade de técnicas de prompt aplicadas** — deixe explícito no código (comentários no topo de cada prompt indicando qual técnica está sendo usada e por quê)
- **Logs do raciocínio do agente visíveis** — pro pitch, mostrar Thought/Action/Observation rodando ao vivo é o que mais impressiona
- **Código limpo e organizado** — pasta por responsabilidade, sem arquivo monstrengo
- **README com instruções claras** — qualquer um do grupo (ou o professor) consegue rodar
- **Demonstração funcional** — os 3 fluxos (lavrar BO, consultar, relatório) precisam funcionar de verdade no dia do pitch

---

## 9. O Que NÃO Fazer

- ❌ Não implemente autenticação (escopo acadêmico, dispensa)
- ❌ Não use Next.js, FastAPI, ou qualquer outro framework além dos listados
- ❌ Não invente um modelo de BO completamente diferente do simplificado descrito aqui
- ❌ Não use SQLite — o projeto requer Postgres (Supabase) pelas razões já decididas
- ❌ Não pule a Chain of Verification — ela é central pro diferencial do projeto
- ❌ Não comece pela UI — siga as fases na ordem
- ❌ Não tente fazer tudo de uma vez. **Pare ao final de cada fase.**

---

## 10. Primeira Ação

Comece pela **Fase 1**. Confirme o entendimento geral do projeto (uma frase) e parta pra criação da estrutura. Ao final da Fase 1, pare e me peça pra rodar `scripts/teste_setup.py`.

Boa execução. 🚀
