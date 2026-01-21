#!/usr/bin/env python3
"""Script de teste para gerar protocolo IQ usando template"""

import json
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent))

from tools.template_generator import TemplateGenerator

def test_generate_iq():
    """Testa geração de protocolo IQ"""
    
    print("[*] Iniciando teste de geracao de Protocolo IQ...\n")
    
    # Dados de exemplo do sistema
    system_data = {
        "nome_sistema": "SAP ERP",
        "versao": "S/4HANA 2023",
        "fabricante": "SAP SE",
        "responsavel_tecnico": "Joao Silva",
        "revisor_qualidade": "Maria Santos",
        "aprovador": "Pedro Oliveira",
        "categoria_gamp": "5",
        "criticidade": "Critico",
        "especificacao_servidor": "Dell PowerEdge R740",
        "instalado_servidor": "Dell PowerEdge R740",
        "ram_requerida": "64GB DDR4",
        "ram_instalada": "64GB DDR4",
        "disco_requerido": "2TB SSD NVMe",
        "disco_disponivel": "2TB SSD NVMe",
        "cpu_requerida": "Intel Xeon Gold 6248R (2x24 cores)",
        "cpu_instalada": "Intel Xeon Gold 6248R (2x24 cores)",
        "so_requerido": "Red Hat Enterprise Linux 8.6",
        "so_instalado": "Red Hat Enterprise Linux 8.6",
        "bd_versao": "Oracle Database 19c Enterprise Edition",
        "servidor_versao": "SAP NetWeaver 7.5",
        "dependencias": "Java 11, SAP HANA Client 2.0",
        "validade_licenca": "31/12/2026",
        "num_usuarios": "500 usuarios nomeados",
        "frequencia_backup": "Diario as 22h00",
        "local_backup": "NAS Synology DS1821+ (RAID 6)",
        "sistema_integracao_1": "Salesforce CRM",
        "sistema_integracao_2": "Microsoft Dynamics 365",
        "sistema_integracao_3": "N/A",
        "observacoes_finais": "Sistema instalado conforme especificacoes do projeto. Todos os requisitos de hardware e software foram atendidos.",
        "elaborador": "Digital Worker VSC",
        "revisor": "Maria Santos"
    }
    
    # Criar gerador
    generator = TemplateGenerator()
    
    # Caminho de saída
    output_path = "./output/PRT-IQ-SAP-ERP-20260121.md"
    
    print("[*] Dados do Sistema:")
    print(f"  - Sistema: {system_data['nome_sistema']}")
    print(f"  - Versao: {system_data['versao']}")
    print(f"  - Fabricante: {system_data['fabricante']}")
    print(f"  - Categoria GAMP: {system_data['categoria_gamp']}")
    print(f"  - Criticidade: {system_data['criticidade']}\n")
    
    # Gerar protocolo
    print("[*] Gerando protocolo IQ...\n")
    
    result = generator._run(
        protocol_type="IQ",
        system_data=json.dumps(system_data),
        output_path=output_path
    )
    
    print("\n" + "="*70)
    print("RESULTADO:")
    print("="*70)
    print(result)
    print("="*70)
    
    # Verificar se arquivo foi criado
    if Path(output_path).exists():
        print(f"\n[OK] Arquivo gerado com sucesso: {output_path}")
        print(f"[*] Tamanho: {Path(output_path).stat().st_size} bytes")
    else:
        print(f"\n[ERRO] Arquivo nao foi criado em {output_path}")

if __name__ == "__main__":
    try:
        test_generate_iq()
    except Exception as e:
        print(f"\n[ERRO] {str(e)}")
        import traceback
        traceback.print_exc()
