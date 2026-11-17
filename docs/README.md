# Olokuti Digital — documentação técnica

Índice de documentação mantida no repositório.

| Documento | Conteúdo |
| --- | --- |
| [README principal](../README.md) | Contexto, escopo, arquitetura, setup, configuração, testes e deploy |
| [README em inglês](../README.en.md) | Documentação equivalente em inglês |
| [Estrutura do projeto](project-structure.md) | Árvore de diretórios, responsabilidades e convenções |
| [Tecnologias e linguagens](technology-stack.md) | Papel de Python, Django, HTML, CSS, JavaScript, SQL e ferramentas |
| [Arquitetura técnica](architecture/README.md) | Componentes, fluxo de requisições, persistência e limites dos módulos |
| [Identidade visual](brand/README.md) | Conceito, paleta e ativos SVG |
| [Política de segurança](../SECURITY.md) | Escopo e canal privado de relatos |
| [Contribuição](../CONTRIBUTING.md) | Setup, qualidade e regras para contribuições |
| [Changelog](../CHANGELOG.md) | Histórico de alterações relevantes |
| [Metodologia de desenvolvimento](development-methodology.md) | Ciclo de trabalho, critérios de aceite e Definition of Done |
| [Qualidade e testes](quality/README.md) | Ruff, pytest, CI, CodeQL, Dependabot e política de badges |
| [Roadmap de evolução](roadmap.md) | Estado documentado, fases recomendadas e critérios de priorização |
| [Repositórios de referência](reference-projects.md) | Projetos Django e padrões de documentação consultados |

## Organização de novos documentos

- Decisões arquiteturais permanentes: `docs/adr/NNNN-titulo.md`.
- Guias de execução e operação: `docs/guides/`.
- Diagramas e visão técnica: `docs/architecture/`.
- Materiais da identidade visual: `docs/brand/` e os arquivos-fonte em `assets/brand/`.

Criar esses diretórios somente quando houver conteúdo real para versionar. Evitar pastas vazias e duplicação de instruções entre os READMEs.
