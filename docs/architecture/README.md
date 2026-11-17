# Arquitetura do Olokuti Digital

## Visão geral

O Olokuti Digital é um MVP acadêmico e experimental implementado como monólito modular Django. O backend é organizado em aplicações por domínio; os módulos compartilham processo, configuração e banco de dados. Templates Django renderizam a interface e HTMX atualiza fragmentos selecionados.

## Componentes observados

| Componente | Responsabilidade |
|---|---|
| `config/` | Configurações Django, URLs, ASGI e WSGI |
| `apps/accounts/` | Contas, autenticação e permissões |
| `apps/catalog/` | Funcionalidades de catálogo |
| `apps/operations/` | Operações e listas de trabalho |
| `apps/reports/` | Relatórios |
| `apps/audit/` | Auditoria |
| `templates/` e `static/` | Interface e recursos estáticos |
| `locale/` | Catálogos de tradução do Django |
| `tests/` | Testes automatizados |

## Fluxo arquitetural

```mermaid
flowchart TD
    B[Browser] --> M[Django Middleware]
    M --> I18N[Locale Middleware e URLs localizadas]
    I18N --> V[Views e URLs dos apps]
    V --> T[Templates e recursos estáticos]
    V --> ORM[Django ORM]
    ORM --> DB[(PostgreSQL ou SQLite de desenvolvimento)]
    V --> AUD[Auditoria e relatórios]
```

## Dados e configuração

Leio a conexão de banco a partir de `DATABASE_URL`. O parser em `config/settings/base.py` contempla PostgreSQL e SQLite. Para o pooler transacional do Supabase, desativo cursores server-side e mantenho conexões persistentes desabilitadas.

O endpoint `/health?db=1` executa `SELECT 1` para validar conectividade com o banco.

## Idiomas

Utilizo `LocaleMiddleware`, URLs localizadas e catálogos em `locale/`. Mantenho a lista de idiomas suportados e os procedimentos de compilação alinhados ao README e aos arquivos de tradução do repositório.

## Qualidade e segurança

O workflow executa Ruff e pytest. Mantenho testes para parsing de URLs de banco, autenticação, catálogo, operações, relatórios e permissões. Nos exemplos e contribuições, utilizo dados sintéticos e não versiono credenciais reais.

## Hospedagem e configuração

O repositório contém `railway.json`, `render.yaml` e `vercel.json`, mas arquivos versionados não comprovam serviços ativos. Em novembro de 2026, Railway informa que Config as Code está descontinuado: serviços existentes podem utilizar `railway.json`/`railway.toml` somente até 1º de dezembro de 2026; novos serviços não podem adotar esse formato. A migração recomendada é Infrastructure as Code (`.railway/railway.ts`). Verifique o serviço ativo antes de alterar a configuração. Consulte a [documentação oficial da Railway](https://docs.railway.com/config-as-code).

## Referências

- [README](../../README.md)
- [Contribuição](../../CONTRIBUTING.md)
- [Política de segurança](../../SECURITY.md)
- [Decisão arquitetural atual](../decisions/0001-current-architecture.md)
