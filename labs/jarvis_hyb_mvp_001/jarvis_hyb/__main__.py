"""Run via python -m jarvis_hyb verify ..."""
import argparse
import csv
import json
import os
from pathlib import Path
import sys
from .verifier import run, sha256, file_is_safe


def csv_safe(x):
    """Avoid accidental Excel formula interpretation in CSV exports."""
    s=str(x if x is not None else '')
    return "'"+s if s and s.lstrip().startswith(('=','+','-','@','\t','\r')) else s


def write_csv(path, rows, keys):
    with path.open('x',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=keys,delimiter=';',extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({k:csv_safe(row.get(k,'')) for k in keys})


def main(argv=None):
    parser=argparse.ArgumentParser(prog='jarvis_hyb',description='SIM-EMS v0.4: offline deterministic verifier; NEVER GxP release.')
    commands=parser.add_subparsers(dest='command',required=True)
    v=commands.add_parser('verify')
    v.add_argument('--fixture-dir',type=Path,default=Path('fixtures'))
    v.add_argument('--output-dir',type=Path,required=True)
    v.add_argument('--candidate-csv',type=Path,default=None)
    v.add_argument('--restored-csv',type=Path,default=None)
    args=parser.parse_args(argv)
    if args.command!='verify':
        return 2
    source=args.fixture_dir.resolve()
    output=args.output_dir
    if output.is_symlink() or output.exists():
        parser.error('OUTPUT_DIR_EXISTS: use an empty NEW output directory, never overwrite controlled evidence.')
    target=output.resolve()
    if target==source or source in target.parents:
        parser.error('OUTPUT_INSIDE_FIXTURE_FORBIDDEN: use another output directory.')
    for label,filepath in [('fixture manifest',source/'manifest.json'),('candidate export',args.candidate_csv),('restored export',args.restored_csv)]:
        if filepath is not None and filepath.is_symlink():
            parser.error('SYMLINK_INPUT_REJECTED: '+label)
    result=run(source,args.candidate_csv,args.restored_csv)
    try:
        target.mkdir(parents=True,exist_ok=False)
        (target/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        write_csv(target/'findings.csv',result['findings'],['id','severity','item','message'])
        write_csv(target/'traceability.csv',result['traceability'],['urs_id','risk_id','control_id','test_id','evidence_expected','execution_status'])
        summary=[
          'JARVIS-HYB-MVP-001 — RESULTADO DA VERIFICAÇÃO ESTRUTURAL',
          'Escopo: SIM-EMS, 100% sintético, offline, somente verificação estrutural',
          'Estado da fonte: '+result['source_integrity_status'],
          'Resultado estrutural: '+result['documentary_structural_status'],
          'G0/G4/G5: HOLD (inalterados)',
          'OQ executados: 0/16; testes do harness executados: 0/22',
          'Aprovação GxP: NÃO AUTORIZADA',
          f"Achados: {result['counts']['findings']} | vínculos de teste: {result['counts']['traces']}",
          'PASS de regra NÃO comprova validação/qualificação/aprovação.',
          '', 'Arquivos gerados contêm dados sintéticos. Manifesto SHA256SUMS lista seus hashes; não é assinatura.'
        ]
        (target/'summary.txt').write_text('\n'.join(summary)+'\n',encoding='utf-8')
        files=['verification.json','findings.csv','traceability.csv','summary.txt']
        (target/'SHA256SUMS.txt').write_text(''.join(f'{sha256(target/f)}  {f}\n' for f in files),encoding='utf-8')
        print('\n'.join(summary))
        print('\nResultados:',target)
    except (OSError,ValueError) as exc:
        print('Erro ao gravar resultados: '+str(exc),file=sys.stderr)
        return 3
    # Returns nonzero on structural fail/hold for CI. Planning holds G0/G4/G5 do not fail clean fixture regression.
    return 0 if result['documentary_structural_status']=='PASS' else 1


if __name__=='__main__':
    sys.exit(main())
