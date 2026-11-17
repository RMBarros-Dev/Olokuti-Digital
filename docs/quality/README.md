# Qualidade, testes e indicadores do repositório

## 1. Verificações existentes

O repositório configura:
- **Ruff:** análise estática e convenções Python;
- **Django system checks:** validações do projeto com `manage.py check` no perfil de teste;
- **Migration drift check:** falha se houver mudanças de modelos sem migrações versionadas;
- **pytest + pytest-django:** execução dos testes automatizados;
- **GitHub Actions CI:** execução dessas verificações em Python 3.12;
- **CodeQL:** análise estática de segurança para Python;
- **Dependabot:** verificação de atualizações de dependências Python e GitHub Actions.

A existência desses arquivos comprova configuração versionada, não que a última execução tenha sido bem-sucedida. Consulte a aba Actions para verificar o estado atual.

## 2. Comandos locais

Na raiz do repositório, com o ambiente virtual ativo:

```powershell
python -m pip install -r requirements/development.txt
python -m ruff check .
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
python -m pytest -q
```

## 3. Escopo de testes documentado

A suíte descrita no README cobre autenticação, permissões, catálogo, traduções de produtos, tarefas, relatórios, auditoria, contas e proteção da exportação CSV.

Os testes usam SQLite em memória. Isso não substitui testes de integração com PostgreSQL, testes de deploy, restauração de backup ou validação de disponibilidade do provedor.

## 4. Badges: política de uso

O README principal já utiliza badges para:
- workflow de CI;
- workflow de health check;
- versões de Python e Django documentadas;
- PostgreSQL/Supabase como tecnologia de banco;
- licença do repositório.

Regras:
- não adicionar badge de cobertura sem relatório real e workflow que o publique;
- não declarar status `passing` manualmente;
- não usar badge de “production ready”, “100% secure” ou “24/7 uptime” sem critérios e monitoramento que sustentem a afirmação;
- manter badges ligados ao workflow correto;
- remover ou corrigir badge se o workflow for renomeado ou descontinuado.

## 5. Indicadores recomendados — ainda não medidos

Podem ser adotados após definir coleta e metas:
- taxa de sucesso da CI;
- duração mediana da suíte de testes;
- vulnerabilidades abertas por severidade;
- idade de dependências desatualizadas;
- falhas por release;
- tempo de recuperação após incidente;
- cobertura de fluxos críticos por testes.

Não publicar valores até que exista fonte automatizada, janela temporal e método de cálculo documentados.

## 6. Próximas melhorias de qualidade

- [ ] Avaliar cobertura de testes sem transformar percentual isolado em meta de qualidade.
- [ ] Incluir testes de integração PostgreSQL em workflow separado, se necessário.
- [ ] Adotar `ruff format --check .` no CI se a equipe decidir exigir formatação automatizada.
- [ ] Definir política de revisão de dependências e atualizações.
- [ ] Configurar proteção de `main` ou ruleset exigindo PR e verificações obrigatórias antes do merge; essa configuração precisa ser feita nas configurações do GitHub.
- [ ] Registrar evidência de cada melhoria concluída.
