# JARVIS-HYB-MVP-001 no GitHub Actions (F2)

Este diretório contém cópia byte a byte do núcleo Python do MVP v0.1.3 testado no Windows e dados **100% sintéticos** SIM-EMS. F1 continua versão 0.1.0 no código-fonte; F2 adiciona `ci_assert.py` e um workflow manual. Não se conectam produção/cliente, OpenAI API, modelos ou outros endpoints.

## Verificação local, Linux/macOS/Python 3.10+

No diretório `labs/jarvis_hyb_mvp_001`:

```bash
python -m unittest discover -s tests -v
python -m jarvis_hyb verify --fixture-dir fixtures --output-dir reports/clean
python -m jarvis_hyb verify --fixture-dir fixtures --candidate-csv examples/exportacao_alterada_demo.csv --output-dir reports/negative  # retorno 1 esperado
python ci_assert.py reports
```

A verificação negativa foi desenhada para retornar código 1. Ela NÃO representa falha da bateria se o resultado for detectado como esperado.

## Metodologia

- `PASS` = somente regra estrutural com fixture sintética; nunca aprovação GxP;
- 20/20 testes do verificador ≠ 22 testes HT de implementação do harness;
- G0/G4/G5 permanecem HOLD; nenhuma OQ foi executada;
- SHA-256 local verifica bytes de fontes distribuídas, não proveniência externa ou assinatura eletrônica.

O workflow somente é acionado manualmente (`workflow_dispatch`) quando for instalado sob aprovação específica no branch padrão do repositório. Não está agendado, não faz deploy e não executa serviços externos.
