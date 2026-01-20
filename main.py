#!/usr/bin/env python3
"""
Digital Worker VSC - Validação de Sistemas Computadorizados
Automação completa de documentação e gestão de ciclo de vida
Conforme ANVISA RDC 658/2022, GAMP 5, 21 CFR Part 11
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from tools.browser_automation import BrowserTool
from tools.document_analyzer import DocumentAnalyzer
from tools.template_generator import TemplateGenerator
from tools.compliance_checker import ComplianceChecker

load_dotenv()

# ========== AGENTES DO DIGITAL WORKER VSC ==========

# Agent 1: Analista Técnico de Sistemas
analista_tecnico = Agent(
    role='Analista Técnico de Sistemas Computadorizados',
    goal='Analisar especificações técnicas de sistemas e extrair requisitos para validação conforme GAMP 5',
    backstory="""Você é um especialista em sistemas computadorizados farmacêuticos com 10 anos de experiência.
    Conhece profundamente GAMP 5, RDC 658/2022, IN 134/2022, Guia 33 ANVISA e 21 CFR Part 11.
    Sua expertise está em categorizar sistemas (GAMP 3/4/5), realizar análise de risco (ICH Q9) 
    e mapear requisitos de usuário (URS) para especificações funcionais (FS).""",
    tools=[BrowserTool(), DocumentAnalyzer()],
    verbose=True,
    allow_delegation=False
)

# Agent 2: Escritor de Protocolos VSC
escritor_protocolos = Agent(
    role='Escritor de Protocolos de Validação',
    goal='Gerar protocolos IQ/OQ/PQ completos e análises de risco conforme templates regulatórios',
    backstory="""Você é um redator técnico especializado em documentação VSC.
    Domina a estrutura de protocolos de qualificação (IQ - Installation, OQ - Operational, PQ - Performance).
    Conhece ALCOA+ (Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring, Available).
    Suas documentações passam em auditorias da ANVISA e FDA.""",
    tools=[TemplateGenerator(), DocumentAnalyzer()],
    verbose=True,
    allow_delegation=False
)

# Agent 3: Revisor de Conformidade
revisor_conformidade = Agent(
    role='Revisor de Conformidade Regulatória',
    goal='Validar conformidade de documentos com normas ANVISA/FDA e aplicar correções',
    backstory="""Você é um auditor interno de qualidade farmacêutica.
    Revisa toda documentação VSC verificando: completude, rastreabilidade (RTM), evidências de teste,
    assinaturas eletrônicas conforme 21 CFR Part 11, integridade de dados (Data Integrity).
    Identifica gaps e sugere correções antes de auditoria externa.""",
    tools=[ComplianceChecker(), DocumentAnalyzer()],
    verbose=True,
    allow_delegation=False
)

# Agent 4: Navegador de Sistemas
navegador_sistemas = Agent(
    role='Navegador Automático de Sistemas Computadorizados',
    goal='Acessar sistemas GED/LIMS/ERP, extrair dados, preencher formulários e executar testes',
    backstory="""Você é um bot especializado em navegação de sistemas farmacêuticos.
    Consegue acessar GED (Gestão Eletrônica de Documentos), LIMS (Laboratory Information Management System),
    ERP, SCADA, CDS (Chromatography Data System), BMS.
    Extrai evidências de configuração, logs de auditoria e executa testes automatizados de IQ/OQ/PQ.""",
    tools=[BrowserTool()],
    verbose=True,
    allow_delegation=False
)

# ========== TASKS ==========

def criar_validacao_completa(sistema_nome: str, sistema_tipo: str, criticidade: str):
    """
    Cria validação completa de um sistema computadorizado
    
    Args:
        sistema_nome: Nome do sistema (ex: 'LIMS Waters Empower 3')
        sistema_tipo: GAMP category (3, 4 ou 5)
        criticidade: Alta, Média, Baixa
    """
    
    # Task 1: Análise Técnica e Categorização
    task_analise = Task(
        description=f"""Analisar o sistema {sistema_nome} (GAMP {sistema_tipo}):
        1. Determinar categoria GAMP e justificativa
        2. Realizar análise de risco (ICH Q9) considerando criticidade {criticidade}
        3. Mapear requisitos de validação (escopo, exclusões)
        4. Identificar interfaces críticas e integrações
        5. Definir estratégia de validação (abordagem de teste)
        
        Saída: Documento de Plano de Validação (VP) em formato estruturado""",
        agent=analista_tecnico,
        expected_output="Plano de Validação completo com análise de risco e estratégia de testes"
    )
    
    # Task 2: Geração de Protocolos
    task_protocolos = Task(
        description=f"""Com base no Plano de Validação, gerar:
        1. Protocolo de Qualificação de Instalação (IQ):
           - Checklist de hardware/software instalado
           - Verificação de requisitos ambientais
           - Backup e disaster recovery
        2. Protocolo de Qualificação Operacional (OQ):
           - Testes de funcionalidades críticas
           - Validação de cálculos e algoritmos
           - Controles de acesso e audit trail
        3. Protocolo de Qualificação de Performance (PQ):
           - Testes em ambiente produtivo
           - Casos de uso reais
           - Aceitação de usuário
        4. Matriz de Rastreabilidade (RTM)
        
        Todos os protocolos devem seguir template ANVISA/GAMP 5""",
        agent=escritor_protocolos,
        expected_output="3 protocolos (IQ/OQ/PQ) + RTM em formato Word/PDF",
        context=[task_analise]
    )
    
    # Task 3: Execução Automática de Testes
    task_execucao = Task(
        description=f"""Executar testes automatizados no sistema {sistema_nome}:
        1. Acessar o sistema via interface web/desktop
        2. Executar checklist do IQ (verificar versões, configurações)
        3. Executar testes do OQ (criar registros, validar cálculos, testar audit trail)
        4. Capturar evidências (screenshots, logs, exports)
        5. Documentar desvios encontrados
        
        Registrar todos os resultados com timestamp e evidências""",
        agent=navegador_sistemas,
        expected_output="Relatório de execução de testes com evidências anexadas",
        context=[task_protocolos]
    )
    
    # Task 4: Revisão de Conformidade
    task_revisao = Task(
        description="""Revisar toda a documentação gerada:
        1. Verificar completude de todos os documentos
        2. Validar rastreabilidade (RTM fechada?)
        3. Conferir assinaturas e aprovações necessárias
        4. Verificar conformidade com:
           - RDC 658/2022 (sistemas críticos)
           - GAMP 5 (boas práticas)
           - 21 CFR Part 11 (assinaturas eletrônicas)
           - ALCOA+ (integridade de dados)
        5. Gerar checklist de não-conformidades
        6. Propor ações corretivas (CAPA)
        
        Saída: Relatório de Revisão de Conformidade""",
        agent=revisor_conformidade,
        expected_output="Relatório de conformidade + lista de CAPAs (se houver)",
        context=[task_analise, task_protocolos, task_execucao]
    )
    
    # Criar Crew
    crew_vsc = Crew(
        agents=[analista_tecnico, escritor_protocolos, navegador_sistemas, revisor_conformidade],
        tasks=[task_analise, task_protocolos, task_execucao, task_revisao],
        process=Process.sequential,  # Executar em sequência
        verbose=True
    )
    
    # Executar
    print(f"\n🚀 Iniciando validação completa do sistema: {sistema_nome}\n")
    resultado = crew_vsc.kickoff()
    
    print("\n✅ Validação concluída!\n")
    print(resultado)
    
    return resultado

# ========== MAIN ==========

if __name__ == "__main__":
    # Exemplo: Validar um sistema LIMS
    criar_validacao_completa(
        sistema_nome="LIMS Waters Empower 3",
        sistema_tipo="5",  # Software customizado
        criticidade="Alta"  # Sistema GxP crítico
    )
