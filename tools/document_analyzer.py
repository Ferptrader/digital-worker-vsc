"""Isolated replacement candidate for tools/document_analyzer.py; not qualified GxP."""
import os
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from .safe_document_core import analyze_json

class DocumentAnalyzerInput(BaseModel):
    document_path: str = Field(..., description="Caminho do documento")
    analysis_type: str = Field(..., description="requirements, risk, compliance, structure")

class DocumentAnalyzer(BaseTool):
    name: str = 'Document Analyzer'
    description: str = 'Extrai texto como evidência não verificada; não aprova conformidade GxP.'
    args_schema: Type[BaseModel] = DocumentAnalyzerInput

    def _run(self, document_path: str, analysis_type: str) -> str:
        root = os.environ.get('DWVSC_ALLOWED_ROOT')
        if not root:
            return '{"status":"NOT_VERIFIED","reason":"MISSING_ALLOWED_ROOT","gxp_compliance":"NOT_VERIFIED","gxp_approval":"NOT_GRANTED","gxp_release":"NOT_GRANTED"}'
        return analyze_json(document_path, analysis_type, root)
