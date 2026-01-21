"""Template Generator Tool - Gera protocolos IQ/OQ/PQ a partir de templates"""
from crewai.tools import BaseTool
from typing import Type, Optional, Dict
from pydantic import BaseModel, Field
from pathlib import Path
import json
from datetime import datetime
import re

class TemplateGeneratorInput(BaseModel):
    """Input para TemplateGenerator"""
    protocol_type: str = Field(..., description="Tipo: 'IQ', 'OQ', 'PQ', 'VP', 'ARI'")
    system_data: str = Field(..., description="Dados do sistema em formato JSON")
    output_path: str = Field(..., description="Caminho para salvar documento gerado")

class TemplateGenerator(BaseTool):
    name: str = "Template Generator"
    description: str = (
        "Gera protocolos de validação VSC (IQ/OQ/PQ, Plano de Validação, Análise de Risco) "
        "a partir de templates Markdown preenchendo com dados do sistema automaticamente."
    )
    args_schema: Type[BaseModel] = TemplateGeneratorInput
    
    def _run(self, protocol_type: str, system_data: str, output_path: str) -> str:
        """
        Gera protocolo a partir de template
        
        Args:
            protocol_type: IQ, OQ, PQ, VP, ARI
            system_data: JSON com dados do sistema
            output_path: Caminho para salvar
        """
        try:
            # Parse system data
            data = json.loads(system_data) if isinstance(system_data, str) else system_data
            
            # Mapa de templates
            template_map = {
                'IQ': 'template_iq.md',
                'OQ': 'template_oq.md',
                'PQ': 'template_pq.md',
                'VP': 'template_vp.md',
                'ARI': 'template_ari.md'
            }
            
            if protocol_type not in template_map:
                return f"Tipo de protocolo '{protocol_type}' não reconhecido."
            
            # Ler template
            template_path = Path(__file__).parent.parent / 'templates' / template_map[protocol_type]
            
            if not template_path.exists():
                return f"Template não encontrado: {template_path}"
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Preencher template
            documento = self._fill_template(template_content, data)
            
            # Salvar documento
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(documento)
            
            return f"✅ Protocolo {protocol_type} gerado com sucesso!\n\nArquivo: {output_path}\n\nPrévia:\n{documento[:300]}..."
            
        except Exception as e:
            return f"❌ Erro ao gerar protocolo: {str(e)}"
    
    def _fill_template(self, template: str, data: Dict) -> str:
        """
        Substitui marcadores {{VARIAVEL}} pelos dados reais
        """
        # Adicionar data atual automaticamente
        data['DATA_DOCUMENTO'] = datetime.now().strftime('%Y%m%d')
        data['DATA_ELABORACAO'] = datetime.now().strftime('%d/%m/%Y')
        
        # Valores padrão para campos comuns
        defaults = {
            'NOME_SISTEMA': 'Sistema Não Especificado',
            'VERSAO_SISTEMA': 'N/A',
            'FABRICANTE': 'N/A',
            'RESPONSAVEL_TECNICO': 'A definir',
            'REVISOR_QUALIDADE': 'A definir',
            'APROVADOR': 'A definir',
            'CATEGORIA_GAMP': '5',
            'CRITICIDADE': 'Alta',
            'OBSERVACOES_FINAIS': 'Nenhuma observação adicional.',
            'ELABORADOR': 'Digital Worker VSC',
            'REVISOR': 'A definir',
            'ESPECIFICACAO_SERVIDOR': 'A definir',
            'INSTALADO_SERVIDOR': 'A verificar',
            'RAM_REQUERIDA': 'A definir',
            'RAM_INSTALADA': 'A verificar',
            'DISCO_REQUERIDO': 'A definir',
            'DISCO_DISPONIVEL': 'A verificar',
            'CPU_REQUERIDA': 'A definir',
            'CPU_INSTALADA': 'A verificar',
            'SO_REQUERIDO': 'A definir',
            'SO_INSTALADO': 'A verificar',
            'BD_VERSAO': 'A definir',
            'SERVIDOR_VERSAO': 'A definir',
            'DEPENDENCIAS': 'A definir',
            'VALIDADE_LICENCA': 'A definir',
            'NUM_USUARIOS': 'A definir',
            'FREQUENCIA_BACKUP': 'A definir',
            'LOCAL_BACKUP': 'A definir',
            'SISTEMA_INTEGRACAO_1': 'N/A',
            'SISTEMA_INTEGRACAO_2': 'N/A',
            'SISTEMA_INTEGRACAO_3': 'N/A',
        }
        
        # Mesclar com valores padrão
        full_data = {**defaults, **data}
        
        # Substituir todos os marcadores {{VARIAVEL}}
        def replace_marker(match):
            key = match.group(1)
            return str(full_data.get(key, f'{{{{MISSING: {key}}}}}'))
        
        # Regex para encontrar {{VARIAVEL}}
        filled_template = re.sub(r'\{\{(\w+)\}\}', replace_marker, template)
        
        return filled_template
    
    async def _arun(self, *args, **kwargs) -> str:
        """Versão assíncrona"""
        return self._run(*args, **kwargs)
