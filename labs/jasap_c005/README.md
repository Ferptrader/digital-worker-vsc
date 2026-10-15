# JARVIS C005 — Gate operacional de confiança

Status: **LAB ONLY / HOLD / NOT QUALIFIED**. Sem integração ao runtime autoritativo do JARVIS, sem provisionamento AWS e sem liberação GxP.

O código da C004 agora está versionado no GitHub (antes havia apenas um relatório). Os 69 testes sintéticos e de regressão incluem cinco casos do novo preflight AWS. Para executar:

```bash
python -m pip install -r requirements-lab.txt
PYTHONPATH=. python -m unittest discover -s tests -v
```

## Auditoria read-only de ambiente AWS

Exige credenciais AWS já concedidas a um perfil com permissões de leitura. Nunca provisiona ou escreve recursos.

```bash
python aws_preflight.py --table TABELA --bucket BUCKET --region us-east-1 \
  --anchor-account 111111111111 --witness-account 222222222222
```

Verifica que IDs declarados são distintos, a identidade AWS chamadora e o estado de DynamoDB, PITR, proteção contra exclusão, versionamento S3, Object Lock e public access block. **Mesmo que todos os checks passem, retorna `INFRASTRUCTURE_PRESENT_NOT_QUALIFIED`; não prova segregação administrativa ou IAM efetivo.**

Os seguintes testes independentes continuam necessários para resolver IA-02/IDEMP-01: IAM positivo e negativo entre contas (permissões efetivas, políticas de bucket/roles, revogação e rotação); teste WORM com versão de objeto sob retenção; corrida multi-host e falha de rede após efeito externo; reconciliação com evidência autoritativa e fencing; isolamento administrador; revisão QA/Segurança e aprovação humana.

A execução em GitHub Actions confirma regressão em outro ambiente, mas não substitui a qualificação de produção.


## Revisão de segurança — 15/10/2026 (C005-R1)

- Todas as chamadas ao testemunho S3 exigem `ExpectedBucketOwner` de 12 dígitos; o adaptador falha na configuração sem proprietário declarado.
- `status()` não informa falsamente `NOT_FOUND` após perda da reserva DynamoDB se existir uma versão anterior ou delete marker do mesmo identificador. Consulta `ListObjectVersions` com owner esperado; erro/truncamento resulta em HOLD.
- O preflight AWS consulta o modo padrão `COMPLIANCE`, a permissão de listar versões e uma política Deny incondicional para exclusões. Ainda assim, não demonstra segregação administrativa real, controle de IAM ou imutabilidade fim a fim.
- **69 testes PASS** em ambiente local nesta revisão; execução remota deve ser verificada separadamente pelo GitHub Actions.
- Nenhuma ação de execução de negócio ou liberação GxP está autorizada. IA-02/IDEMP-01 continuam OPEN para ambiente real.
