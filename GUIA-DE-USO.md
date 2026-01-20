# 📘 GUIA COMPLETO DE USO - Digital Worker VSC

## 🎯 O QUE É O DIGITAL WORKER VSC?

É um assistente inteligente que automatiza 80% do trabalho de um Analista de Validação de Sistemas Computadorizados (VSC).

Ele usa 4 agentes de IA que trabalham em equipe para:
- ✅ Criar documentação IQ/OQ/QP
- ✅ Fazer análise de riscos
- ✅ Planejar e executar testes
- ✅ Garantir conformidade com ANVISA/GAMP 5

---

## 🚀 COMO USAR (PASSO A PASSO)

### 1️⃣ PRIMEIRA VEZ - Configuração Inicial

#### Abra o terminal na pasta do projeto:
```bash
cd C:\Projetos\digital-worker-vsc-main
```

#### Configure sua chave OpenAI:
1. Renomeie `.env.example` para `.env`
2. Abra o arquivo `.env` com Bloco de Notas
3. Adicione sua chave:
```
OPENAI_API_KEY=sk-proj-SUA_CHAVE_AQUI
```
4. Salve o arquivo

---

### 2️⃣ RODANDO O DIGITAL WORKER

#### Comando básico:
```bash
python main.py
```

O Digital Worker vai iniciar e você verá os 4 agentes trabalhando:

```
🤖 [Gerente de Validação] Iniciando análise do projeto...
📝 [Especialista em Documentação] Preparando templates IQ/OQ/QP...
🎯 [Analista de Testes] Planejando casos de teste...
⚖️ [Auditor de Conformidade] Verificando requisitos ANVISA...
```

---

## 📂 ESTRUTURA DE PASTAS

```
digital-worker-vsc-main/
├── main.py                 # Arquivo principal - RODE ESTE!
├── requirements.txt        # Dependências (já instaladas)
├── .env                   # Suas chaves API (CONFIDENCIAL)
├── README.md              # Documentação do projeto
├── GUIA-DE-USO.md         # Este guia
├── templates/             # Cole seus templates de documentos aqui
│   ├── template_IQ.docx
│   ├── template_OQ.docx
│   └── template_PQ.docx
└── tools/                 # Ferramentas customizadas dos agentes
    └── __init__.py
```

---

## 💼 CASOS DE USO

### Caso 1: Criar Documentação IQ para um sistema novo

1. Prepare as informações do sistema:
   - Nome do sistema
   - Fabricante
   - Versão
   - Criticidade (Alto/Médio/Baixo)

2. Rode o Digital Worker:
```bash
python main.py
```

3. Os agentes vão:
   - Gerar o plano de validação
   - Criar documentação IQ baseada nos templates
   - Sugerir pontos de teste
   - Validar conformidade com RDC 430/2020

---

### Caso 2: Análise de Risco de um Sistema

1. Forneça dados do sistema:
   - Descrição funcional
   - Impacto na qualidade do produto
   - Dados críticos processados

2. O Digital Worker executa análise usando:
   - Metodologia ICH Q9
   - Matriz de criticidade GAMP 5
   - Identificação de controles necessários

3. Gera relatório de análise de risco automaticamente

---

### Caso 3: Planejamento de Testes OQ

1. Informe:
   - Especificações do sistema
   - Funções críticas
   - Requisitos regulatórios

2. O agente cria:
   - Casos de teste detalhados
   - Critérios de aceitação
   - Roteiro de execução
   - Formulários de evidência

---

## 🛠️ COMANDOS ÚTEIS

### Ver versão do Python:
```bash
python --version
```

### Atualizar dependências:
```bash
python -m pip install --upgrade -r requirements.txt
```

### Verificar se está tudo instalado:
```bash
python -m pip list
```

### Limpar cache do Python:
```bash
python -c "import shutil; shutil.rmtree('__pycache__', ignore_errors=True)"
```

---

## 🎓 OS 4 AGENTES E SUAS FUNÇÕES

### 🤵 1. Gerente de Validação
**Papel:** Coordena todo o processo
**Tarefas:**
- Entende os requisitos do projeto
- Distribui tarefas entre os agentes
- Garante que tudo siga o cronograma
- Toma decisões estratégicas

### 📝 2. Especialista em Documentação  
**Papel:** Cria toda a documentação
**Tarefas:**
- Elabora protocolos IQ/OQ/QP
- Gera relatórios de validação
- Documenta desvios e CAPAs
- Mantém rastreabilidade

### 🎯 3. Analista de Testes
**Papel:** Planeja e executa testes
**Tarefas:**
- Cria casos de teste
- Define critérios de aceitação
- Executa testes quando possível
- Documenta resultados

### ⚖️ 4. Auditor de Conformidade
**Papel:** Garante conformidade regulatória
**Tarefas:**
- Valida contra ANVISA RDC 430/2020
- Verifica GAMP 5
- Checa princípios ALCOA+
- Identifica não conformidades

---

## ❓ TROUBLESHOOTING

### Erro: "No module named 'crewai'"
**Solução:**
```bash
python -m pip install -r requirements.txt
```

### Erro: "OpenAI API key not found"
**Solução:**
1. Verifique se o arquivo `.env` existe
2. Abra o `.env` e confirme que tem:
```
OPENAI_API_KEY=sk-proj-...
```

### Erro: "Permission denied"
**Solução:**
- Execute o terminal como Administrador
- Ou rode: `python -m pip install --user -r requirements.txt`

### O programa trava ou demora muito
**Causas comuns:**
- Internet lenta (precisa conectar com OpenAI)
- Chave API inválida ou sem créditos
- Muitos processos rodando no PC

---

## 📞 PRÓXIMOS PASSOS

1. ✅ **Teste básico:** Rode `python main.py` e veja os agentes trabalhando
2. ✅ **Adicione templates:** Coloque seus documentos Word na pasta `templates/`
3. ✅ **Primeiro projeto:** Use para validar um sistema real
4. ✅ **Customize:** Edite `main.py` para adaptar ao seu fluxo

---

## 🎉 DICAS DE PRODUTIVIDADE

- 💡 **Use templates próprios:** Os agentes são mais eficientes com seus modelos de documentos
- 💡 **Forneça contexto:** Quanto mais informação você der, melhor o resultado
- 💡 **Revise sempre:** O Digital Worker é um assistente, não substitui revisão humana
- 💡 **Iteração:** Se não gostar do resultado, rode novamente com mais detalhes

---

## 📚 REFERÊNCIAS REGULATÓRIAS

- **ANVISA RDC 430/2020:** Validação de Sistemas Computadorizados
- **GAMP 5:** Good Automated Manufacturing Practice
- **ICH Q9:** Quality Risk Management
- **21 CFR Part 11:** Electronic Records (FDA)
- **ALCOA+:** Princípios de integridade de dados

---

## 🆘 PRECISA DE AJUDA?

Se tiver dúvidas:
1. Leia este guia novamente
2. Verifique o arquivo `README.md`
3. Confira se seguiu todos os passos de instalação
4. Teste com um exemplo simples primeiro

---

**Versão:** 1.0  
**Última atualização:** 20/01/2026  
**Criado por:** Fernando (Ferptrader)  
**Licença:** Uso interno

🚀 **Bom trabalho com seu Digital Worker VSC!**
