"""
Template Processor - Processa templates Word (.docx)
Preenche marcadores com dados gerados pelos agentes
"""

from docx import Document
from pathlib import Path

class TemplateProcessor:
    def __init__(self, templates_path="templates"):
        self.templates_path = Path(templates_path)
    
    def substituir_marcadores(self, doc, dados):
        for paragraph in doc.paragraphs:
            for key, value in dados.items():
                marcador = f"{{{{{key}}}}}"
                if marcador in paragraph.text:
                    inline = paragraph.runs
                    for run in inline:
                        if marcador in run.text:
                            run.text = run.text.replace(marcador, str(value))
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for key, value in dados.items():
                            marcador = f"{{{{{key}}}}}"
                            if marcador in paragraph.text:
                                for run in paragraph.runs:
                                    if marcador in run.text:
                                        run.text = run.text.replace(marcador, str(value))
        return doc
    
    def preencher_template(self, template_name, dados, output_path):
        template_path = self.templates_path / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template: {template_path}")
        
        doc = Document(template_path)
        doc = self.substituir_marcadores(doc, dados)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        
        return output_path
