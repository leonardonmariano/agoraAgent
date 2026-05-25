# ÁGORA — Agente de Inteligência em Segurança Pública

Agente de IA que automatiza a lavratura de Boletins de Ocorrência e gera inteligência operacional a partir da base de BOs.

## Pré-requisitos

- Python 3.11+
- Conta na [OpenAI](https://platform.openai.com) com chave de API
- Conta no [Supabase](https://supabase.com) com projeto criado

## Setup

### 1. Clone e crie o ambiente virtual

```bash
git clone <repo>
cd agora
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas chaves:

| Variável | Onde obter |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `SUPABASE_URL` | Dashboard do projeto → Settings → API → Project URL |
| `SUPABASE_KEY` | Dashboard do projeto → Settings → API → anon public |

### 4. Configure o banco de dados

No Dashboard do Supabase, vá em **SQL Editor → New Query**, cole o conteúdo de `db/schema.sql` e clique em **Run**.

### 5. Teste o setup

```bash
python scripts/teste_setup.py
```

Deve imprimir `✅ Setup OK`.

### 6. Popule o banco com dados sintéticos

```bash
python scripts/seed_bos.py --quantidade 150
```

### 7. Rode a aplicação

```bash
streamlit run app/streamlit_app.py
```

## Estrutura do Projeto

```
agora/
├── agente/          # Núcleo do agente ReAct e ferramentas LangChain
├── prompts/         # Templates de prompt (Role, Few-shot, CoT, CoVe, Step Back, Least-to-Most)
├── db/              # Schema SQL, conexão e repositório Supabase
├── app/             # Interface Streamlit
├── scripts/         # Utilitários (seed, reset, teste)
└── tests/           # Casos de teste
```

## Técnicas de Prompt Utilizadas

| Técnica | Arquivo | Propósito |
|---|---|---|
| Role Prompt | `prompts/sistema.py` | Identidade e tom do ÁGORA |
| Few-shot | `prompts/gerar_bo.py` | Exemplos de resumo→BO |
| Chain of Thought | `prompts/gerar_bo.py` | Classificação penal passo a passo |
| Chain of Verification | `prompts/validar_bo.py` | Checklist de completude do BO |
| Step Back | `prompts/consultar_base.py` | NL→SQL com reflexão prévia |
| Least-to-Most | `prompts/gerar_relatorio.py` | Decomposição de relatórios executivos |
| ReAct | `agente/nucleo.py` | Orquestração com LangChain |
