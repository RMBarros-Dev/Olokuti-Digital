# Metodologia de desenvolvimento — Olokuti Digital

## 1. Abordagem atual

O repositório descreve o Olokuti Digital como um MVP acadêmico e experimental. O desenvolvimento é incremental, organizado por módulos Django, com requisitos e hipóteses documentados, testes automatizados e verificações de qualidade em integração contínua.

Não há evidência no repositório de adoção formal de Scrum, Kanban ou outro framework ágil completo. Portanto, este documento não declara que a equipe execute cerimônias, papéis ou métricas desses métodos.

## 2. Princípios de trabalho

1. **Evidência antes de requisito:** separar observações, hipóteses e decisões.
2. **Escopo pequeno:** implementar uma mudança coerente por vez.
3. **Modularidade:** manter responsabilidades nos apps de domínio existentes.
4. **Segurança por padrão:** aplicar autenticação, autorização e menor privilégio.
5. **Testabilidade:** cobrir regras e regressões relevantes.
6. **Rastreabilidade:** relacionar mudanças a Issues, commits e documentação quando aplicável.
7. **Reversibilidade:** planejar migrações e rollback para alterações de risco.
8. **Transparência:** não afirmar validação de campo, disponibilidade ou cobertura que não tenha sido verificada.

## 3. Ciclo recomendado para cada alteração

| Etapa | Atividade | Evidência de conclusão |
| --- | --- | --- |
| 1. Entendimento | Descrever problema, usuário afetado e resultado esperado | Issue ou especificação curta |
| 2. Análise | Identificar módulos, dados, permissões, riscos e compatibilidade | Plano técnico e critérios de aceite |
| 3. Implementação | Fazer alteração pequena, isolada e coerente | Diff revisável |
| 4. Verificação | Executar lint e testes; adicionar testes para o comportamento alterado | Saída dos comandos e CI verde |
| 5. Documentação | Atualizar README, guia, ADR ou changelog se a mudança alterar comportamento ou operação | Documentação consistente |
| 6. Revisão | Conferir segurança, regressões, escopo e clareza | Pull request revisado |
| 7. Integração | Integrar somente após verificações e aprovação aplicáveis | Commit integrado |
| 8. Acompanhamento | Verificar healthcheck e comportamento do ambiente após deploy | Evidência observável, sem inferir disponibilidade contínua |

## 4. Critérios de aceite

Uma alteração é candidata à integração quando:
- atende aos critérios de aceite definidos;
- não introduz segredos ou dados reais em arquivos versionados;
- preserva permissões e isolamento entre usuários;
- inclui testes para regras novas ou modificadas;
- não quebra migrações, traduções ou comandos de execução;
- passa por Ruff e pytest;
- atualiza a documentação quando necessário;
- não amplia o escopo sem justificativa.

## 5. Branches e commits — recomendação

O workflow atual executa CI em pushes para `main` e em pull requests. Para reduzir risco, recomenda-se trabalhar em branches curtas e abrir PR para `main`, evitando commits diretos na branch principal quando a mudança for relevante.

Padrão sugerido para nomes:
- `docs/<assunto>` — documentação;
- `feat/<assunto>` — funcionalidade;
- `fix/<assunto>` — correção;
- `refactor/<assunto>` — refatoração;
- `test/<assunto>` — testes;
- `chore/<assunto>` — manutenção.

Padrão sugerido para mensagens de commit: Conventional Commits (`docs:`, `feat:`, `fix:`, `test:`, `refactor:`, `chore:`). É uma convenção recomendada, não uma regra atualmente imposta por automação.

## 6. Definition of Done

Uma tarefa só deve ser marcada como concluída quando:
- a implementação corresponde ao escopo aprovado;
- os testes relevantes foram executados;
- a CI foi verificada;
- documentação e changelog foram atualizados quando aplicável;
- não há credenciais ou dados sensíveis no diff;
- limitações e riscos remanescentes foram registrados.

## 7. Gestão de hipóteses e pesquisa de campo

O contexto comercial associado ao estudo não deve ser tratado como evidência de processos reais da empresa. Requisitos de negócio devem ser classificados como:
- **Fato observado:** sustentado por fonte ou observação registrada;
- **Hipótese:** explicação ainda não validada;
- **Requisito validado:** confirmado com usuários ou responsáveis autorizados;
- **Decisão técnica:** escolha de implementação com justificativa;
- **Pendência:** informação ou validação ausente.

Dados sintéticos devem permanecer identificados como demonstração. Não usar nomes de fornecedores, certificações, origens ou alegações de sustentabilidade como fatos sem fonte verificável.

## 8. Referências metodológicas

- [Django — Tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)
- [GitHub — Pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Diátaxis — documentação técnica](https://diataxis.fr/)

As referências são materiais de apoio. Sua presença não significa que todos os processos descritos estejam automatizados no repositório.
