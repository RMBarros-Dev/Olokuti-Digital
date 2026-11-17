<h1 align="center">Olokuti Digital</h1>

<p align="center">
  MVP acadêmico e experimental para explorar fluxos de catálogo, tarefas e organização operacional.<br>
  <strong>Aplicação online:</strong> <a href="https://olokuti-web-production.up.railway.app/">https://olokuti-web-production.up.railway.app/</a>
</p>

<p align="center">
  <a href="https://olokuti-web-production.up.railway.app/"><img src="https://img.shields.io/badge/Demo%20Online-Railway-0B0D0E?logo=railway&logoColor=white" alt="Aplicação Online no Railway"></a>
  <a href="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/ci.yml"><img src="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/ci.yml/badge.svg?branch=main" alt="Status da CI"></a>
  <a href="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/keepalive.yml"><img src="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/keepalive.yml/badge.svg?branch=main" alt="Keep-Alive 24/7"></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white" alt="Django 5.2">
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?logo=supabase&logoColor=white" alt="PostgreSQL Supabase">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/RMBarros-Dev/Olokuti-Digital" alt="Licença MIT"></a>
</p>

> **Status: MVP acadêmico e experimental.** Este projeto não é um sistema oficial da Olokuti, não tem afiliação ou aprovação institucional declarada e não se conecta a sistemas da empresa. Necessidades, processos e valor operacional são hipóteses **a validar mediante investigação de campo**.

## Índice

- [Contexto e objetivo](#contexto-e-objetivo)
- [Escopo funcional](#escopo-funcional)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Começar localmente](#começar-localmente)
- [Configuração](#configuração)
- [Contas, grupos e permissões](#contas-grupos-e-permissões)
- [Testes e integração contínua](#testes-e-integração-contínua)
- [Idiomas e traduções](#idiomas-e-traduções)
- [Deploy e operação](#deploy-e-operação)
- [Segurança, dados e limitações](#segurança-dados-e-limitações)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Contribuição e licença](#contribuição-e-licença)

## Contexto e objetivo

O projeto foi concebido no contexto da investigação **“Da identidade à inovação: memória, diagnóstico operacional e transformação digital do comércio sustentável em Barcelona — estudo de caso da Olokuti”**. A aplicação oferece um ambiente de prototipagem para avaliar conceitos de catálogo, tarefas e relatórios; ela não pressupõe que a empresa precise dessas funcionalidades.

O princípio de trabalho é separar fatos observados de hipóteses. Integrações, dados, requisitos, processos e identidade institucional só devem ser incorporados após evidência, autorização e validação adequadas.

## Escopo funcional

| Área | O que o MVP oferece |
| --- | --- |
| Acesso e IAM | Login, cadastro básico de menor privilégio (`/accounts/register/`), logout, controle RBAC por grupos/permissões, invalidação de sessão em alterações críticas e redefinição de senha. |
| Acessibilidade | Alternador global de **Alto Contraste (WCAG 2.2 AA/AAA)** no cabeçalho (`#high-contrast-toggle`), persistência em `localStorage`, atalho Skip to content, foco visível reforçado, suporte a `prefers-reduced-motion` e região `aria-live`. |
| Dashboard | Resumo de produtos, estoque baixo, tarefas e atividade recente, condicionado às permissões do usuário. |
| Catálogo | Produtos com SKU único parcial, código de barras, preço/moeda (`EUR`, `BRL`, `USD`, `GBP`, `INR`), atributos JSON, ativação/inativação, pesquisa HTMX, histórico e exportação CSV segura. |
| Traduções de produtos | Registros localizados separados do texto original, sem substituir os dados-fonte. |
| Inventário | Locais de estoque (`StockLocation`), saldos com bloqueio transacional (`select_for_update`), movimentações imutáveis (`StockMovement`: entrada, saída e ajuste), alertas de estoque mínimo e CSV. |
| Operações | Tarefas com categoria, produto opcional, responsável, prioridade, prazo, página de detalhes, comentários colaborativos (`TaskComment`), histórico e filtros/status com HTMX. |
| Relatórios | Resumo por período, status, atividade por colaborador e estoque por localização, com exportação CSV protegida contra fórmulas e geração nativa de relatório **PDF** (`%PDF-1.4`). |
| Auditoria | Eventos de criação, atualização, mudança de status, exclusão, movimentações de estoque, comentários e alterações administrativas (`AuditedAdminMixin`). |
| Administração | Gestão de contas e grupos (`is_staff`, com proteção de escalonamento de superusuário e invalidação automática de sessões). |
| Idiomas | Prefixos de URL e seletor para 11 idiomas/variantes, incluindo `en-in` (`English (India)`), com suporte a compilação via GNU gettext ou comando integrado `compile_locales`. |
| Saúde e segurança | `GET /health`, `GET /health?db=1` (rate-limited), cabeçalhos CSP com `nonce`, `Permissions-Policy`, rate limiting de autenticação e validação rígida de produção. |

### Fora do escopo

Este MVP não implementa pagamentos, vendas, faturamento, gestão financeira, emissão fiscal ou conexão direta com sistemas legados da Olokuti. Não é uma API pública nem substitui um ERP completo.

O comando `seed_demo` é opcional, só executa com `DEBUG=True` e cria registros sintéticos identificados como demonstração. Origens, certificações, fornecedores e afirmações de sustentabilidade desses registros não são verificadas.

## Arquitetura

Aplicação monolítica modular em Django 5.2 com separação explícita entre **Models / QuerySets**, **Services** (regras transacionais e auditoria), **Selectors** (consultas otimizadas sem N+1) e **Views/Templates**:

```mermaid
flowchart LR
    Browser[Navegador<br/>Templates, Bootstrap, Alto Contraste e HTMX] --> Middleware[SecurityHeadersMiddleware CSP Nonce + ActiveUser]
    Middleware --> Django[Django Urls / Views / Forms]
    Django --> Accounts[accounts]
    Django --> Catalog[catalog]
    Django --> Inventory[inventory]
    Django --> Operations[operations]
    Django --> Reports[reports]
    Django --> Audit[audit]
    Inventory --> Services[Services & Selectors<br/>select_for_update + atomic]
    Catalog --> Services
    Operations --> Services
    Reports --> PDF[config/csv.py & config/pdf.py]
    Services --> ORM[Django ORM]
    ORM --> PostgreSQL[(PostgreSQL / Supabase)]
    Django --> WhiteNoise[WhiteNoise<br/>arquivos estáticos]
    WhiteNoise --> Browser
```

Os módulos têm responsabilidades delimitadas:

| Módulo | Responsabilidade |
| --- | --- |
| `apps/accounts` | Dashboard, autenticação, rate limiting, RBAC, grupos e gestão segura de usuários. |
| `apps/catalog` | Categorias, produtos (SKU, preço, atributos JSON, ativação), traduções, histórico e CSV. |
| `apps/inventory` | Locais de estoque, saldos por local, movimentações atômicas/imutáveis, alertas mínimos e CSV. |
| `apps/operations` | Tarefas, categorias, filtros HTMX, atualização rápida de status e comentários colaborativos. |
| `apps/reports` | Indicadores operacionais/colaboradores/estoque, exportação CSV e relatório PDF puro em Python. |
| `apps/audit` | Modelo de trilha de auditoria, serviço `record_event`, `AuditedAdminMixin` e visualização. |
| `config/` | Settings modulares, validador de produção, middleware CSP/segurança, CSV e gerador PDF. |
| `docs/` | Documentação arquitetural ([`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)) e runbook operacional ([`docs/OPERATIONS_RUNBOOK.md`](docs/OPERATIONS_RUNBOOK.md)). |

## Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Linguagem e runtime | Python 3.12 |
| Backend | Django 5.2, Django ORM, Forms, Templates e autenticação nativa |
| Banco local e produção | PostgreSQL 14 ou superior; SQLite em memória nos testes |
| Interface | HTML, CSS, Bootstrap 5.3.9, HTMX 2.0.11 e JavaScript nativo |
| Arquivos estáticos | WhiteNoise |
| Servidor WSGI | Gunicorn |
| Qualidade | pytest, pytest-django e Ruff |
| Deploy configurado | Railpack/Railway; consulte a seção [Deploy e operação](#deploy-e-operação) sobre o formato atual de configuração |

Django 5.2 requer PostgreSQL 14 ou superior ([notas oficiais da versão 5.2](https://docs.djangoproject.com/en/5.2/releases/5.2/)). Docker, Node.js, Redis e microserviços não são requisitos para desenvolvimento local.

## Começar localmente

### Pré-requisitos

- Python 3.12 e `pip`;
- PostgreSQL 14 ou superior, com uma base vazia para o projeto;
- Git;
- GNU gettext apenas se você for extrair ou recompilar traduções;
- acesso à internet para os arquivos Bootstrap e HTMX carregados pelos CDNs do layout.

### 1. Criar a base local

No `psql`, com uma conta administrativa do PostgreSQL:

```sql
CREATE ROLE olokuti WITH LOGIN PASSWORD 'defina-uma-senha-local';
CREATE DATABASE olokuti_digital OWNER olokuti;
```

### 2. Criar o ambiente Python

No PowerShell, a partir da raiz do repositório:

```powershell
py -3.12 -m venv .venv
Copy-Item .env.example .env
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/development.txt
```

Se a ativação do ambiente virtual estiver bloqueada pela política local do PowerShell, use diretamente `.\.venv\Scripts\python.exe` no lugar de `python` nos comandos seguintes.

### 3. Configurar e iniciar

Edite `.env` e substitua os valores de exemplo. Use uma senha URL-encoded na `DATABASE_URL` se ela contiver caracteres especiais. O `.env` é ignorado pelo Git; não o adicione ao repositório.

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse [http://127.0.0.1:8000/](http://127.0.0.1:8000/). A raiz redireciona para o prefixo do idioma ativo; com a configuração padrão, o login fica em [`/en/accounts/login/`](http://127.0.0.1:8000/en/accounts/login/). O e-mail de redefinição de senha é enviado ao console no ambiente local.

Para criar dados sintéticos para uma demonstração local, execute `python manage.py seed_demo` com `DEBUG=True`. O comando avisa que os registros são fictícios e recusa execução fora do modo de depuração.

## Configuração

As configurações locais são carregadas de `.env` pelo `python-dotenv`. Em produção, defina-as como variáveis protegidas no provedor; não publique segredos no GitHub.

| Variável | Uso |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.local` localmente; `config.settings.production` em produção. |
| `DJANGO_SECRET_KEY` | Chave secreta longa e exclusiva por ambiente. O valor de exemplo não deve ser usado em produção. |
| `DATABASE_URL` | URL PostgreSQL local ou de produção. SQLite é aceito para testes; a configuração de produção exige PostgreSQL. |
| `DJANGO_ALLOWED_HOSTS` | Lista de hosts permitidos separada por vírgula. Produção recusa `*`. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origens confiáveis completas, incluindo `https://`, separadas por vírgula. Obrigatória em produção. |
| `DJANGO_EMAIL_BACKEND` | Backend de e-mail. O modo local usa o console; produção usa SMTP por padrão. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | Configuração do provedor SMTP autorizado. `EMAIL_HOST` é obrigatório quando o backend de produção é SMTP. |
| `DEFAULT_FROM_EMAIL` | Endereço remetente usado nas mensagens. |
| `DJANGO_TRUST_PROXY_SSL_HEADER` | Ative como `true` somente atrás de um proxy confiável que filtre e defina `X-Forwarded-Proto`. |
| `DJANGO_HSTS_SECONDS` | Duração do HSTS em segundos; o padrão de produção é um ano. |

`config.settings.production` mantém `DEBUG=False`, exige chave, PostgreSQL, hosts explícitos e origens CSRF confiáveis. HTTPS, cookies seguros e HSTS são configurados nessa camada.

## Contas, grupos e permissões

Na tela de login (`/accounts/login/`), novos usuários podem se cadastrar diretamente clicando em **Criar conta** (`/accounts/register/`). Seguindo o princípio do menor privilégio, o cadastro público cria uma conta básica: o usuário não recebe grupos automaticamente e não recebe permissões operacionais ou administrativas automaticamente; a atribuição de grupos e permissões é feita por administradores autorizados.

Para avaliação rápida, consulte o ambiente de demonstração online ([https://olokuti-web-production.up.railway.app/](https://olokuti-web-production.up.railway.app/)). **Não são publicadas credenciais administrativas neste repositório.** O acesso administrativo deve ser provisionado pelo responsável pelo ambiente, por canal seguro e com credenciais exclusivas; não reutilize credenciais de demonstração.

Usuários com acesso administrativo autorizado podem acessar o Django Admin e a gestão de contas pela interface em `/en/accounts/users/`. Na própria página, a ação de configurar grupos cria os grupos padrão e acrescenta as permissões-base sem remover permissões personalizadas existentes.

| Grupo padrão | Permissões incluídas |
| --- | --- |
| `Catalogue Team` | Visualizar, criar, editar e excluir produtos e categorias; visualizar locais e saldos de estoque. |
| `Operations Team` | Visualizar produtos, tarefas, comentários, locais/saldos de estoque; criar/editar/excluir tarefas e comentários; registrar movimentações de estoque (`add_stockmovement`). |
| `Auditors & Managers` | Administrar produtos, tarefas, comentários, locais/limites de estoque, movimentações e visualizar eventos de auditoria. |

Permissões usadas pelas áreas:

- Produtos: `catalog.view_product`, `catalog.add_product`, `catalog.change_product`, `catalog.delete_product`.
- Categorias: `catalog.view_category`, `catalog.add_category`, `catalog.change_category`, `catalog.delete_category`.
- Inventário: `inventory.view_stocklocation`, `inventory.add_stocklocation`, `inventory.change_stocklocation`, `inventory.view_stockitem`, `inventory.change_stockitem`, `inventory.view_stockmovement`, `inventory.add_stockmovement`.
- Tarefas e comentários: `operations.view_operationaltask`, `operations.add_operationaltask`, `operations.change_operationaltask`, `operations.delete_operationaltask`, `operations.view_taskcomment`, `operations.add_taskcomment`.
- Auditoria: `audit.view_auditlog`.
- Relatórios: `operations.view_operationaltask` **e** `catalog.view_product` (exportação CSV de estoque requer adicionalmente `inventory.view_stockitem`).
- Gestão de usuários: requer `is_staff` (edição de `is_superuser` e atribuição do grupo de auditoria restritas a superusuários).

A exclusão de categorias é bloqueada enquanto houver produtos relacionados. O dashboard oculta métricas sem permissão correspondente.

## Testes e integração contínua

Execute os mesmos verificadores usados no workflow do GitHub:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov=apps --cov=config --cov-report=term-missing --cov-fail-under=90
```

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda Ruff (`check` + `format --check`), verificação de dependências (`pip check`), `manage.py check`, `makemigrations --check --dry-run`, `check --deploy --fail-level WARNING` e pytest com meta mínima de 90% de cobertura em Python 3.12.

## Idiomas e traduções

Os prefixos configurados são `es-419`, `es-es`, `ca`, `gl`, `eu`, `en-us`, `en-gb`, `en-in`, `en`, `pt-br` e `pt-pt`. Todos os `.po` possuem catálogos compilados `.mo` versionados; execute `python manage.py compile_locales` para recompilar (com fallback puro em Python quando GNU gettext não estiver disponível no sistema).

Consulte também [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) e [`docs/OPERATIONS_RUNBOOK.md`](docs/OPERATIONS_RUNBOOK.md) para detalhes operacionais, cache, pooler Supabase e procedimentos de backup/rollback.

## Deploy e operação

- **Ambiente de demonstração online (24/7):** [https://olokuti-web-production.up.railway.app/](https://olokuti-web-production.up.railway.app/)
- **Verificação de saúde e banco (Supabase PostgreSQL):** [https://olokuti-web-production.up.railway.app/health?db=1](https://olokuti-web-production.up.railway.app/health?db=1)

### Railway

O repositório contém `railway.json` com comandos para coleta de arquivos estáticos, migrações pré-deploy, Gunicorn, healthcheck `/health` e política de reinício. O arquivo não cria um projeto Railway, banco de dados, domínio ou variáveis e não comprova que exista um deployment ativo.

**Atenção ao formato:** em **12 de novembro de 2026**, Railway marca Config as Code (`railway.json`/`railway.toml`) como obsoleto. Arquivos existentes continuam válidos apenas para serviços que já os utilizam, com corte previsto para **1º de dezembro de 2026**; novos serviços não podem optar por esse formato. Consulte a [documentação Railway](https://docs.railway.com/config-as-code) e a [migração para Infrastructure as Code](https://docs.railway.com/infrastructure-as-code) antes de criar ou atualizar o serviço.

Para um serviço existente que ainda usa esse arquivo, o Railpack detecta `requirements.txt`; o comando de build recolhe estáticos, o comando pré-deploy executa `migrate` e o servidor inicia com Gunicorn na porta `$PORT`. Para um serviço novo, configure os comandos nas definições do Railway ou migre a configuração para o mecanismo IaC atual.

Variáveis de produção necessárias no serviço:

1. `DJANGO_SETTINGS_MODULE=config.settings.production`
2. `DJANGO_SECRET_KEY`: segredo forte, exclusivo de produção.
3. `DATABASE_URL`: PostgreSQL de produção previamente criado e autorizado.
4. `DJANGO_ALLOWED_HOSTS`: domínio Railway atribuído, sem protocolo e sem `*`.
5. `DJANGO_CSRF_TRUSTED_ORIGINS`: origem completa do domínio, por exemplo `https://seu-dominio.up.railway.app`.
6. `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS=true` e `DEFAULT_FROM_EMAIL` para SMTP.

Depois que o domínio for criado, inclua-o em `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS` e faça novo deploy. `healthcheck.railway.app` já está permitido para o healthcheck. A configuração não provisiona banco nem migra dados entre provedores.

Para configurar os comandos manualmente no painel:

| Campo do serviço | Comando ou valor |
| --- | --- |
| Build | `python manage.py collectstatic --noinput` |
| Pre-deploy | `python manage.py migrate --noinput` |
| Start | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -` |
| Healthcheck path | `/health` |

### Render, Vercel e Keep-Alive 24/7 (Supabase)

Além do `railway.json`, o repositório inclui configurações prontas para hospedagem gratuita permanente conectada ao **Supabase PostgreSQL**:

- **`render.yaml` (Render Blueprint):** configura o serviço web Python gratuito (`gunicorn` + `collectstatic` + `migrate`) com healthcheck em `/health`.
- **`vercel.json` (Vercel Serverless WSGI):** expõe `config/wsgi.py` (`app = application`) para execução serverless sem hibernação de container.
- **`.github/workflows/keepalive.yml` (Monitoramento & Keep-Alive 24/7):** executa automaticamente a cada 6 horas um `GET /health?db=1` (que realiza `SELECT 1` no PostgreSQL), mantendo o serviço web aquecido e impedindo a pausa automática de 7 dias por inatividade no plano gratuito do Supabase. Para apontar para um novo domínio (como Render ou Vercel), basta definir a variável de repositório `APP_HEALTHCHECK_URL` em *Settings → Secrets and variables → Actions → Variables*.

### Arquivos estáticos, logs e backups

WhiteNoise serve os arquivos recolhidos em `STATIC_ROOT`; o build de produção precisa executar `collectstatic`. Os logs são enviados a stdout/stderr em formato JSON. Não inclua dados pessoais ou conteúdo de tarefas em mensagens de log.

Para PostgreSQL, defina backups periódicos em destino protegido e criptografado, com credencial de menor privilégio. Retenha cópias de acordo com a política aplicável e teste uma restauração antes de depender do backup. Não coloque senhas em comandos, histórico do terminal, documentação ou arquivos versionados.

## Segurança, dados e limitações

- Não use dados pessoais ou operacionais reais sem autorização e salvaguardas apropriadas.
- Não trate exemplos, hipóteses, origens ou certificações como fatos sobre a Olokuti.
- Não há integração com sistemas da empresa nem validação institucional do produto.
- Os eventos de auditoria ficam na mesma base da aplicação; não são um registro inviolável nem guardam snapshots completos das alterações.
- Bootstrap e HTMX são carregados de CDNs. Ambientes restritos precisam disponibilizar esses arquivos localmente.
- Traduções de interface são parciais e não passaram por revisão humana completa.
- Os testes não validam uma conexão real de produção com PostgreSQL.
- `railway.json` está em formato legado e requer migração ou configuração atualizada do serviço para deployments novos/após o período de compatibilidade.

Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md) para as regras de contribuição e tratamento de dados de demonstração. Não publique credenciais ou detalhes exploráveis em issues públicas.

## Estrutura do repositório

```text
.
├── apps/
│   ├── accounts/       # autenticação, grupos, dashboard e usuários
│   ├── audit/          # eventos de auditoria e AuditedAdminMixin
│   ├── catalog/        # produtos (SKU, preço, atributos), categorias, traduções
│   ├── inventory/      # locais, saldos, movimentações atômicas e alertas
│   ├── operations/     # tarefas, categorias, comentários e status
│   └── reports/        # resumos, produtividade, CSV e PDF
├── config/
│   ├── csv.py          # exportação CSV protegida contra injeção de fórmulas
│   ├── middleware.py   # CSP com nonce, Permissions-Policy e usuário ativo
│   ├── pdf.py          # gerador PDF multi-página sem dependências externas
│   └── settings/       # base, local, test, production e validators
├── docs/               # arquitetura e runbook de operação/backup/rollback
├── locale/             # catálogos gettext .po/.mo (11 idiomas incl. en_IN)
├── static/             # CSS e JavaScript
├── templates/          # templates Django
├── tests/              # testes automatizados
├── requirements/       # dependências de produção e desenvolvimento
├── .github/workflows/  # CI e Keep-Alive 24/7
├── .env.example
├── manage.py
├── Procfile
├── railway.json        # configuração Railway legada
├── render.yaml         # Render Blueprint (hospedagem gratuita)
├── vercel.json         # Vercel Serverless Python WSGI
└── pyproject.toml      # configuração do pytest e Ruff
```

## Contribuição e licença

Leia [`CONTRIBUTING.md`](CONTRIBUTING.md) antes de enviar alterações. Toda contribuição deve manter explícita a natureza experimental do MVP e evitar dados ou afirmações não verificadas.

O código original e a documentação deste repositório estão sob a [licença MIT](LICENSE). Ela não concede direitos sobre marcas, nomes, logotipos, dados ou materiais de terceiros. O nome “Olokuti” identifica o contexto acadêmico e não implica afiliação ou aprovação institucional.
