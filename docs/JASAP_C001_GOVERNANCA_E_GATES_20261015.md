# JASAP-C001 | Governança SAP AI Agents como referência para JARVIS
Data: 2026-10-15  
Classificação: **LAB ONLY / CANDIDATE / HOLD / NOT QUALIFIED**  
Baseline declarada: **JV8-BL-001 — V8.1 Rev03.1 ACTIVE (sem alteração)**

## Decisão arquitetural
Aproveitar o modelo de governança do SAP AI Agent Hub, e os padrões abertos MCP/A2A/RAG como referências, **sem adquirir SAP BTP ou integrar serviços SAP nesta fase**. Prioridade é eliminar os riscos críticos preexistentes de autorização e idempotência.

## Avaliação comparativa
| Conceito | Aplicação útil | Estado recomendado |
|---|---|---|
| SAP AI Agent Hub/LeanIX | Inventário de agentes, responsáveis, finalidade, risco, ciclo de vida e verificação | DOCUMENTAR |
| MCP | Catálogo de ferramentas, autenticação por recurso, autorização e controle de acesso | ESPECIFICAR e testar no futuro |
| A2A | Identificador de tarefas, identidade do agente, estados e mensagens entre agentes | ESPECIFICAR e testar no futuro |
| RAG | Recuperar documentos controlados com fonte, versão, ACL e citações verificáveis | PROJETAR antes de executar |
| Joule Studio | Referência de composição e governança de agentes SAP | ESTUDAR |
| SAP AI Core / Generative AI Hub | Separação entre runtime, modelo e controles | SEM MIGRAÇÃO |
| SAP BTP/Cloud SDK for AI | Integração quando houver sistema SAP e ambiente de cliente autorizado | NÃO IMPLEMENTAR |

**Nota de disponibilidade:** funções do AI Agent Hub podem estar sujeitas a Early Adopter Care; verificar acesso antes de planejar adoção.

## Estado do projeto inspecionado via GitHub
- O `main.py` do branch `main` define um agente de navegação com `tools=[]`: a execução real de testes externos não está comprovada nessa implementação.
- O branch `sandbox/jarvis-supervised-boundary-v03-20261011` contém candidatos de gateway autenticado, dispatcher, replay SQLite e contrato de âncora independente.
- A evidência `docs/IDEMP_01_CONFIRMED_ADVERSARIAL_FAIL_20261011.md` registra uma fraqueza: exclusão/recriação da base SQLite permite reutilização de nonce.
- A especificação `docs/INDEPENDENT_TRUST_ANCHOR_ACCEPTANCE_C001.md` indica explicitamente **design only / not implemented**.
- Os registros indicam **IA-02 / IDEMP-01 OPEN — CRITICAL**. Não há comprovação de runtime autoritativo integrado.

## Gates para qualquer promoção
1. **Identidade e autorização independentes:** autenticação positiva, escopo por capacidade, menor privilégio, deny-by-default; dados fornecidos pelo agente não são autoridade.
2. **Idempotência verificável:** reserva atômica durável segregada, witness imutável, fencing, reconciliação de efeitos ambíguos, replay após falhas e concorrência testados.
3. **Protocolos reais:** MCP/A2A com versões declaradas, autenticação/transporte seguro e E2E, não apenas formatos JSON similares.
4. **RAG com proveniência:** corpus versionado, ACL, revogação, referências reproduzíveis, testes de prompt injection, documentos conflitantes e obsoletos.
5. **Assurance GxP proporcional ao risco:** requisitos, rastreabilidade, ensaios negativos, registros íntegros e aprovação humana/Qualidade.

**Critério de não promoção:** se IA-02 ou IDEMP-01 permanecerem abertos, se houver testemunho co-local ou se a autorização depender exclusivamente do conteúdo declarado pelo agente, o gate de produção permanece **HOLD**.

## Testes realizados nesta avaliação
Protótipo Python **offline** com dados sintéticos, demonstrando política de leitura somente: **22 testes executados, 22 resultados esperados**, com `unittest` em Python 3.13.5. **Um dos 22 testes comprova intencionalmente a vulnerabilidade de replay após reinicialização do armazenamento volátil.** A contagem não comprova segurança GxP.

Nenhum endpoint, servidor MCP ou A2A real, SDK SAP, identidade IAM real, RAG real, conexão JARVIS operacional, âncora imutável ou sistema GxP foi executado no laboratório. Código, inventário, logs e manifesto local foram preservados no pacote entregue na conversa, sem alterar branches existentes.

## Fontes oficiais
- SAP AI Agent Hub: https://help.sap.com/docs/leanix/ea/ai-agent-hub?version=CLOUD
- SAP Agent Modeling: https://help.sap.com/docs/leanix/ea/ai-agent-modeling-guidelines
- MCP 2025-11-25 Authorization: https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- A2A specification v0.3.0: https://a2a-protocol.org/v0.3.0/specification/

**Escopo de escrita:** apenas documentação em branch `sandbox/jarvis-sap-ai-governance-c001-20261015`, sem merge/deploy/alteração de baseline.
