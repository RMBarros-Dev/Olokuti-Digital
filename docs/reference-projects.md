# Repositórios de referência e critérios de comparação

Esta seleção foi consultada para orientar a apresentação, a documentação e as práticas de engenharia do Olokuti Digital. Ela não representa uma classificação absoluta dos “melhores” projetos: cada referência foi escolhida por sua relevância para um aspecto específico.

## 1. Referências Django

| Repositório | Por que foi consultado | Prática aproveitável |
| --- | --- | --- |
| [django/django](https://github.com/django/django) | Projeto oficial do framework | Navegação clara para documentação, contribuição, segurança e testes |
| [cookiecutter/cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django) | Template de projeto Django com práticas de produção | Organização de configuração, testes, deploy, dependências e ferramentas de qualidade |
| [wagtail/wagtail](https://github.com/wagtail/wagtail) | Aplicação de grande porte construída sobre Django | Documentação organizada por públicos, guias, compatibilidade e notas de versão |

## 2. Referências de README e documentação

| Recurso | Utilidade | Critério aplicado |
| --- | --- | --- |
| [matiassingers/awesome-readme](https://github.com/matiassingers/awesome-readme) | Coleção curada de READMEs | Clareza visual, exemplos, navegação, quickstart e contribuição |
| [mhucka/readmine](https://github.com/mhucka/readmine) | Estrutura de referência para README | Resumo do projeto, instruções de uso, badges úteis e documentação complementar |
| [Diátaxis](https://diataxis.fr/) | Método para organizar documentação | Separar tutoriais, guias de execução, referência e explicações conceituais |

## 3. Padrões adotados nesta revisão

A partir da comparação, a revisão prioriza:
- resumo claro do que o projeto é e do que não é;
- badges vinculados a workflows ou metadados verificáveis;
- README como ponto de entrada, com índice para documentação especializada;
- explicação da arquitetura e da responsabilidade de cada tecnologia;
- instruções reproduzíveis de instalação, teste e operação;
- documentação de segurança, contribuição, metodologia e evolução;
- distinção entre estado implementado, hipótese e recomendação futura.

## 4. O que não foi copiado

O Olokuti Digital é um MVP acadêmico e experimental, não um framework, CMS ou template de produção. Portanto, não foram importados:
- estruturas de microserviços ou componentes que não existem no projeto;
- badges de cobertura, release, downloads ou maturidade sem evidência;
- declarações de suporte a versões que o projeto não testou;
- promessas de disponibilidade ou prontidão para produção;
- dependências e ferramentas apenas porque aparecem em projetos maiores.

## 5. Como usar as referências

Revisitar essas fontes quando houver mudança relevante na stack, na organização documental ou na governança. Antes de adotar uma prática, avaliar compatibilidade com o tamanho do MVP, custo de manutenção, segurança e benefício mensurável.
