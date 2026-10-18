"""Offline assurance checks on the SIM-EMS synthetic CSV/CSA planning package.

NO external network, LLM, regulatory approval, agent execution or application OQ.
No third-party dependencies. Byte integrity is checked against a fixture manifest;
it is NOT a cryptographic signature or proof of regulated provenance.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

COLUMNS = ('id_evento','id_sensor','valor_c','unidade','timestamp_iso8601','status','id_configuracao')
DATASET_ROWS = 20  # SIM-EMS-v0.4 scenario expectation, NOT a regulatory standard.
ID_PATTERN = {
    'URS': re.compile(r'^URS-\d{3}$'),
    'RISKS': re.compile(r'^RSK-\d{3}$'),
    'OQ': re.compile(r'^OQ-\d{3}$'),
}
EXPECTED_ROWS = {'URS': 12, 'RISKS': 10, 'OQ': 16}
EXPECTED_LENGTHS = {'URS':5, 'RISKS':7, 'OQ':9}
SEVERITY = ('CRITICAL','HIGH','MEDIUM','INFO')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_is_safe(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def split_refs(raw: Any) -> set[str]:
    if not isinstance(raw,str):
        return set()
    return set(part.strip() for part in raw.split(';') if part.strip())


def _as_decimal(value: str) -> Decimal | None:
    try:
        dec = Decimal(value.strip())
        return dec if dec.is_finite() else None
    except (InvalidOperation, AttributeError):
        return None


def validate_csv(path: Path) -> tuple[list[dict[str,str]],list[dict[str, Any]]]:
    problems: list[dict[str,Any]] = []
    rows: list[dict[str,str]] = []

    def add(code: str, message: str, severity: str = 'HIGH', item: str = 'CSV') -> None:
        problems.append({'id':code,'severity':severity,'item':item,'message':message})

    try:
        with path.open('r',encoding='utf-8-sig',newline='') as f:
            rd = csv.DictReader(f,delimiter=';',restkey='__overflow__',restval=None)
            if tuple(rd.fieldnames or []) != COLUMNS:
                add('CSV-001', 'Cabeçalho diferente dos 7 campos controlados do SIM-EMS v0.4.')
            rows=list(rd)
    except (UnicodeError, OSError, csv.Error) as exc:
        add('CSV-000',f'Leitura CSV inválida: {type(exc).__name__}')
        return [],problems

    if len(rows)!=DATASET_ROWS:
        add('CSV-002',f'Contagem divergente: {len(rows)} versus {DATASET_ROWS} esperados.')
    seen: set[str] = set()
    for number,row in enumerate(rows,2):
        if None in row or '__overflow__' in row:
            add('CSV-003',f'Linha {number}: quantidade de colunas inválida.',item=str(number))
        vals=[row.get(c) for c in COLUMNS]
        if any(v is None or not isinstance(v,str) or not v.strip() for v in vals):
            add('CSV-004',f'Linha {number}: campo obrigatório vazio/ausente.',item=str(number))
            continue
        identifier=row['id_evento']
        if identifier in seen:
            add('CSV-005',f'Linha {number}: evento duplicado: {identifier}.',item=identifier)
        seen.add(identifier)
        if row['unidade'] != '°C':
            add('CSV-006',f'Linha {number}: unidade divergente.',item=identifier)
        if row['status'] not in {'VALID','INVALID','UNAVAILABLE'}:
            add('CSV-007',f'Linha {number}: status fora de domínio.',item=identifier)
        if _as_decimal(row['valor_c']) is None:
            add('CSV-008',f'Linha {number}: valor_c não numérico/finito.',item=identifier)
        try:
            dt=datetime.fromisoformat(row['timestamp_iso8601'])
            if not dt.tzinfo or dt.utcoffset() is None:
                raise ValueError('timestamp without explicit offset')
        except ValueError:
            add('CSV-009',f'Linha {number}: timestamp ISO8601 sem offset explícito/válido.',item=identifier)
    return rows,problems


def compare_csv(reference: list[dict[str,str]],candidate: list[dict[str,str]], kind: str) -> dict[str,Any]:
    """Literal, full-field 20/20 comparison. Does not prove real backup/export/OQ."""
    left = {r.get('id_evento'):r for r in reference}
    right = {r.get('id_evento'):r for r in candidate}
    diffs=[]
    for id_ in sorted(set(left)|set(right)):
        if id_ not in left or id_ not in right:
            diffs.append({'event_id':id_,'field':'id_evento','reference':str(id_ in left),'candidate':str(id_ in right)})
            continue
        for key in COLUMNS:
            if left[id_].get(key)!=right[id_].get(key):
                diffs.append({'event_id':id_,'field':key,'reference':left[id_].get(key),'candidate':right[id_].get(key)})
    return {'kind':kind,'status':'PASS' if not diffs and len(candidate)==DATASET_ROWS else 'FAIL',
            'compared_reference_records':len(reference), 'compared_candidate_records':len(candidate),
            'compared_fields':list(COLUMNS),'differences':diffs,
            'interpretation':'Comparação sintética de arquivos; não constitui teste OQ executado nem prova de operação de backup/export.'}


def run(fixture_dir: Path, candidate_csv: Path|None = None, restored_csv: Path|None = None) -> dict[str,Any]:
    findings: list[dict[str,Any]]=[]
    checks:list[dict[str,Any]]=[]
    traceability:list[dict[str,str]]=[]
    manifest_status='HOLD'

    def finding(code:str, severity:str, item:str, message:str) -> None:
        if not any(f['id']==code and f['item']==item for f in findings):
            findings.append({'id':code,'severity':severity,'item':item,'message':message})

    def check(code:str,status:str,message:str) -> None:
        checks.append({'id':code,'status':status,'detail':message})

    root=fixture_dir.resolve()
    manifest_path=root/'manifest.json'
    try:
        if not file_is_safe(manifest_path):
            raise ValueError('manifest not found or symlink')
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        if not isinstance(manifest,dict) or manifest.get('fixture_revision')!='v0.4' or manifest.get('provenance')!='SYNTHETIC_TEST_FIXTURE_NOT_GXP':
            raise ValueError('unrecognized fixture version/provenance')
        inputs=manifest['declared_inputs']
        if set(inputs)!={'requirements_json','readings_csv'}:
            raise ValueError('missing/extra manifest input labels')
        paths={}
        for key in ('requirements_json','readings_csv'):
            item=inputs[key]
            filename=item['file']
            if not isinstance(filename,str) or Path(filename).name!=filename or filename in ('.','..'):
                raise ValueError('unsafe input filename')
            path=root/filename
            if not file_is_safe(path) or not re.fullmatch('[0-9a-f]{64}',str(item['sha256'])):
                raise ValueError('input missing, symlink or invalid digest')
            if sha256(path)!=item['sha256']:
                raise ValueError('SHA-256 mismatch for '+key)
            paths[key]=path
        manifest_status='PASS'
        check('INT-001','PASS','Manifesto sintético v0.4 e SHA-256 dos 2 arquivos conferidos.')
    except (ValueError,KeyError,TypeError,UnicodeError,OSError,json.JSONDecodeError) as exc:
        finding('INT-001','CRITICAL','manifest','Proveniência/integridade não confirmada: '+str(exc))
        check('INT-001','HOLD','Fontes bloqueadas por manifesto, versão ou hash divergente.')
        return finish(findings,checks,traceability,{},'HOLD')

    try:
        data=json.loads(paths['requirements_json'].read_text(encoding='utf-8'))
        if not isinstance(data,dict) or set(data)!={'URS','RISKS','OQ'}:
            raise ValueError('mandatory URS/RISKS/OQ sections absent or extra')
        for kind,expected in EXPECTED_ROWS.items():
            rows=data[kind]
            if not isinstance(rows,list) or any(not isinstance(row,list) or len(row)!=EXPECTED_LENGTHS[kind] for row in rows):
                raise ValueError(f'invalid {kind} row layout')
    except (ValueError, UnicodeError, json.JSONDecodeError, TypeError) as exc:
        finding('DAT-001','CRITICAL','JSON','Esquema de dados não interpretável: '+str(exc))
        check('DAT-001','FAIL','Esquema URS/risco/OQ inválido; não avaliar vínculos.')
        return finish(findings,checks,traceability,{},'HOLD')

    # Duplicate IDs cannot silently overwrite source records in dictionaries.
    indexed={}
    for kind in ('URS','RISKS','OQ'):
        rows=data[kind]
        ids=[row[0] for row in rows]
        bad=[str(i) for i in ids if not isinstance(i,str) or not ID_PATTERN[kind].fullmatch(i)]
        dup=sorted({i for i in ids if ids.count(i)>1},key=str)
        if len(rows)!=EXPECTED_ROWS[kind]:
            finding('DAT-COUNT','HIGH',kind,f'{kind}: {len(rows)} registros; esperado {EXPECTED_ROWS[kind]} para o cenário fixo.')
        for i in bad:
            finding('DAT-ID','HIGH',kind,f'Identificador inválido: {i}')
        for i in dup:
            finding('DAT-DUP','HIGH',str(i),f'ID duplicado na seção {kind}.')
        indexed[kind]={r[0]:r for r in rows if isinstance(r[0],str)}
    check('DAT-001','FAIL' if any(f['id'].startswith('DAT-') for f in findings) else 'PASS',
          'Formato, quantidades do cenário fixo e unicidade de IDs das seções URS/RISKS/OQ.')

    riskmap=indexed['RISKS']
    ursmap=indexed['URS']
    oqmap=indexed['OQ']
    for req in data['URS']:
        uid,cat,description,level,rid=req
        if not isinstance(rid,str) or rid not in riskmap:
            finding('RTM-001','HIGH',str(uid),'URS sem risco relacionado existente.')
        if any(not isinstance(v,str) or not v.strip() for v in (uid,cat,description,level,rid)):
            finding('RTM-002','HIGH',str(uid),'URS com campo documental obrigatório vazio.')
        if level not in ('Alta','Média','Baixa'):
            finding('RTM-003','MEDIUM',str(uid),'Criticidade inválida.')
    for risk in data['RISKS']:
        rid,title,effect,level,ctrl,mitigation,recommended=risk
        if any(not isinstance(v,str) or not v.strip() for v in risk):
            finding('RTM-004','HIGH',str(rid),'Risco/controle com campo obrigatório vazio.')
        if not isinstance(ctrl,str) or not re.fullmatch(r'^CTRL-\d{3}$',ctrl):
            finding('RTM-005','HIGH',str(rid),'ID de controle inválido.')
        if level not in ('Alta','Média','Baixa'):
            finding('RTM-006','MEDIUM',str(rid),'Criticidade do risco inválida.')
        expected=split_refs(recommended)
        actual={o[0] for o in data['OQ'] if o[2]==rid}
        if expected!=actual:
            finding('RTM-007','HIGH',str(rid),f'Casos planejados inconsistentes: lista={sorted(expected)}, RTM={sorted(actual)}.')
        if not actual:
            finding('RTM-008','HIGH',str(rid),'Risco sem teste relacionado.')
    for oq in data['OQ']:
        oid,uid,rid,title,pre,steps,expected,evidence,level=oq
        if uid not in ursmap:
            finding('RTM-009','HIGH',str(oid),f'URS não encontrada: {uid}.')
        if rid not in riskmap:
            finding('RTM-010','HIGH',str(oid),f'Risco não encontrado: {rid}.')
        if uid in ursmap and rid!=ursmap[uid][4]:
            finding('RTM-011','HIGH',str(oid),f'URS {uid} não referencia o risco {rid}.')
        if any(not isinstance(v,str) or not v.strip() for v in (title,pre,steps,expected,evidence,level)):
            finding('RTM-012','HIGH',str(oid),'Teste sem pré-condição, passos, resultado esperado ou evidência esperada.')
        if level not in ('Alta','Média','Baixa'):
            finding('RTM-013','MEDIUM',str(oid),'Criticidade inválida.')
        traceability.append({'urs_id':str(uid),'risk_id':str(rid),
                             'control_id':str(riskmap[rid][4]) if rid in riskmap else 'UNKNOWN',
                             'test_id':str(oid),'evidence_expected':str(evidence),'execution_status':'NOT_EXECUTED'})
    for req in data['URS']:
        if not any(oq[1]==req[0] for oq in data['OQ']):
            finding('RTM-014','HIGH',str(req[0]),'Requisito sem caso de teste planejado.')

    check('RTM-001','FAIL' if any(f['id'].startswith('RTM') for f in findings) else 'PASS',
          'URS→risco→controle→OQ consistentes estruturalmente; não atesta suficiência semântica/regulatória.')

    rows,errors=validate_csv(paths['readings_csv'])
    findings.extend(errors)
    check('CSV-001','FAIL' if errors else 'PASS',
          f'Dataset sintético de leitura: {len(rows)}/{DATASET_ROWS} eventos e 7 campos críticos inspecionados.')

    comparisons={}
    for kind,candidate in [('export',candidate_csv),('restored',restored_csv)]:
        if candidate is None:
            check('CMP-'+kind.upper(),'NOT_EXECUTED',f'Arquivo {kind} não fornecido; nenhuma alegação de OQ.')
        else:
            if not file_is_safe(candidate):
                finding('CMP-001','HIGH',kind,'Arquivo de comparação inexistente ou symlink.')
                check('CMP-'+kind.upper(),'HOLD','Arquivo não elegível à comparação.')
            else:
                candidate_rows,candidate_errors=validate_csv(candidate)
                for error in candidate_errors:
                    finding('CMP-'+error['id'],error['severity'],kind+':'+str(error['item']),error['message'])
                comparison=compare_csv(rows,candidate_rows,kind)
                comparisons[kind]=comparison
                if candidate_errors:
                    comparison['status']='FAIL'
                if comparison['differences']:
                    finding('CMP-DIFF','HIGH',kind,f"{len(comparison['differences'])} divergências na reconciliação {kind} 20/20.")
                check('CMP-'+kind.upper(),comparison['status'],f'Comparação estrutural {kind} (20/20); NÃO é teste OQ do sistema.')

    # Always preserve the execution boundary. OQ/HT only have procedures/plans in this pilot.
    check('OQ-EXEC','NOT_EXECUTED','16 fichas OQ são planos; sem aplicação SIM-EMS executável ou executor de OQ.')
    check('HT-EXEC','NOT_EXECUTED','22 testes operacionais de harness não executados neste MVP.')
    check('G4-CHECKER','HOLD','Checker independente não atribuído; DR-F005 permanece aberto.')
    check('G5-HUMAN','HOLD','Aprovação humana formal ausente; vedada liberação GxP.')
    check('G0-RUNTIME','HOLD','Runtime autoritativo JV8-BL-001 ainda não comprovado.')

    return finish(findings,checks,traceability,comparisons,manifest_status)


def finish(findings:list[dict[str,Any]],checks:list[dict[str,Any]],traceability:list[dict[str,str]],comparisons:dict[str,Any],manifest_status:str) -> dict[str,Any]:
    checks_pass=sum(c['status']=='PASS' for c in checks)
    checks_fail=sum(c['status']=='FAIL' for c in checks)
    is_data_ok=manifest_status=='PASS' and not findings
    return {
       'package':'JARVIS-HYB-MVP-001','version':'0.1.0',
       'scope':'SYNTHETIC_OFFLINE_STRUCTURAL_ASSURANCE',
       'created_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
       'source_integrity_status':manifest_status,
       'documentary_structural_status':'PASS' if is_data_ok else ('HOLD' if manifest_status!='PASS' else 'FAIL'),
       'harness_authoritative_gate':'HOLD',
       'gxp_release_authorized':False,
       'quality_gates':{'G0':'HOLD','G1':'REVIEW_REQUIRED','G2':'REVIEW_REQUIRED','G3':'REVIEW_REQUIRED','G4':'HOLD','G5':'HOLD'},
       'execution':{'oq_planned':16,'oq_executed':0,'harness_tests_planned':22,'harness_tests_executed':0},
       'counts':{'checks_pass':checks_pass,'checks_fail':checks_fail,'findings':len(findings),'traces':len(traceability)},
       'checks':checks,'findings':sorted(findings,key=lambda f:(SEVERITY.index(f['severity']) if f['severity'] in SEVERITY else 4, f['id'],f['item'])),
       'traceability':traceability,'comparisons':comparisons,
       'limitations':['PASS is structural inspection only; not OQ/PQ/CSV/CSA, regulatory approval or independent Checker.',
                      'Hashes detect changed fixture bytes; do not prove original authenticity or chain of custody.',
                      'Only controlled synthetic sources; source data not independently validated.']
    }
