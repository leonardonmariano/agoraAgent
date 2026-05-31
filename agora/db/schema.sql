-- Schema Supabase do AGORA.
-- Execute este arquivo no SQL Editor do Supabase.

create extension if not exists "pgcrypto";

create table if not exists public.boletins (
    id uuid primary key default gen_random_uuid(),
    numero text not null unique,
    tipo_penal text not null,
    artigo_penal text,
    data_fato date,
    hora_fato time,
    cidade text,
    uf text,
    bairro text,
    endereco text,
    narrativa text not null,
    pendencias jsonb not null default '[]'::jsonb,
    raciocinio_cot text,
    passos jsonb not null default '[]'::jsonb,
    criado_em timestamptz not null default now()
);

create table if not exists public.partes (
    id uuid primary key default gen_random_uuid(),
    boletim_id uuid not null references public.boletins(id) on delete cascade,
    papel text not null,
    nome text,
    documento text,
    descricao text
);

create table if not exists public.objetos (
    id uuid primary key default gen_random_uuid(),
    boletim_id uuid not null references public.boletins(id) on delete cascade,
    descricao text not null,
    status text
);

create index if not exists idx_boletins_data on public.boletins(data_fato);
create index if not exists idx_boletins_cidade on public.boletins(cidade);
create index if not exists idx_boletins_bairro on public.boletins(bairro);
create index if not exists idx_boletins_tipo on public.boletins(tipo_penal);
create index if not exists idx_partes_boletim on public.partes(boletim_id);
create index if not exists idx_objetos_boletim on public.objetos(boletim_id);

alter table public.boletins enable row level security;
alter table public.partes enable row level security;
alter table public.objetos enable row level security;

drop policy if exists "boletins_anon_select" on public.boletins;
drop policy if exists "boletins_anon_insert" on public.boletins;
drop policy if exists "boletins_anon_delete" on public.boletins;
drop policy if exists "partes_anon_all" on public.partes;
drop policy if exists "objetos_anon_all" on public.objetos;

create policy "boletins_anon_select" on public.boletins
for select to anon using (true);

create policy "boletins_anon_insert" on public.boletins
for insert to anon with check (true);

create policy "boletins_anon_delete" on public.boletins
for delete to anon using (true);

create policy "partes_anon_all" on public.partes
for all to anon using (true) with check (true);

create policy "objetos_anon_all" on public.objetos
for all to anon using (true) with check (true);
