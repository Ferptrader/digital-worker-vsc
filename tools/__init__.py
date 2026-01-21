"""
Digital Worker VSC - Tools Package
Ferramentas para automação de Validação de Sistemas Computadorizados
"""

# from .browser_automation import BrowserTool
from .document_analyzer import DocumentAnalyzer
from .template_generator import TemplateGenerator
from .compliance_checker import ComplianceChecker

__all__ = [
        # 'BrowserTool',
    'DocumentAnalyzer',
    'TemplateGenerator',
    'ComplianceChecker'
]
