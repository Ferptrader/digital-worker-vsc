# PROTOCOLO DE QUALIFICAÇÃO DE INSTALAÇÃO (IQ)

## Informações do Documento

**Documento:** PRT-IQ-{{DATA_DOCUMENTO}}
**Sistema:** {{NOME_SISTEMA}}
**Versão:** {{VERSAO_SISTEMA}}
**Fabricante:** {{FABRICANTE}}
**Data de Elaboração:** {{DATA_ELABORACAO}}
**Responsável Técnico:** {{RESPONSAVEL_TECNICO}}
**Categoria GAMP:** {{CATEGORIA_GAMP}}
**Criticidade:** {{CRITICIDADE}}

---

## 1. OBJETIVO

Este protocolo tem como objetivo verificar e documentar que o sistema **{{NOME_SISTEMA}}** foi instalado conforme especificações do fabricante e requisitos da empresa, atendendo às Boas Práticas de Fabricação (BPF) e regulamentações vigentes da ANVISA (RDC 430/2020).

## 2. ESCOPO

Este protocolo abrange:

- ✅ Verificação de hardware instalado
- ✅ Validação de software e licenças
- ✅ Checklist de configurações iniciais
- ✅ Verificação de backup e disaster recovery
- ✅ Documentação de instalação
- ✅ Configuração de segurança e controles de acesso

## 3. RESPONSABILIDADES

| Papel | Nome | Assinatura | Data |
|-------|------|------------|------|
| Responsável Técnico | {{RESPONSAVEL_TECNICO}} | __________ | ___/___/___ |
| Revisor de Qualidade | {{REVISOR_QUALIDADE}} | __________ | ___/___/___ |
| Aprovador Final | {{APROVADOR}} | __________ | ___/___/___ |

## 4. REQUISITOS DE HARDWARE

| Item | Especificação Requerida | Especificação Instalada | Status | Evidência |
|------|------------------------|------------------------|--------|----------|
| IQ-HW-001 | Servidor: {{ESPECIFICACAO_SERVIDOR}} | {{INSTALADO_SERVIDOR}} | [ ] ✅ [ ] ❌ | Screenshot |
| IQ-HW-002 | Memória RAM: {{RAM_REQUERIDA}} | {{RAM_INSTALADA}} | [ ] ✅ [ ] ❌ | Relatório sistema |
| IQ-HW-003 | Espaço em Disco: {{DISCO_REQUERIDO}} | {{DISCO_DISPONIVEL}} | [ ] ✅ [ ] ❌ | Screenshot |
| IQ-HW-004 | Processador: {{CPU_REQUERIDA}} | {{CPU_INSTALADA}} | [ ] ✅ [ ] ❌ | Relatório sistema |
| IQ-HW-005 | Sistema Operacional: {{SO_REQUERIDO}} | {{SO_INSTALADO}} | [ ] ✅ [ ] ❌ | Screenshot versão |

## 5. REQUISITOS DE SOFTWARE

| Item | Descrição | Versão Esperada | Versão Instalada | Status | Evidência |
|------|-----------|----------------|-----------------|--------|----------|
| IQ-SW-001 | {{NOME_SISTEMA}} | {{VERSAO_SISTEMA}} | __________ | [ ] ✅ [ ] ❌ | Tela "Sobre" |
| IQ-SW-002 | Banco de Dados | {{BD_VERSAO}} | __________ | [ ] ✅ [ ] ❌ | Query versão |
| IQ-SW-003 | Servidor Web/App | {{SERVIDOR_VERSAO}} | __________ | [ ] ✅ [ ] ❌ | Logs servidor |
| IQ-SW-004 | Dependências/Libraries | {{DEPENDENCIAS}} | __________ | [ ] ✅ [ ] ❌ | Lista packages |

## 6. LICENÇAS E DOCUMENTAÇÃO

| Item | Descrição | Status | Evidência |
|------|-----------|--------|----------|
| IQ-LIC-001 | Licença do software ativa e válida | [ ] ✅ [ ] ❌ | Certificado |
| IQ-LIC-002 | Período de validade: {{VALIDADE_LICENCA}} | [ ] ✅ [ ] ❌ | Documento licença |
| IQ-LIC-003 | Número de usuários licenciados: {{NUM_USUARIOS}} | [ ] ✅ [ ] ❌ | Contrato |
| IQ-DOC-001 | Manual de instalação disponível | [ ] ✅ [ ] ❌ | Cópia digital |
| IQ-DOC-002 | Especificações técnicas disponíveis | [ ] ✅ [ ] ❌ | Documentação |
| IQ-DOC-003 | Release notes da versão | [ ] ✅ [ ] ❌ | PDF release |

## 7. CONFIGURAÇÃO INICIAL DO SISTEMA

| Item | Descrição | Status | Evidência |
|------|-----------|--------|----------|
| IQ-CFG-001 | Banco de dados criado e configurado | [ ] ✅ [ ] ❌ | Script SQL |
| IQ-CFG-002 | Tabelas e estrutura de BD implementadas | [ ] ✅ [ ] ❌ | Diagrama ER |
| IQ-CFG-003 | Conexão BD ↔ Aplicação testada | [ ] ✅ [ ] ❌ | Log conexão |
| IQ-CFG-004 | Configurações de rede aplicadas | [ ] ✅ [ ] ❌ | Config files |
| IQ-CFG-005 | Firewall e portas configuradas | [ ] ✅ [ ] ❌ | Regras firewall |
| IQ-CFG-006 | SSL/TLS certificado instalado | [ ] ✅ [ ] ❌ | Certificado |

## 8. BACKUP E DISASTER RECOVERY

| Item | Descrição | Status | Evidência |
|------|-----------|--------|----------|
| IQ-BCK-001 | Rotina de backup automático configurada | [ ] ✅ [ ] ❌ | Script backup |
| IQ-BCK-002 | Frequência de backup: {{FREQUENCIA_BACKUP}} | [ ] ✅ [ ] ❌ | Agendamento |
| IQ-BCK-003 | Local de armazenamento backup: {{LOCAL_BACKUP}} | [ ] ✅ [ ] ❌ | Configuração |
| IQ-BCK-004 | Teste de restore realizado com sucesso | [ ] ✅ [ ] ❌ | Log restore |
| IQ-BCK-005 | Plano de disaster recovery documentado | [ ] ✅ [ ] ❌ | Documento DR |

## 9. SEGURANÇA E CONTROLE DE ACESSO

| Item | Descrição | Status | Evidência |
|------|-----------|--------|----------|
| IQ-SEC-001 | Usuários administradores criados | [ ] ✅ [ ] ❌ | Lista usuários |
| IQ-SEC-002 | Políticas de senha implementadas | [ ] ✅ [ ] ❌ | Config senha |
| IQ-SEC-003 | Perfis de acesso configurados (RBAC) | [ ] ✅ [ ] ❌ | Matriz acesso |
| IQ-SEC-004 | Audit trail ativo e funcional | [ ] ✅ [ ] ❌ | Logs audit |
| IQ-SEC-005 | Logs de sistema habilitados | [ ] ✅ [ ] ❌ | Config logs |
| IQ-SEC-006 | Criptografia de dados sensíveis ativa | [ ] ✅ [ ] ❌ | Config cripto |

## 10. INTEGRAÇÃO COM OUTROS SISTEMAS

| Item | Sistema Integrado | Status | Evidência |
|------|------------------|--------|----------|
| IQ-INT-001 | {{SISTEMA_INTEGRACAO_1}} | [ ] ✅ [ ] ❌ [ ] N/A | Config API |
| IQ-INT-002 | {{SISTEMA_INTEGRACAO_2}} | [ ] ✅ [ ] ❌ [ ] N/A | Log integração |
| IQ-INT-003 | {{SISTEMA_INTEGRACAO_3}} | [ ] ✅ [ ] ❌ [ ] N/A | Testes |

## 11. CRITÉRIOS DE ACEITAÇÃO

✅ **O sistema será considerado APROVADO na Qualificação de Instalação se:**

- Todos os itens obrigatórios do checklist estão CONFORMES (✅)
- Evidências fotográficas e documentais estão anexadas
- Desvios identificados foram documentados e possuem plano de ação
- Instalação aprovada pelo Responsável Técnico e Revisor de Qualidade
- Documentação de instalação está completa e arquivada

## 12. DESVIOS E NÃO CONFORMIDADES

| ID | Descrição do Desvio | Criticidade | Plano de Ação | Responsável | Prazo |
|----|--------------------|-----------|--------------|-----------  |-------|
| D-001 | | [ ] Crítico [ ] Maior [ ] Menor | | | ___/___/___ |
| D-002 | | [ ] Crítico [ ] Maior [ ] Menor | | | ___/___/___ |

## 13. CONCLUSÃO

### Status Final da Qualificação de Instalação:

- [ ] ✅ **APROVADO** - Sistema instalado conforme especificações
- [ ] ⚠️ **APROVADO COM RESSALVAS** - Desvios menores identificados com plano de ação
- [ ] ❌ **REPROVADO** - Não conformidades críticas impedem aprovação

### Observações:

{{OBSERVACOES_FINAIS}}

---

## APROVAÇÕES

| Papel | Nome | Assinatura | Data |
|-------|------|------------|------|
| Elaborado por | {{ELABORADOR}} | __________ | ___/___/___ |
| Revisado por | {{REVISOR}} | __________ | ___/___/___ |
| Aprovado por | {{APROVADOR}} | __________ | ___/___/___ |

---

**Documento gerado automaticamente pelo Digital Worker VSC**  
**Conforme ANVISA RDC 430/2020 e GAMP 5**  
**Versão do Template: 1.0**
