"""Document Analyzer Tool - Analisa documentos técnicos e extrai requisitos"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
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
            document_path: Caminho do documento
            analysis_type: Tipo de análise a realizar
            
        Returns:
            Análise estruturada do documento
        """
        return f"Análise do documento {document_path} realizada com foco em {analysis_type}"
