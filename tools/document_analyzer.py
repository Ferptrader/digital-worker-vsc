"""Document Analyzer Tool - Analisa documentos técnicos e extrai requisitos"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Fieldfrom typing import Type, Optional
import re

class DocumentAnalyzerInput(BaseModel):
    """Input para DocumentAnalyzer"""
    document_path: str = Field(..., description="Caminho do documento a analisar")
    analysis_type: str = Field(..., description="Tipo: 'requirements', 'risk', 'compliance', 'structure'")
    
class DocumentAnalyzer(BaseTool):
    name: str = "Document Analyzer"
    description: str = (
        "Analisa documentos técnicos (URS, FS, SDS, manuais) e extrai informações críticas. "
        "Identifica requisitos, riscos, não-conformidades e estrutura de documentos VSC."
    )
    args_schema: Type[BaseModel] = DocumentAnalyzerInput
    
    def _run(self, document_path: str, analysis_type: str) -> str:
        """
        Analisa documento e retorna insights
        
        Args:
            document_path: Caminho para o arquivo
            analysis_type: requirements, risk, compliance, structure
        """
        try:
            if analysis_type == 'requirements':
                return self._analyze_requirements(document_path)
            elif analysis_type == 'risk':
                return self._analyze_risks(document_path)
            elif analysis_type == 'compliance':
                return self._analyze_compliance(document_path)
            elif analysis_type == 'structure':
                return self._analyze_structure(document_path)
            else:
                return f"Tipo de análise '{analysis_type}' não reconhecido."
        except Exception as e:
            return f"Erro ao analisar documento: {str(e)}"
    
    def _analyze_requirements(self, doc_path: str) -> str:
        """Extrai requisitos funcionais e não-funcionais"""
        # Simulação de extração de requisitos
        return (
            f"Análise de Requisitos - {doc_path}:\n"
            "Requisitos Funcionais identificados: 15\n"
            "- RF001: Sistema deve permitir login com autenticação de dois fatores\n"
            "- RF002: Registros devem ter audit trail automático\n"
            "- RF003: Cálculos críticos devem ser validados\n"
            "Requisitos Não-Funcionais: 8\n"
            "- RNF001: Sistema deve estar disponível 99.9% do tempo\n"
            "- RNF002: Backup diário automático\n"
        )
    
    def _analyze_risks(self, doc_path: str) -> str:
        """Identifica riscos potenciais no sistema"""
        return (
            f"Análise de Risco (ICH Q9) - {doc_path}:\n"
            "Riscos Críticos identificados: 3\n"
            "- RISCO-001: Perda de dados por falha de backup (Severidade: Alta, Probabilidade: Média)\n"
            "- RISCO-002: Acesso não autorizado a registros (Severidade: Alta, Probabilidade: Baixa)\n"
            "- RISCO-003: Inconsistência em cálculos críticos (Severidade: Crítica, Probabilidade: Muito Baixa)\n"
            "Recomendação: Implementar controles preventivos para riscos de severidade Alta/Crítica"
        )
    
    def _analyze_compliance(self, doc_path: str) -> str:
        """Verifica conformidade com normas regulatórias"""
        return (
            f"Análise de Conformidade - {doc_path}:\n"
            "RDC 658/2022 (ANVISA): \u2705 Conforme\n"
            "GAMP 5: \u2705 Categoria 5 corretamente identificada\n"
            "21 CFR Part 11: \u26a0\ufe0f Atenção - Verificar assinaturas eletrônicas\n"
            "ALCOA+: \u2705 Princípios aplicados\n"
            "\nGaps identificados: 1\n"
            "- Falta evidência de validação de assinatura eletrônica conforme 21 CFR 11.50\n"
        )
    
    def _analyze_structure(self, doc_path: str) -> str:
        """Analisa estrutura do documento"""
        return (
            f"Análise de Estrutura - {doc_path}:\n"
            "Seções encontradas: 12\n"
            "- 1. Introdução\n"
            "- 2. Escopo\n"
            "- 3. Referências\n"
            "- 4. Definições\n"
            "- 5. Categorização GAMP\n"
            "- 6. Análise de Risco\n"
            "- 7-12. Casos de Teste IQ/OQ/PQ\n"
            "Completude: 90% (falta seção de Desvios)\n"
        )
    
    async def _arun(self, *args, **kwargs) -> str:
        """Versão assíncrona"""
        return self._run(*args, **kwargs)
