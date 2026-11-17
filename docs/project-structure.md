# Organização do repositório — Olokuti Digital

Este documento descreve a estrutura efetivamente adotada pelo repositório. A aplicação permanece um monólito modular Django: os domínios são separados em apps, mas compartilham o mesmo processo, configuração e banco PostgreSQL.

## Árvore de diretórios

```text
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/              # CI, CodeQL e verificação de saúde
│   └── PULL_REQUEST_TEMPLATE.md
├── apps/
│   ├── accounts/               # autenticação, usuários, grupos e permissões
│   ├── audit/                  # eventos de auditoria
│   ├── catalog/                # produtos, categorias, traduções e seed de demonstração
│   ├── operations/             # tarefas e estados operacionais
│   └── reports/                # relatórios e exportações
├── assets/
│   └── brand/                  # SVGs oficiais da identidade do projeto
├── config/
│   └── settings/               # configuração base e ambientes
├── docs/
│   ├── adr/                    # decisões arquiteturais registradas
│   ├── brand/                  # diretrizes da identidade visual
│   └── project-structure.md    # este documento
├── locale/                     # catálogos gettext .po/.mo por variante
├── requirements/               # dependências de desenvolvimento e produção
├── static/
│   ├── css/
│   └── js/
├── templates/                  # templates agrupados por domínio
├── tests/                      # testes automatizados
├── .env.example                # exemplo sem credenciais reais
├── manage.py
├── pyproject.toml              # pytest e Ruff
├── Procfile                    # comando WSGI
├── railway.json                # Config as Code; corte de suporte em 2026-12-01
├── render.yaml                 # Blueprint Render
├── vercel.json                 # configuração serverless experimental
└── README.md / README.en.md
```

## Responsabilidades e limites

| Diretório | Responsabilidade | Regra de manutenção |
| --- | --- | --- |
| `apps/` | Domínios de negócio Django | Não mover apps ou renomear modelos sem revisar imports, `INSTALLED_APPS`, URLs e migrações. |
| `config/` | WSGI, URLs e settings por ambiente | Segredos exclusivamente em variáveis de ambiente. |
| `templates/` | Apresentação HTML | Manter templates agrupados por domínio e estender a base comum. |
| `static/` | CSS e JavaScript próprios | Não versionar artefatos gerados de `collectstatic`. |
| `locale/` | Internacionalização gettext | `.po` é fonte; recompilar `.mo` após alterações. |
| `assets/brand/` | Identidade visual | Preservar nomes, proporções, paleta e referências usadas pelo README. |
| `tests/` | Testes de regressão | Acrescentar testes para regras, permissões, segurança e migrações relevantes. |
| `.github/` | Automação e governança | Revisar permissões mínimas dos workflows e manter CI reproduzível. |
| `docs/` | Arquitetura e decisões | Registrar decisões duradouras em ADRs, com contexto e consequências. |

## Fluxo arquitetural

1. A requisição HTTP chega às rotas Django em `config/urls.py`.
2. O app de domínio valida entrada por Forms e aplica as permissões necessárias.
3. A lógica de aplicação acessa os modelos via Django ORM.
4. O ORM comunica-se com PostgreSQL; SQLite em memória é usado pela suíte de testes.
5. Templates renderizam a interface; HTMX atualiza fragmentos quando aplicável.
6. WhiteNoise serve os arquivos estáticos coletados no build.

Os apps não são microserviços e não devem introduzir chamadas de rede internas entre si sem uma decisão arquitetural documentada.

## Convenções de desenvolvimento

- Python 3.12; executar `python -m ruff check .` e `python -m pytest -q` antes de integrar alterações.
- Manter dependências de runtime em `requirements/production.txt` e ferramentas de desenvolvimento em `requirements/development.txt`.
- Alterações em modelos devem incluir migrações e testes correspondentes.
- Nunca versionar `.env`, tokens, chaves, dumps de banco, dados pessoais ou credenciais.
- `.env.example` contém somente nomes e valores ilustrativos; não copiar valores de produção.
- Utilizar dados sintéticos nos testes e demonstrações. Não atribuir hipóteses ou registros fictícios à empresa estudada.
- Mudanças em permissões devem adotar o menor privilégio e incluir testes para usuários autorizados e não autorizados.
- Preservar variantes linguísticas regionais: `pt-BR`, `pt-PT`, `es-419`, `es-es`, `ca`, `gl`, `eu`, `en-us`, `en-gb` e `en`.
- Não mover diretórios ou renomear apps apenas por preferência estética; considerar compatibilidade com deploy, migrações e histórico Git.

## Configuração, execução e operações

- Leia o [README principal](../README.md) para instalar, configurar variáveis, executar testes e iniciar localmente.
- Consulte [SECURITY.md](../SECURITY.md) antes de relatar vulnerabilidades.
- Siga [CONTRIBUTING.md](../CONTRIBUTING.md) para preparar alterações.
- Consulte [diretrizes de identidade visual](brand/README.md) antes de alterar os SVGs.
- Antes de criar ou modificar deployments, valide os comandos e o formato de configuração diretamente no provedor. A presença de um arquivo YAML/JSON no repositório não comprova que um serviço esteja ativo nem que a configuração ainda seja aceita pelo provedor.

## Política de mudança estrutural

Uma mudança que mova arquivos deve ser feita em commit dedicado, preservar o histórico sempre que possível e incluir validação de imports, testes, build e deploy. Não misturar refatoração de diretórios com alterações funcionais ou de segurança no mesmo commit, salvo necessidade justificada.
