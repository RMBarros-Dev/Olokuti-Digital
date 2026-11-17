# Tecnologias e linguagens — Olokuti Digital

Este documento explica o papel de cada tecnologia identificada na configuração e no código do repositório. A lista descreve o estado documentado do projeto, não uma promessa de que todos os componentes estejam ativos em produção.

## 1. Linguagens

| Tecnologia | Papel no projeto | Por que é utilizada |
| --- | --- | --- |
| **Python 3.12** | Backend, regras de domínio, comandos e testes | Linguagem principal integrada ao Django |
| **HTML** | Estrutura semântica das páginas | Base da renderização server-side com templates Django |
| **CSS** | Estilos da interface | Separa apresentação e estrutura |
| **JavaScript** | Interações pontuais no navegador | Complementa HTML e HTMX sem exigir uma SPA |
| **SQL** | Persistência relacional | Linguagem do PostgreSQL e base conceitual do ORM |
| **Markdown** | READMEs e documentação | Formato legível e nativo do GitHub |

## 2. Frameworks e bibliotecas

| Tecnologia | Camada | Responsabilidade |
| --- | --- | --- |
| **Django 5.2** | Backend | Rotas, views, formulários, autenticação, ORM, templates, sessões e administração |
| **Bootstrap 5.3.9** | Interface | Componentes e sistema de layout responsivo |
| **HTMX 2.0.11** | Interação web | Atualização parcial de conteúdo por requisições HTTP |
| **WhiteNoise** | Arquivos estáticos | Entrega de arquivos estáticos coletados pelo Django |
| **Gunicorn** | Servidor WSGI | Executa a aplicação Django em ambientes compatíveis |
| **psycopg 3** | Banco de dados | Driver PostgreSQL utilizado pela aplicação |
| **python-dotenv** | Configuração local | Carrega variáveis do arquivo `.env` em desenvolvimento |
| **pytest / pytest-django** | Testes | Execução e integração dos testes com Django |
| **Ruff** | Qualidade estática | Lint e verificação de convenções Python |

## 3. Infraestrutura e serviços

| Componente | Uso documentado | Observação |
| --- | --- | --- |
| **PostgreSQL / Supabase** | Banco relacional previsto para o ambiente hospedado | Configurado por `DATABASE_URL`; disponibilidade deve ser verificada no provedor |
| **Railway** | Hospedagem documentada para a aplicação | Validar configuração e comandos no serviço atual |
| **GitHub Actions** | CI, análise CodeQL e verificação de saúde | Workflow não equivale a monitoramento completo de produção |
| **Dependabot** | Alertas e propostas de atualização | Atualizações devem ser revisadas e testadas antes da integração |

## 4. Como as peças trabalham juntas

1. Django recebe a requisição e executa a lógica no backend.
2. O Django ORM converte operações dos modelos em consultas SQL.
3. O driver psycopg realiza a comunicação com PostgreSQL.
4. Templates Django produzem HTML.
5. Bootstrap fornece estilos e componentes visuais.
6. HTMX solicita atualizações parciais sem exigir uma aplicação JavaScript independente.
7. WhiteNoise disponibiliza os arquivos estáticos coletados.
8. Gunicorn executa a aplicação WSGI no ambiente de hospedagem.

## 5. Dependências e versões

As faixas de dependências devem ser conferidas nos arquivos:
- `requirements/production.txt`: dependências de runtime;
- `requirements/development.txt`: ferramentas de desenvolvimento e testes;
- `pyproject.toml`: configuração de pytest e Ruff.

O projeto usa faixas de versão, não necessariamente versões travadas por lockfile. Para builds reproduzíveis em maior escala, recomenda-se avaliar um processo de lock/constraints e atualização automatizada, sem introduzi-lo antes de definir a estratégia de dependências.

## 6. Tecnologias que não são requisitos atuais

Docker, Node.js, React, Redis, Celery, Kubernetes e arquitetura de microserviços não são requisitos do fluxo de desenvolvimento descrito no README atual. Podem ser avaliados futuramente, mas não devem ser apresentados como parte da stack implementada.

## 7. Referências oficiais

- [Python 3.12](https://docs.python.org/3.12/)
- [Django 5.2](https://docs.djangoproject.com/en/5.2/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [HTMX](https://htmx.org/docs/)
- [Bootstrap 5.3](https://getbootstrap.com/docs/5.3/)
- [pytest](https://docs.pytest.org/)
- [Ruff](https://docs.astral.sh/ruff/)
