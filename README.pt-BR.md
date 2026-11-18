<p align="right"><strong>Idioma:</strong> <a href="README.pt-BR.md">Português (Brasil)</a> · <a href="README.md">English</a></p>

<p align="center">
  <img src="assets/brand/banner.svg" alt="Olokuti Digital — catálogo, tarefas e organização operacional" width="100%" />
</p>

<p align="center"><img src="assets/brand/logo.svg" alt="Olokuti Digital logo" width="76" /></p>

<h1 align="center">Olokuti Digital</h1>

<p align="center">
  MVP acadêmico e experimental para explorar fluxos de catálogo, tarefas e organização operacional.<br><strong>Informação organizada. Operações conectadas.</strong><br>
  <strong>URL do ambiente de demonstração:</strong> <a href="https://olokuti-web-production.up.railway.app/">https://olokuti-web-production.up.railway.app/</a>
</p>

<p align="center">
  <a href="https://olokuti-web-production.up.railway.app/"><img src="https://img.shields.io/badge/Demo%20URL-Railway-0B0D0E?logo=railway&logoColor=white" alt="URL do ambiente de demonstração no Railway"></a>
  <a href="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/ci.yml"><img src="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/ci.yml/badge.svg?branch=main" alt="Status da CI"></a>
  <a href="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/keepalive.yml"><img src="https://github.com/RMBarros-Dev/Olokuti-Digital/actions/workflows/keepalive.yml/badge.svg?branch=main" alt="Health Check"></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white" alt="Django 5.2">
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?logo=supabase&logoColor=white" alt="PostgreSQL Supabase">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/RMBarros-Dev/Olokuti-Digital" alt="Licença MIT"></a>
</p>

> **Status: MVP acadêmico e experimental.** Este projeto não é um sistema oficial da Olokuti, não tem afiliação ou aprovação institucional declarada e não se conecta a sistemas da empresa. Necessidades, processos e valor operacional são hipóteses **a validar mediante investigação de campo**.

## Índice

- [01 · Contexto e objetivo](#01--contexto-e-objetivo)
- [02 · Escopo funcional](#02--escopo-funcional)
- [03 · Fora do escopo](#03--fora-do-escopo)
- [04 · Área de aplicação e metodologia de desenvolvimento](#04--área-de-aplicação-e-metodologia-de-desenvolvimento)
- [05 · Arquitetura](#05--arquitetura)
- [06 · Tecnologias](#06--tecnologias)
- [07 · Começar localmente](#07--começar-localmente)
- [08 · Configuração](#08--configuração)
- [09 · Contas, grupos e permissões](#09--contas-grupos-e-permissões)
- [10 · Testes e integração contínua](#10--testes-e-integração-contínua)
- [11 · Idiomas e traduções](#11--idiomas-e-traduções)
- [12 · Deploy e operação](#12--deploy-e-operação)
- [13 · Arquivos estáticos, logs e backups](#13--arquivos-estáticos-logs-e-backups)
- [14 · Documentação do projeto](#14--documentação-do-projeto)
- [15 · Princípios de engenharia](#15--princípios-de-engenharia)
- [16 · Segurança, dados e limitações](#16--segurança-dados-e-limitações)
- [17 · Estrutura do repositório](#17--estrutura-do-repositório)
- [18 · Contribuição e licença](#18--contribuição-e-licença)

## 01 · Contexto e objetivo

O projeto foi concebido no contexto da investigação **“Da identidade à inovação: memória, diagnóstico operacional e transformação digital do comércio sustentável em Barcelona — estudo de caso da Olokuti”**. A aplicação oferece um ambiente de prototipagem para avaliar conceitos de catálogo, tarefas e relatórios; ela não pressupõe que a empresa precise dessas funcionalidades.

O princípio de trabalho é separar fatos observados de hipóteses. Integrações, dados, requisitos, processos e identidade institucional só devem ser incorporados após evidência, autorização e validação adequadas.

## 02 · Escopo funcional

| Área | O que o MVP oferece |
| --- | --- |
| Acesso | Login, criação de conta (`/accounts/register/`), logout, sessões e fluxo de redefinição de senha do Django. |
| Dashboard | Resumo de produtos, tarefas e atividade recente, condicionado às permissões do usuário. |
| Catálogo | Produtos, categorias, pesquisa, filtros, origem, informações de sustentabilidade e exportação CSV. |
| Traduções de produtos | Registros localizados separados do texto original, sem substituir os dados-fonte. |
| Operações | Tarefas com produto opcional, responsável, prioridade, prazo e estados; filtros e atualização rápida de status com HTMX. |
| Relatórios | Resumo de tarefas por período e status, com exportação CSV protegida contra fórmulas de planilha. |
| Auditoria | Eventos mínimos de criação, atualização, mudança de status, exclusão e configuração. |
| Administração | Listagem, pesquisa, criação e edição de contas por usuários `is_staff`; grupos com permissões do Django. |
| Idiomas | Prefixos de URL e seletor para dez idiomas; os catálogos de interface são parciais. |
| Saúde da aplicação | `GET /health` retorna `200 OK`; `GET /health?db=1` valida também a conexão SQL ativa com o PostgreSQL. |

## 03 · Fora do escopo

Este MVP não implementa pagamentos, vendas, faturamento, gestão financeira, sincronização de inventário, integração omnicanal ou conexão com sistemas da Olokuti. Não é uma API pública nem um sistema pronto para uso operacional.

O comando `seed_demo` é opcional, só executa com `DEBUG=True` e cria registros sintéticos identificados como demonstração. Origens, certificações, fornecedores e afirmações de sustentabilidade desses registros não são verificadas.

## 04 · Área de aplicação e metodologia de desenvolvimento

O MVP explora fluxos de informação de catálogo e coordenação de tarefas para um contexto de operação comercial. O desenvolvimento é incremental e acadêmico: requisitos e hipóteses são documentados, implementações são divididas por módulos Django e comportamentos relevantes são cobertos por testes automatizados. O valor operacional e a adequação dos fluxos dependem de validação de campo; o protótipo não declara representar processos reais da empresa citada.

## 05 · Arquitetura

Aplicação monolítica modular: o navegador acessa rotas Django; os módulos usam o ORM e a mesma base PostgreSQL; templates renderizam a interface e HTMX atualiza partes das listas. WhiteNoise publica os arquivos estáticos recolhidos no build.

```mermaid
flowchart LR
    Browser[Navegador<br/>Templates, Bootstrap e HTMX] --> Django[Django<br/>URLs, Forms e autenticação]
    Django --> Accounts[accounts]
    Django --> Catalog[catalog]
    Django --> Operations[operations]
    Django --> Reports[reports]
    Django --> Audit[audit]
    Accounts --> ORM[Django ORM]
    Catalog --> ORM
    Operations --> ORM
    Reports --> ORM
    Audit --> ORM
    ORM --> PostgreSQL[(PostgreSQL)]
    Django --> WhiteNoise[WhiteNoise<br/>arquivos estáticos]
    WhiteNoise --> Browser
```

Os módulos têm responsabilidades delimitadas:

| Módulo | Responsabilidade |
| --- | --- |
| `apps/accounts` | Dashboard, autenticação, grupos, permissões e administração de usuários. |
| `apps/catalog` | Categorias, produtos, traduções localizadas e CSV do catálogo. |
| `apps/operations` | Tarefas, filtros, mudanças de status e eventos operacionais. |
| `apps/reports` | Agregações e exportação de relatórios de tarefas. |
| `apps/audit` | Modelo, serviço e visualização dos eventos de auditoria. |
| `config/settings` | Configurações compartilhadas, local, de testes e produção. |

## 06 · Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Linguagem e runtime | Python 3.12 |
| Backend | Django 5.2, Django ORM, Forms, Templates e autenticação nativa |
| Banco local e produção | PostgreSQL 14 ou superior; SQLite em memória nos testes |
| Interface | HTML, CSS, Bootstrap 5.3.9, HTMX 2.0.11 e JavaScript nativo |
| Arquivos estáticos | WhiteNoise |
| Servidor WSGI | Gunicorn |
| Qualidade | pytest, pytest-django e Ruff |
| Deploy configurado | Railpack/Railway; consulte a seção [Deploy e operação](#12--deploy-e-operação) sobre o formato atual de configuração |

Django 5.2 requer PostgreSQL 14 ou superior ([notas oficiais da versão 5.2](https://docs.djangoproject.com/en/5.2/releases/5.2/)). Docker, Node.js, Redis e microserviços não são requisitos para desenvolvimento local.

## 07 · Começar localmente

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

## 08 · Configuração

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

## 09 · Contas, grupos e permissões

Na tela de login (`/accounts/login/`), novos usuários podem se cadastrar diretamente clicando em **Criar conta** (`/accounts/register/`). Seguindo o princípio do menor privilégio, o cadastro público cria uma conta básica, sem grupos ou permissões operacionais automáticos. A atribuição de grupos e permissões é uma ação administrativa explícita, realizada após análise da conta.

O acesso administrativo é reservado a usuários autorizados com `is_staff`. Não publique usuários, senhas ou credenciais de demonstração neste README. Para avaliação do ambiente online, solicite um acesso temporário por canal privado e revogue-o após o uso.

O superusuário acessa o Django Admin e a gestão de contas pela interface em `/en/accounts/users/`. Na própria página, a ação de configurar grupos cria os grupos padrão e acrescenta as permissões-base sem remover permissões personalizadas existentes.

| Grupo padrão | Permissões incluídas |
| --- | --- |
| `Catalogue Team` | Visualizar, criar, editar e excluir produtos e categorias. |
| `Operations Team` | Visualizar produtos e visualizar, criar, editar e excluir tarefas. |
| `Auditors & Managers` | Visualizar e administrar produtos e tarefas, além de visualizar eventos de auditoria. **Esse grupo não é somente leitura.** |

Permissões usadas pelas áreas:

- Produtos: `catalog.view_product`, `catalog.add_product`, `catalog.change_product`, `catalog.delete_product`.
- Categorias: `catalog.view_category`, `catalog.add_category`, `catalog.change_category`, `catalog.delete_category`.
- Tarefas: `operations.view_operationaltask`, `operations.add_operationaltask`, `operations.change_operationaltask`, `operations.delete_operationaltask`.
- Auditoria: `audit.view_auditlog`.
- Relatórios: requerem visualização de produtos **e** tarefas.
- Gestão de usuários: requer `is_staff`.

A exclusão de categorias é bloqueada enquanto houver produtos relacionados. O dashboard oculta métricas sem permissão correspondente.

## 10 · Testes e integração contínua

Execute os mesmos verificadores usados no workflow do GitHub:

```powershell
python -m ruff check .
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
python -m pytest -q
```

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) executa Ruff, verificações do Django, detecção de migrações pendentes e pytest em Python 3.12 para pushes em `main` e pull requests. O Dependabot verifica semanalmente dependências Python e GitHub Actions.

Os testes usam `config.settings.test` e SQLite em memória. Eles cobrem autenticação, permissões, catálogo, traduções de produtos, tarefas, relatórios, auditoria, contas e segurança da exportação CSV. A suíte não valida conectividade com o PostgreSQL do provedor nem substitui uma verificação do ambiente de produção.

## 11 · Idiomas e traduções

Os prefixos configurados são `es-419`, `es-es`, `ca`, `gl`, `eu`, `en-us`, `en-gb`, `en`, `pt-br` e `pt-pt`. Os catálogos contêm traduções parciais e ainda precisam de revisão linguística humana; a interface pode exibir texto em inglês quando não houver tradução.

Os arquivos `.po` são a fonte editável e os `.mo` compilados estão versionados. O comando `python manage.py compile_locales` delega ao `compilemessages` do Django e não reescreve os `.po`. Para extrair novas strings e compilar, instale GNU gettext e execute:

```powershell
python manage.py makemessages -a
# Revise os arquivos locale/<idioma>/LC_MESSAGES/django.po.
python manage.py compile_locales
```

`ProductTranslation` mantém nome, descrição e informação de sustentabilidade separados do produto original. A aplicação só seleciona uma tradução da mesma variante regional; por exemplo, `pt-BR` não usa automaticamente uma tradução `pt-PT`.

## 12 · Deploy e operação

- **URL publicada do ambiente de demonstração:** [https://olokuti-web-production.up.railway.app/](https://olokuti-web-production.up.railway.app/). A disponibilidade atual deve ser confirmada no provedor.
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

### Render, Vercel e Health Check (Supabase)

Além do `railway.json`, o repositório inclui configurações prontas para hospedagem gratuita permanente conectada ao **Supabase PostgreSQL**:

- **`render.yaml` (Render Blueprint):** configura o serviço web Python gratuito (`gunicorn` + `collectstatic` + `migrate`) com healthcheck em `/health`.
- **`vercel.json` (Vercel Serverless WSGI):** configura a entrada WSGI `config/wsgi.py` (`app = application`) para uma implantação baseada em funções serverless. Isso não elimina cold starts nem comprova adequação operacional sem testes no provedor.
- **`.github/workflows/keepalive.yml` (verificação periódica):** executa a cada 6 horas um `GET /health?db=1`, que valida a conexão PostgreSQL com `SELECT 1`. A URL pode ser alterada pela variável `APP_HEALTHCHECK_URL` em *Settings → Secrets and variables → Actions → Variables*. Essa chamada confirma conectividade no momento da execução; não deve ser tratada como garantia de disponibilidade contínua nem como garantia de que um provedor não suspenderá um serviço.

## 13 · Arquivos estáticos, logs e backups

WhiteNoise serve os arquivos recolhidos em `STATIC_ROOT`; o build de produção precisa executar `collectstatic`. Os logs são enviados a stdout/stderr em formato JSON. Não inclua dados pessoais ou conteúdo de tarefas em mensagens de log.

Para PostgreSQL, defina backups periódicos em destino protegido e criptografado, com credencial de menor privilégio. Retenha cópias de acordo com a política aplicável e teste uma restauração antes de depender do backup. Não coloque senhas em comandos, histórico do terminal, documentação ou arquivos versionados.

## 14 · Documentação do projeto

- [Índice da documentação técnica](docs/README.md).
- [Arquitetura técnica](docs/architecture/README.md).
- [Estrutura dos diretórios](docs/project-structure.md).
- [Tecnologias e linguagens](docs/technology-stack.md).
- [Metodologia de desenvolvimento](docs/development-methodology.md).
- [Qualidade, testes e badges](docs/quality/README.md).
- [Roadmap de evolução](docs/roadmap.md).
- [Repositórios de referência](docs/reference-projects.md).
- [Identidade visual](docs/brand/README.md).
- [Guia de contribuição](CONTRIBUTING.md).
- [Política de segurança](SECURITY.md).
- [Configuração de exemplo](.env.example), sem segredos reais.
- [Configuração de qualidade](pyproject.toml).
- [Guia de traduções](locale/README.md).
- [Workflow de integração contínua](.github/workflows/ci.yml).

## 15 · Princípios de engenharia

O projeto procura manter separação por domínio, permissões explícitas, configurações distintas por ambiente, testes automatizados e documentação que diferencia dados sintéticos de informações observadas. A auditoria registrada pela aplicação não deve ser interpretada como trilha imutável ou certificação independente.

## 16 · Segurança, dados e limitações

- Não use dados pessoais ou operacionais reais sem autorização e salvaguardas apropriadas.
- Não trate exemplos, hipóteses, origens ou certificações como fatos sobre a Olokuti.
- Não há integração com sistemas da empresa nem validação institucional do produto.
- Os eventos de auditoria ficam na mesma base da aplicação; não são um registro inviolável nem guardam snapshots completos das alterações.
- Bootstrap e HTMX são carregados de CDNs. Ambientes restritos precisam disponibilizar esses arquivos localmente.
- Traduções de interface são parciais e não passaram por revisão humana completa.
- Os testes não validam uma conexão real de produção com PostgreSQL.
- `railway.json` está em formato legado e requer migração ou configuração atualizada do serviço para deployments novos/após o período de compatibilidade.

Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md) para as regras de contribuição e tratamento de dados de demonstração. Não publique credenciais ou detalhes exploráveis em issues públicas.

## 17 · Estrutura do repositório

```text
.
├── apps/
│   ├── accounts/       # autenticação, grupos e usuários
│   ├── audit/          # eventos de auditoria
│   ├── catalog/        # produtos, categorias e traduções
│   ├── operations/     # tarefas e status
│   └── reports/        # resumos e CSV
├── config/
│   └── settings/       # base, local, test e production
├── locale/             # catálogos gettext .po/.mo
├── static/             # CSS e JavaScript
├── templates/          # templates Django
├── tests/              # testes automatizados
├── requirements/       # dependências de produção e desenvolvimento
├── .github/workflows/  # CI e Health Check
├── .env.example
├── manage.py
├── Procfile
├── railway.json        # configuração Railway legada
├── render.yaml         # Render Blueprint (hospedagem gratuita)
├── vercel.json         # Vercel Serverless Python WSGI
└── pyproject.toml      # configuração do pytest e Ruff
```

## 18 · Contribuição e licença

Leia [`CONTRIBUTING.md`](CONTRIBUTING.md) antes de enviar alterações. Toda contribuição deve manter explícita a natureza experimental do MVP e evitar dados ou afirmações não verificadas.

O código original e a documentação deste repositório estão sob a [licença MIT](LICENSE). Ela não concede direitos sobre marcas, nomes, logotipos, dados ou materiais de terceiros. O nome “Olokuti” identifica o contexto acadêmico e não implica afiliação ou aprovação institucional.
