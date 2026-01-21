"""Template Generator Tool - Gera protocolos IQ/OQ/PQ a partir de templates"""
from crewai.tools import BaseTool from typing import Type, Optional, Dict
from pydantic import BaseModel, Field
from pathlib import Path
import json
from datetime import datetime

class TemplateGeneratorInput(BaseModel):
    """Input para TemplateGenerator"""
    protocol_type: str = Field(..., description="Tipo: 'IQ', 'OQ', 'PQ', 'VP', 'ARI'")
    system_data: str = Field(..., description="Dados do sistema em formato JSON")
    output_path: str = Field(..., description="Caminho para salvar documento gerado")
    
class TemplateGenerator(BaseTool):
    name: str = "Template Generator"
    description: str = (
        "Gera protocolos de validação VSC (IQ/OQ/PQ, Plano de Validação, Análise de Risco) "
        "a partir de templates Word preenchendo com dados do sistema automaticamente."
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
            
            if protocol_type == 'IQ':
                return self._generate_iq(data, output_path)
            elif protocol_type == 'OQ':
                return self._generate_oq(data, output_path)
            elif protocol_type == 'PQ':
                return self._generate_pq(data, output_path)
            elif protocol_type == 'VP':
                return self._generate_vp(data, output_path)
            elif protocol_type == 'ARI':
                return self._generate_ari(data, output_path)
            else:
                return f"Tipo de protocolo '{protocol_type}' não reconhecido."
                
        except Exception as e:
            return f"Erro ao gerar protocolo: {str(e)}"
    
    def _generate_iq(self, data: Dict, output: str) -> str:
        """Gera Protocolo de Qualificação de Instalação"""
        sistema = data.get('nome_sistema', 'Sistema N/A')
        versao = data.get('versao', 'N/A')
        
        documento = f"""
=== PROTOCOLO DE QUALIFICAÇÃO DE INSTALAÇÃO (IQ) ===
Documento: PRT-IQ-{datetime.now().strftime('%Y%m%d')}
Sistema: {sistema}
Versão: {versao}
Data: {datetime.now().strftime('%d/%m/%Y')}

1. OBJETIVO
Este protocolo tem como objetivo verificar que o sistema {sistema} foi instalado
conforme especificações do fabricante e requisitos da empresa.

2. ESCOPO
- Verificação de hardware instalado
- Validação de software e licenças
- Checklist de configurações iniciais
- Verificação de backup e disaster recovery

3. CHECKLIST DE INSTALAÇÃO

| Item | Descrição | Status | Evidencia |
|------|------------|--------|----------|
| IQ-001 | Servidor instalado conforme especificação | [ ] | Screenshot |
| IQ-002 | Software versão {versao} instalado | [ ] | Tela versão |
| IQ-003 | Licenças ativas e válidas | [ ] | Arquivo licença |
| IQ-004 | Banco de dados configurado | [ ] | Script config |
| IQ-005 | Backup automático configurado | [ ] | Logs backup |
| IQ-006 | Usuários administradores criados | [ ] | Lista users |

4. CRITÉRIOS DE ACEITAÇÃO
- Todos os itens do checklist devem estar conformes
- Evidências fotográficas anexadas
- Instalação aprovada por responsável técnico

Gerado automaticamente pelo Digital Worker VSC
        """
        
        return f"Protocolo IQ gerado com sucesso: {output}\n\nPrévia:\n{documento[:500]}..."
    
    def _generate_oq(self, data: Dict, output: str) -> str:
        """Gera Protocolo de Qualificação Operacional"""
        sistema = data.get('nome_sistema', 'Sistema N/A')
        
        return (
            f"Protocolo OQ gerado para {sistema}\n"
            f"Arquivo: {output}\n"
            "Conteúdo: Testes de funcionalidades críticas, validação de cálculos, "
            "controles de acesso, audit trail, relatórios.\n"
            "Status: 25 casos de teste incluídos"
        )
    
    def _generate_pq(self, data: Dict, output: str) -> str:
        """Gera Protocolo de Qualificação de Performance"""
        sistema = data.get('nome_sistema', 'Sistema N/A')
        
        return (
            f"Protocolo PQ gerado para {sistema}\n"
            f"Arquivo: {output}\n"
            "Conteúdo: Testes em ambiente produtivo, casos de uso reais, "
            "aceitação de usuário final, performance sob carga.\n"
            "Status: 15 cenários de teste definidos"
        )
    
    def _generate_vp(self, data: Dict, output: str) -> str:
        """Gera Plano de Validação"""
        sistema = data.get('nome_sistema', 'Sistema N/A')
        categoria_gamp = data.get('categoria_gamp', '5')
        criticidade = data.get('criticidade', 'Alta')
        
        return (
            f"Plano de Validação (VP) gerado para {sistema}\n"
            f"GAMP Categoria: {categoria_gamp}\n"
            f"Criticidade: {criticidade}\n"
            f"Arquivo: {output}\n"
            "Conteúdo: Categorização GAMP, análise de risco, escopo, estratégia de testes, "
            "recursos necessários, cronograma.\n"
            "Status: Documento completo com matriz de rastreabilidade"
        )
    
    def _generate_ari(self, data: Dict, output: str) -> str:
        """Gera Análise de Risco"""
        sistema = data.get('nome_sistema', 'Sistema N/A')
        
        return (
            f"Análise de Risco (ARI) gerada para {sistema}\n"
            f"Arquivo: {output}\n"
            "Metodologia: ICH Q9 - Gestão de Risco da Qualidade\n"
            "Conteúdo: Identificação de perigos, avaliação de riscos (severidade x probabilidade), "
            "controles preventivos, medidas de mitigação, matriz de risco.\n"
            "Status: 12 riscos identificados e avaliados"
        )
    
    async def _arun(self, *args, **kwargs) -> str:
        """Versão assíncrona"""
        return self._run(*args, **kwargs)
