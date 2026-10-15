# JARVIS C003 — Âncora cloud segregada (pré-implantação)

**Data:** 2026-10-15  
**Estado:** LAB ONLY / CANDIDATE / HOLD / NOT QUALIFIED  
**Baseline:** JV8-BL-001 — V8.1 Rev03.1 ACTIVE, não alterada  
**Branch:** sandbox/jarvis-cloud-anchor-c003-20261015

## Escopo efetivamente implementado em laboratório
- Adaptador Python `CloudLedger` baseado em boto3 para DynamoDB `PutItem ConditionExpression=attribute_not_exists(pk)`; tenant/operação/request_id compõem fingerprint SHA-256.
- Reserva inicial `PENDING_WITNESS`, gravação de evidência versionada em S3 Object Lock `COMPLIANCE` com `IfNoneMatch=*` e confirmação por `VersionId`, retenção, conteúdo e SHA-256.
- Transição DynamoDB condicional para `WITNESSED` após confirmação WORM. Erro ou estado ambíguo retorna `HOLD`; conflito de digest retorna `CONFLICT`.
- Reutilização de autenticação Ed25519 da C002 com clientes sintéticos e política de autorização deny-by-default. Não há IAM real.
- Modelos CloudFormation separados: tabela de reserva em conta de confiança e bucket WORM em conta administrativa de auditoria. Modelos não implantados.
- Os modelos não criam funções Lambda, IAM Roles, API Gateways ou qualquer endpoint operacional.

## Evidência
- **35/35 testes locais aprovados**, por `python -m unittest discover -s tests -v`, usando clientes AWS simulados, autenticação real Ed25519 no processo de testes, cenários de concorrência/adulteração/perda de armazenamento, verificações estáticas de CloudFormation.
- Pacote entregue na conversa: `JARVIS_C003_CLOUD_ANCHOR_20261015.zip`.
- SHA-256 do ZIP: `50357c2d760dc449315c09154476e0ee3bcacafa3cda7aedf064589d91bc0f0b`.
- Inclui `evidence/test_results.txt` e `MANIFEST_SHA256.txt`, módulos Python, templates CF, README e matriz de riscos.
- **O código executável está no ZIP da conversa; este commit só registra o relatório, não equivale à implantação nem à incorporação dos módulos ao repositório.**

## Arquitetura alvo (não implantada)
1. Conta A — runtime de agentes, invocação autenticada apenas; **sem** acesso direto a tabela, testemunho ou políticas de retenção.
2. Conta B — âncora de autorização, IAM, Lambda e DynamoDB com reservas condicionais e controle de reconciliação.
3. Conta C — testemunho S3 Object Lock `COMPLIANCE` em conta/gestão independentes, acesso estritamente segregado e auditoria.
Mesmo três contas sob um único administrador superior não demonstram isolamento administrativo completo.

## Riscos ainda abertos
- **IA-02 OPEN — CRITICAL:** IAM e dispatcher autoritativo ainda não existem na implantação operacional; sem comprovação de políticas cross-account, autenticação por workload e gestão de chaves.
- **IDEMP-01 OPEN — CRITICAL:** reserva condicional não é prova de efeitos externos exatamente uma vez. DynamoDB+S3 não são uma transação distribuída; após falha parcial mantém-se HOLD e reconciliação por autoridade humana.
- O `IfNoneMatch=*` do S3 verifica somente a versão atual; versões protegidas podem coexistir com delete markers. Necessário negar deleção em policy e conferir explicitamente o `VersionId`.
- Uma retenção `COMPLIANCE` é irreversível durante o prazo. O exemplo de 7 dias se aplica apenas a laboratório e não determina prazo GxP.
- Testes de IAM revogado, tenant cruzado real, backup/restore, failover, RTO/RPO, object lock AWS real e multi-host permanecem pendentes.
- **Não houve deploy AWS, gasto contratado, uso de credenciais, backend em nuvem, integração MCP/A2A ou alteração de baseline.**

## Próxima etapa autorizável
Somente com contas AWS e gestores distintos definidos: revisar estimativa de custos e políticas de retenção; obter aceite para provisionamento; aplicar e testar IAM federado/SigV4, bucket WORM e tabela em ambiente segregado; produzir evidência E2E e revisão técnica independente. Não liberar produção GxP sem fechamento de riscos.

## Referências oficiais
- DynamoDB conditional writes: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html
- S3 Object Lock: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
- S3 conditional write/delete-marker: https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html
- AWS security reference architecture for log archive: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/log-archive.html
- GitHub OIDC with AWS: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
