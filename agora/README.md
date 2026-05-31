# AGORA - Agente de Inteligencia em Seguranca Publica

Aplicacao academica em Python/Streamlit para lavratura assistida de Boletins de Ocorrencia e geracao de inteligencia operacional sobre uma base de BOs.

## O que funciona

- Interface Streamlit com tres abas: lavrar BO, consultar inteligencia e relatorio executivo.
- Geracao de BO com OpenAI quando `OPENAI_API_KEY` esta configurada.
- Fallback local por heuristicas quando a chave da OpenAI nao existe, permitindo demonstracao offline.
- Persistencia no Supabase via API REST.
- Scripts para testar setup, limpar banco e popular dados sinteticos.
- Testes automatizados sem dependencia de rede.

## Pre-requisitos

- Python 3.11+
- Conta OpenAI, opcional para uso com IA real
- Projeto Supabase, necessario para salvar, consultar e gerar relatorios com dados reais

## Como executar localmente

```powershell
cd "C:\caminho\para\boletinFaculdade\agora"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
streamlit run app\streamlit_app.py
```

Acesse:

```text
http://localhost:8501
```

## Configuracao do .env

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha:

```env
OPENAI_API_KEY=sua_chave_openai
MODELO_GERAL=gpt-4o-mini
MODELO_GERACAO_BO=gpt-4o
TEMPERATURA_GERAL=0.3
TEMPERATURA_GERACAO=0.4

SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_anon_public_key
```

Sem `OPENAI_API_KEY`, a geracao de BO continua funcionando com fallback local. Sem Supabase, a interface abre, mas salvar, consultar dados reais e gerar relatorios reais dependem do banco configurado.

No Streamlit Cloud, configure as mesmas chaves em **Settings > Secrets**:

```toml
OPENAI_API_KEY = "sua_chave_openai"
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua_anon_public_key"
MODELO_GERAL = "gpt-4o-mini"
MODELO_GERACAO_BO = "gpt-4o"
TEMPERATURA_GERAL = "0.3"
TEMPERATURA_GERACAO = "0.4"
HTTPX_VERIFY_SSL = "true"
```

## Configurar o Supabase

1. Abra o dashboard do Supabase.
2. Entre em SQL Editor.
3. Crie uma nova query.
4. Cole todo o conteudo de `db/schema.sql`.
5. Execute.

O schema cria as tabelas `boletins`, `partes` e `objetos`, indices e policies para uso com a anon key em contexto academico.

## Comandos uteis

Testar OpenAI e Supabase:

```powershell
python scripts\teste_setup.py
```

Popular o banco:

```powershell
python scripts\seed_bos.py --quantidade 150
```

Limpar o banco:

```powershell
python scripts\reset_db.py
```

Rodar testes:

```powershell
python -m pytest -q
```

## Estrutura

```text
agente/   ferramentas do agente e orquestrador simples
app/      interface Streamlit
db/       schema SQL e repositorio REST para Supabase
prompts/  espaco para prompts academicos
scripts/  utilitarios de setup, seed e reset
tests/    testes automatizados
```
