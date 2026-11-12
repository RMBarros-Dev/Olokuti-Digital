# Olokuti Digital

MVP acadêmico e experimental para organizar registros de catálogo e tarefas operacionais. O software não representa sistemas internos confirmados da Olokuti, não se conecta aos sistemas da empresa e não contém dados reais. A hipótese de valor e cada necessidade operacional continuam **a validar mediante investigação de campo**.

## O que está incluído

- Autenticação Django, redefinição de senha e administração de utilizadores.
- Dashboard calculado a partir dos registos guardados neste MVP e limitado pelas permissões do utilizador.
- Catálogo com pesquisa, filtros, categorias, origem, informação de sustentabilidade e traduções opcionais separadas do texto original.
- Tarefas com responsável, prioridade, prazo, estado e eventos de auditoria.
- Relatórios por intervalo de criação e exportação CSV com proteção contra fórmulas de folha de cálculo.
- Registo de auditoria com utilizador, ação, tipo e identificador do registo, sem duplicar o conteúdo do catálogo ou das tarefas.
- Prefixos de URL para dez idiomas e estrutura Django gettext. Os catálogos ainda não foram traduzidos nem revistos.
- PostgreSQL como banco para execução local e produção. O perfil automatizado de testes usa SQLite em memória para não exigir um servidor PostgreSQL.

Não há pagamentos, vendas, faturação, gestão financeira, integração omnicanal ou sincronização de inventário. Não são carregados dados de demonstração.

## Arquitetura

Aplicação monolítica modular em Python 3.12 e Django 5.2, com Django ORM, Forms, Templates, autenticação nativa e HTMX. Bootstrap 5 fornece componentes visuais; JavaScript nativo cobre mensagens de erro das atualizações HTMX. Não há Docker, Node.js, Redis ou microserviços.

| Módulo | Responsabilidade |
| --- | --- |
| `apps/accounts` | Sessões, login, recuperação de senha, criação e gestão de utilizadores |
| `apps/catalog` | Categorias, produtos e traduções separadas |
| `apps/operations` | Tarefas e respetivo estado |
| `apps/reports` | Agregações e CSV |
| `apps/audit` | Eventos de auditoria |
| `config/settings` | Configuração comum, local, de testes e produção |

## Requisitos locais

- Python 3.12.
- PostgreSQL 14 ou superior.
- GNU gettext disponível no `PATH` para extrair e compilar traduções.
- Acesso à rede para carregar Bootstrap e HTMX dos CDNs configurados no layout.

Não é necessário Docker. Instale PostgreSQL nativamente e crie um utilizador e uma base de dados vazia, por exemplo:

```sql
CREATE USER olokuti WITH PASSWORD 'escolha-uma-palavra-passe-local';
CREATE DATABASE olokuti_digital OWNER olokuti;
```

No PowerShell, a partir da raiz do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -r requirements/development.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Edite `.env` antes de executar a aplicação: substitua `DJANGO_SECRET_KEY` por um segredo aleatório e `DATABASE_URL` pelas credenciais PostgreSQL locais. Codifique caracteres especiais da palavra-passe como URL-encoding. O ficheiro `.env` é ignorado pelo Git. A aplicação carrega as variáveis deste ficheiro com `python-dotenv`.

Abra `http://127.0.0.1:8000/`; a raiz redireciona para o prefixo do idioma escolhido. O login inicial é `/en/accounts/login/`. A redefinição de senha local escreve a mensagem no terminal; em produção configure um serviço SMTP autorizado.

## Utilizadores e permissões

O primeiro superutilizador pode entrar em Django Admin. Crie grupos em **Admin → Authentication and Authorization → Groups** e atribua as permissões necessárias. A página de utilizadores também permite criar contas e associá-las a grupos; a edição de contas existentes é feita no Admin.

- Catálogo: `view_product`, `add_product`, `change_product`, `delete_product`.
- Tarefas: `view_operationaltask`, `add_operationaltask`, `change_operationaltask`, `delete_operationaltask`.
- Auditoria: `view_auditlog`.
- Relatórios: exigem `catalog.view_product` e `operations.view_operationaltask`.
- Gestão de contas: utilizadores com `is_staff`.

O dashboard omite métricas para as quais o utilizador não tem permissão. As categorias são geridas no Django Admin e não podem ser apagadas enquanto existirem produtos associados.

## Testes e análise estática

```powershell
pytest
ruff check .
```

Os testes cobrem autenticação, permissões, operações básicas do catálogo e tarefas, preservação do texto original, auditoria, criação de utilizadores e segurança da exportação CSV. O ambiente de testes usa `config.settings.test` e SQLite em memória. Isto não valida a conexão PostgreSQL nem substitui uma verificação com a versão de produção.

## Internacionalização

Os idiomas configurados são `es-419`, `es-ES`, `ca`, `gl`, `eu`, `en-US`, `en-GB`, `en`, `pt-BR` e `pt-PT`. Cada locale tem um catálogo `.po` e um `.mo` compilado apenas com cabeçalho para que os prefixos de idioma sejam reconhecidos; o texto de interface continua em inglês até ser traduzido e revisto por pessoas qualificadas. Estes catálogos não são traduções completas.

Depois de instalar GNU gettext:

```powershell
django-admin makemessages -a
# Revise cada locale/.../django.po com tradutores qualificados.
django-admin compilemessages
```

As traduções não devem ser declaradas completas até à revisão humana. `ProductTranslation` guarda o idioma, nome, descrição e informação de sustentabilidade em registos separados; a alteração do idioma da interface não modifica o texto original.

## Produção e operações

Use `DJANGO_SETTINGS_MODULE=config.settings.production`, PostgreSQL, HTTPS e Gunicorn. Configure `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` e as credenciais SMTP por variáveis de ambiente. Se houver um proxy TLS, ative `DJANGO_TRUST_PROXY_SSL_HEADER=true` apenas quando o proxy confiável definir e filtrar `X-Forwarded-Proto`.

### Deploy no Railway

O repositório inclui `railway.json`: o Railpack instala `requirements.txt`, recolhe os ficheiros estáticos durante o build, executa migrações antes de ativar a versão e verifica `/health`. O processo web usa Gunicorn ligado à porta `$PORT`. Conecte o serviço ao repositório GitHub e configure no Railway, como variáveis protegidas:

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY`: segredo aleatório forte, exclusivo da produção.
- `DATABASE_URL`: URL PostgreSQL de produção (não use SQLite nem a URL de exemplo).
- `DJANGO_ALLOWED_HOSTS`: domínio público atribuído pelo Railway, sem `https://`.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: origem HTTPS completa do domínio público atribuído pelo Railway.
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS=true` e `DEFAULT_FROM_EMAIL`: credenciais SMTP autorizadas; o settings de produção recusa iniciar sem SMTP configurado.

Depois de gerar o domínio público, atualize `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS` com esse domínio e faça novo deploy. O healthcheck do Railway usa `healthcheck.railway.app`, já permitido explicitamente. A aplicação não provisiona uma base de dados Railway nem migra dados automaticamente entre provedores; a URL deve apontar para uma base PostgreSQL já criada e autorizada.

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.production"
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

O WhiteNoise serve os ficheiros estáticos recolhidos. Os logs são emitidos como JSON para stdout/stderr; não inclua informação pessoal ou conteúdo de tarefas em mensagens de log. Os cookies de sessão e CSRF são seguros em produção, `DEBUG` fica desativado, HTTPS é obrigatório e HSTS está ativado.

### Cópia de segurança PostgreSQL

Faça `pg_dump` periódico num destino protegido e encriptado, com credenciais de backup de menor privilégio; retenha cópias conforme a política da organização e teste uma restauração antes de qualquer validação operacional. Exemplo de cópia manual:

```powershell
pg_dump --format=custom --file=olokuti-backup.dump --dbname="postgresql://olokuti:...@localhost:5432/olokuti_digital"
pg_restore --clean --if-exists --dbname="postgresql://olokuti:...@localhost:5432/olokuti_restore_test" olokuti-backup.dump
```

Não guarde credenciais no comando, no histórico do terminal ou no backup. Utilize mecanismos de credenciais PostgreSQL apropriados no ambiente real.

## Limitações conhecidas

- A pasta original estava vazia; este projeto foi criado como uma nova base após a auditoria inicial.
- A suite automatizada foi executada localmente com SQLite em memória; uma ligação real ao PostgreSQL de produção ainda precisa de validação.
- Catálogos gettext ainda sem traduções e sem `.mo`; a interface usa strings-fonte em inglês.
- Os registos de auditoria são gravados na mesma base e não são invioláveis nem incluem snapshots completos de cada alteração.
- A interface carrega Bootstrap e HTMX por CDN; uma implantação em rede restrita deve alojar esses ativos localmente.
- A configuração técnica não valida a identidade visual oficial, processos, dados, permissões ou valor institucional com a Olokuti. Não foi feita revisão independente de segurança.
- A validação técnica não equivale à validação institucional ou operacional pela Olokuti.
