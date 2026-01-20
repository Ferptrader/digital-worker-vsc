# 🤖 Digital Worker VSC

**Automação Completa de Validação de Sistemas Computadorizados usando CrewAI**

## 🎯 O que é?

Digital Worker VSC é um time de agentes de IA especializados que automatiza **80% do trabalho** de um analista de VSC (Validação de Sistemas Computadorizados), conforme normas:

- ✅ **ANVISA**: RDC 658/2022, IN 134/2022, Guia 33
- ✅ **GAMP 5**: Categorização, Validação, Ciclo de Vida
- ✅ **FDA**: 21 CFR Part 11 (Assinaturas Eletrônicas)
- ✅ **ICH Q9**: Análise de Risco
- ✅ **ALCOA+**: Integridade de Dados

## 🛠️ Agentes do Time

### 1. 📊 Analista Técnico
- Categoriza sistemas (GAMP 3/4/5)
- Realiza análise de risco (ICH Q9)
- Define estratégia de validação
- Gera Plano de Validação (VP)

### 2. 📝 Escritor de Protocolos
- Gera protocolos **IQ** (Qualificação de Instalação)
- Gera protocolos **OQ** (Qualificação Operacional)
- Gera protocolos **PQ** (Qualificação de Performance)
- Cria Matriz de Rastreabilidade (RTM)

### 3. ✅ Revisor de Conformidade
- Valida completude documental
- Verifica rastreabilidade (RTM)
- Checa conformidade ANVISA/FDA
- Propõe CAPAs (Corrective Actions)

### 4. 🔍 Navegador de Sistemas
- Acessa sistemas via browser automation
- Executa testes automatizados (IQ/OQ/PQ)
- Captura evidências (screenshots, logs)
- Documenta desvios

## 🚀 Como Usar

### 1. Instalação

```bash
# Clone o repositório
git clone https://github.com/Ferptrader/digital-worker-vsc.git
cd digital-worker-vsc

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\\Scripts\\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Instale Playwright (para browser automation)
playwri ght install
```

### 2. Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# API Keys - Escolha um provider de LLM
OPENAI_API_KEY=sk-...
# ou
ANTHROPIC_API_KEY=sk-ant-...

# Supabase (opcional - para armazenar histórico)
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...

# Configurações do sistema a validar
SISTEMA_URL=https://lims.exemplo.com.br
SISTEMA_USER=usuario_teste
SISTEMA_PASSWORD=senha_teste
```

### 3. Execução Básica

```python
from main import criar_validacao_completa

# Validar um sistema LIMS
criar_validacao_completa(
    sistema_nome="LIMS Waters Empower 3",
    sistema_tipo="5",  # GAMP 5 (software customizado)
    criticidade="Alta"  # Sistema GxP crítico
)
```

### 4. Exemplos de Uso

```python
# Exemplo 1: Sistema ERP
criar_validacao_completa(
    sistema_nome="SAP ERP - Módulo QM",
    sistema_tipo="4",  # GAMP 4 (software configurável)
    criticidade="Média"
)

# Exemplo 2: GED (Gestão Eletrônica de Documentos)
criar_validacao_completa(
    sistema_nome="SharePoint GED Farmacêutica",
    sistema_tipo="4",
    criticidade="Alta"
)

# Exemplo 3: CDS (Chromatography Data System)
criar_validacao_completa(
    sistema_nome="Agilent OpenLab CDS",
    sistema_tipo="3",  # GAMP 3 (software standard)
    criticidade="Alta"
)
```

## 📁 Saídas Geradas

O Digital Worker VSC gera automaticamente:

```
output/
├── plano-validacao.docx       # Plano de Validação
├── analise-risco.xlsx         # Análise de Risco (ICH Q9)
├── protocolo-iq.docx          # IQ - Qualificação de Instalação
├── protocolo-oq.docx          # OQ - Qualificação Operacional
├── protocolo-pq.docx          # PQ - Qualificação de Performance
├── rtm-matriz-rastreabilidade.xlsx  # Matriz de Rastreabilidade
├── relatorio-execucao.pdf     # Relatório de Execução de Testes
├── evidencias/
│   ├── screenshot_001.png
│   ├── audit_trail_log.txt
│   └── config_export.json
└── relatorio-conformidade.pdf # Revisão de Conformidade + CAPAs
```

## ⚙️ Próximos Passos

### Implementar Ferramentas Customizadas

Você vai precisar criar as ferramentas na pasta `tools/`:

```bash
mkdir -p tools
touch tools/__init__.py
touch tools/browser_automation.py
touch tools/document_analyzer.py
touch tools/template_generator.py
touch tools/compliance_checker.py
```

Exemplo de `tools/browser_automation.py`:

```python
from crewai_tools import BaseTool
from browser_use import Agent as BrowserAgent

class BrowserTool(BaseTool):
    name: str = "Browser Automation Tool"
    description: str = "Navega sistemas web e executa testes automatizados"
    
    def _run(self, instruction: str) -> str:
        browser_agent = BrowserAgent(
            task=instruction,
            llm="gpt-4o"
        )
        result = browser_agent.run()
        return str(result)
```

### Criar Templates de Documentação

```bash
mkdir -p templates
# Adicione seus templates Word/Excel de IQ/OQ/PQ aqui
```

### Adicionar Knowledge Base

```bash
mkdir -p knowledge
# Adicione PDFs das normas:
# - RDC_658_2022.pdf
# - GAMP_5.pdf
# - 21_CFR_Part_11.pdf
# - ICH_Q9.pdf
```

## 📊 Benefícios

✅ **Reduz 80% do tempo** de documentação VSC  
✅ **Elimina erros humanos** em protocolos  
✅ **Garante conformidade** ANVISA/FDA  
✅ **Automatiza testes** repetitivos  
✅ **Rastreabilidade completa** (RTM automática)  
✅ **Escalabilidade** - valida múltiplos sistemas em paralelo

## 🛡️ Casos de Uso Reais

- 🔬 **LIMS** (Waters Empower, LabWare)
- 📦 **ERP** (SAP, Oracle)
- 📄 **GED** (SharePoint, Docuware)
- 📊 **CDS** (Agilent, Thermo)
- 🏭 **SCADA** (Siemens, Rockwell)
- 🧪 **BMS** (Building Management Systems)

## 👥 Contribua

Este é um projeto open-source! Contribua com:

- Novos templates de documentação
- Integrações com sistemas específicos
- Melhorias nos agentes
- Casos de uso reais

## 📝 Licença

MIT License - Veja LICENSE para detalhes

## 🚀 Deploy

### Opção 1: Local
Rode diretamente na sua máquina conforme instruções acima.

### Opção 2: CrewAI AMP Cloud
1. Acesse https://app.crewai.com
2. Importe este repositório
3. Configure variáveis de ambiente
4. Deploy com 1 clique

### Opção 3: Docker (em breve)
```bash
docker-compose up
```

## ❗ Importante

⚠️ **Ambiente Regulado**: Este digital worker auxilia na documentação, mas a **aprovação final** e **responsabilidade regulatória** permanecem com profissionais qualificados.

⚠️ **Validação do Worker**: Em ambientes GxP, o próprio digital worker pode precisar ser validado como ferramenta computadorizada.

---

**Desenvolvido por**: Ferptrader  
**Baseado em**: CrewAI Framework  
**Conformidade**: ANVISA RDC 658/2022, GAMP 5, 21 CFR Part 11
