# Roadmap de evolução — Olokuti Digital

Este roadmap separa o que está documentado como existente do que depende de validação ou implementação. Não representa cronograma, compromisso de entrega ou confirmação de demanda de usuários.

## Estado documentado

| Área | Situação identificada no repositório |
| --- | --- |
| Autenticação e contas | Fluxos Django de login, cadastro e redefinição de senha documentados |
| Catálogo | Produtos, categorias, filtros, traduções localizadas e exportação CSV documentados |
| Operações | Tarefas, responsáveis, prioridade, prazo, status e atualização HTMX documentados |
| Relatórios | Resumo por período/status e exportação CSV documentados |
| Auditoria | Registro de eventos de operações relevantes documentado |
| Internacionalização | Dez variantes configuradas; catálogos parciais |
| Qualidade | Ruff, pytest, GitHub Actions e CodeQL presentes no repositório |
| Deploy | Arquivos de configuração para provedores presentes; operação real precisa de verificação por ambiente |

## Fase 1 — Consolidar a base técnica

**Objetivo:** tornar o estado atual mais previsível e verificável.

- [ ] Executar CI e registrar o resultado real.
- [ ] Verificar migrações em banco PostgreSQL de teste.
- [ ] Revisar variáveis de ambiente e ausência de segredos no histórico.
- [ ] Validar permissões por perfil e tentativas de acesso não autorizado.
- [ ] Verificar configuração atual do provedor de hospedagem.
- [ ] Documentar backup, retenção e teste de restauração com o provedor.
- [ ] Revisar dependências e tratar alertas do Dependabot.

**Critério de saída:** evidências reproduzíveis de qualidade, segurança básica e execução nos ambientes suportados.

## Fase 2 — Validar o problema e os fluxos

**Objetivo:** confirmar se catálogo e tarefas resolvem necessidades reais do público pretendido.

- [ ] Definir perfil dos participantes e protocolo de pesquisa.
- [ ] Realizar entrevistas ou observações com autorização.
- [ ] Mapear fluxo atual e pontos de fricção com evidências.
- [ ] Priorizar problemas por impacto e frequência observados.
- [ ] Revisar linguagem, campos e permissões com usuários representativos.
- [ ] Registrar requisitos confirmados e hipóteses rejeitadas.

**Critério de saída:** requisitos rastreáveis a evidências de pesquisa, sem atribuir conclusões à empresa sem autorização.

## Fase 3 — Melhorar a experiência e a acessibilidade

Candidatas à avaliação, não funcionalidades prometidas:
- [ ] Revisar responsividade em dispositivos e resoluções reais.
- [ ] Verificar navegação por teclado, foco, contraste e rótulos.
- [ ] Revisar mensagens de erro, estados vazios e confirmações.
- [ ] Completar catálogos de tradução com revisão humana.
- [ ] Validar formatos regionais de data, hora, número e moeda.
- [ ] Avaliar consistência visual dos componentes.

**Critério de saída:** critérios de usabilidade e acessibilidade definidos e verificados.

## Fase 4 — Robustez operacional

Candidatas à avaliação após validação de uso:
- [ ] Formalizar política de backup e restauração.
- [ ] Definir retenção e minimização de logs.
- [ ] Adicionar monitoramento de erros e alertas com proteção de dados.
- [ ] Avaliar paginação e desempenho das consultas com dados representativos.
- [ ] Definir estratégia de migrações e rollback.
- [ ] Automatizar verificações de segurança e dependências conforme risco.

**Critério de saída:** operação com procedimentos testados e responsáveis definidos.

## Fase 5 — Evolução funcional orientada por evidências

Novos recursos só devem ser priorizados após validação. Possibilidades a investigar:
- importação controlada de catálogo;
- histórico e rastreabilidade ampliados;
- fluxos de aprovação;
- integrações externas autorizadas;
- API versionada, caso exista consumidor real;
- notificações, se houver necessidade operacional confirmada.

Não adicionar microserviços, filas, cache ou infraestrutura distribuída sem requisitos de escala, volume ou integração que justifiquem seu custo.

## Priorização

Avaliar cada proposta com os seguintes critérios:
1. impacto comprovado no problema;
2. frequência e gravidade da necessidade;
3. risco de segurança e privacidade;
4. esforço de implementação e manutenção;
5. dependências técnicas;
6. possibilidade de medir o resultado.

## Política de atualização

Atualizar este documento quando houver decisão aprovada, entrega verificável ou evidência nova. Itens concluídos devem apontar para PR, commit, teste ou documento que comprove a conclusão.
