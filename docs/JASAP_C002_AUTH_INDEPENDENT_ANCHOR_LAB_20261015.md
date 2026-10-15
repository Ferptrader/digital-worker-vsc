# JARVIS C002 | Autenticação e âncora de confiança — resultado de laboratório
Data: 2026-10-15
Status: **LAB ONLY / CANDIDATE / HOLD / NOT QUALIFIED**
Baseline: **JV8-BL-001 — V8.1 Rev03.1 ACTIVE, sem alteração**

## Implementação executada (código entregue em pacote ZIP da conversa)
Implementado em ambiente local isolado um protótipo Python com:
- Ed25519 por identidade de cliente; assinatura do envelope de requisição, vinculação a tenant, ação e operação.
- Contrato com operação permitida somente `extract_document`; sem lançamento de efeitos em sistemas GxP.
- Autorização deny-by-default e escopos mantidos pelo processo servidor (não pelo agente).
- Âncora de reserva atômica SQLite com chave `(tenant,operation,request_id)`, digest de conteúdo e decisões `RESERVED / DUPLICATE / CONFLICT`.
- Hash encadeado de evidência, assinatura da âncora e **selo assinado em diretório separado**. Divergência dos dois implica recusa de novas operações.
- Recibos assinados verificáveis pelo cliente e consulta `status` autenticada para reconciliação.
- IPC local por UNIX socket, sem endpoint HTTP e sem MCP/A2A real.
- Processo de âncora em UID 65534 `nobody`, cliente em UID 1 `daemon`, com FS isolado por permissões Linux. Chaves Ed25519 efêmeras apenas para testes.
- Reinício do servidor entre a reserva e a tentativa de duplicação; a reserva original foi preservada.

## Evidência de teste executado
- Python 3.13.5 (laboratório); pacote `cryptography` instalado no ambiente isolado.
- **34/34 testes de unidade/segurança** (controles, falsificação de assinatura, replay, adulteração, apagamento, truncamento, segregação tenant, falha segura, concorrência e reconciliação).
- Repetição completa da suíte **5 vezes: 34/34 PASS** depois de corrigir condição de corrida entre selo assinado e COMMIT da transação.
- Teste OS real: **LAB_PASS**. Primeiro pedido `RESERVED`, tentativa de excluir DB `PERMISSION_DENIED`, reinício do processo de âncora e pedido duplicado `DUPLICATE`, consulta posterior `FOUND`, autorização GxP `NOT_GRANTED`.
- Artefatos locais gerados com `evidence/unit_test_results.txt`, `evidence/os_segregation_result.json`, `evidence/execution_metadata.json`, `docs/SECURITY_GATES.md`, `MANIFEST_SHA256.txt`; pacote `JARVIS_TRUST_ANCHOR_C002_20261015.zip`.
- Este registro no GitHub contém o **parecer e trilha de resultados**. O código da PoC está no ZIP disponibilizado na conversa; **não está incorporado ao runtime nem ao repositório neste commit**.

## Análise de riscos e limitações
**IA-02 / IDEMP-01: OPEN — CRITICAL (uso produtivo)**

A implementação cria segregação entre usuários de processos no mesmo host, porém o banco e o selo são administrados pela mesma identidade de âncora. Um administrador root com acesso à chave, ao banco e ao selo pode substituir todas as evidências. Não existe autoridade IAM independente, witness WORM, armazenagem multiadmin, conta/serviço externo, assinatura por HSM/KMS nem comprovação de backup/failover. A operação apenas RESERVA identificadores: não pode garantir idempotência de efeitos externos nem fechamento regulatório. Uma falha entre selo e COMMIT causa HOLD até reconciliação manual; não há garantia de disponibilidade.

**Os testes validam comportamentos sintéticos e isolamento de processos, não segurança de produção nem GxP qualification.**

## Pré-requisitos para gate de produção
1. IAM e serviço de âncora em ambiente e conta administrativa independentes do executor JARVIS; escopos reais, auditoria, revogação e rotação de chave.
2. Reserva durável com fencing e reconciliação de efeito externo, replicação/backup, testes de concorrência/failover/replay em múltiplos nós.
3. Witness externo imutável por período definido e protegido de alteração por administradores do runtime e do serviço aplicacional.
4. Integração end-to-end com dispatcher JARVIS autoritativo identificado e autenticação real; testes e revisão humana/Qualidade.
5. Somente após os critérios anteriores, iniciar MCP/A2A reais e avaliar compatibilidade com SAP.

## Próxima decisão
**Manter HOLD.** Próxima etapa viável: laboratório cloud segregado com IAM gerenciado, banco de reservas transacional e testemunho independente em storage imutável, após avaliação técnica e de custos. Não foi autorizado nem realizado deploy de recursos externos nesta etapa.

Referências:
- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- https://a2a-protocol.org/v0.3.0/specification/
- Documento anterior: `docs/JASAP_C001_GOVERNANCA_E_GATES_20261015.md`.
