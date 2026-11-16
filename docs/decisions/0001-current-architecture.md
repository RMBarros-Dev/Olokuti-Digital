# ADR-0001 — Utilizar Django modular com persistência configurada por ambiente

- **Status:** Registrado (arquitetura atual, documentada retrospectivamente)
- **Data do registro:** 2026-11-15

## Contexto

Organizei o projeto em uma aplicação Django com módulos de contas, catálogo, operações, relatórios e auditoria. O banco é configurado por `DATABASE_URL`, com suporte ao PostgreSQL e SQLite nos ambientes apropriados.

## Decisão atual

Mantenho a aplicação modular por domínio, centralizo configurações em `config/` e utilizo o ORM do Django para persistência. Utilizo middleware e URLs localizadas para organizar a experiência multilíngue.

## Consequências

- Consigo isolar responsabilidades por aplicação Django.
- Alterações de banco devem ser acompanhadas por migrations e testes.
- A configuração por ambiente permite separar desenvolvimento e implantação.
- Permissões e auditoria precisam ser testadas em conjunto com os fluxos de negócio.
- Utilizo dados sintéticos em demonstrações e testes.

## Nota histórica

Registrei retrospectivamente a arquitetura observada nos arquivos do projeto. Não atribuo uma data original a esta decisão.
