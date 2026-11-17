# Organização do repositório — Olokuti Digital

A aplicação utiliza uma organização modular Django, com configurações separadas por ambiente, templates, arquivos estáticos, traduções e testes.

| Caminho | Responsabilidade |
| --- | --- |
| `apps/accounts/` | Autenticação, usuários, grupos e permissões. |
| `apps/catalog/` | Produtos, categorias, traduções e comandos de catálogo. |
| `apps/operations/` | Tarefas e estados operacionais. |
| `apps/reports/` | Relatórios e exportações. |
| `apps/audit/` | Eventos de auditoria. |
| `config/settings/` | Configurações base, local, produção e testes. |
| `templates/` | Templates agrupados por área funcional. |
| `static/` | CSS e JavaScript. |
| `locale/` | Arquivos gettext por idioma. |
| `tests/` | Testes automatizados. |
| `requirements/` | Dependências de desenvolvimento e produção. |
| `assets/brand/` | Identidade visual do projeto. |

## Convenções

- Manter cada domínio dentro do app Django correspondente.
- Novas alterações de modelo devem considerar migrações e testes.
- Não versionar `.env`, credenciais, bancos locais ou dados reais.
- Preservar os arquivos `.po` como fonte das traduções e recompilar os arquivos `.mo` quando necessário.
- Não tratar registros sintéticos como dados observados ou oficiais.
