#!/usr/bin/env python3
"""Validate existing judgments; never generate scores from source instructions."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from decimal import Decimal
from jsonschema import Draft202012Validator, FormatChecker
ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = dict(zip(['clarity','completeness','decomposition','interface_contracts','implementability','testability','reproducibility','reliability','observability','agent_executability'], [10,10,10,15,10,15,10,5,5,10]))
DEFAULT_POLICY = dict(overall_min=90, interface_min=4, testability_min=4, reproducibility_min=4)
ASSIGNMENTS = [('A','C'),('A','B'),('A','C'),('B','A'),('A','B'),('B','C'),('B','C'),('B','A'),('C','B'),('C','A')]
def gates(report):
    scores={d['dimension_id']: d['score'] for d in report['dimensions']}
    p=report['policy']
    return dict(overall=report['total_score']>=p['overall_min'], interface_contracts=scores['interface_contracts']>=p['interface_min'], testability=scores['testability']>=p['testability_min'], reproducibility=scores['reproducibility']>=p['reproducibility_min'], critical_blockers=not report['critical_blockers'], component_readiness=all(all(c[k]['status']=='SPECIFIED' and c[k]['value'] for k in ('owner','acceptance_criteria')) for c in report['components']))
def status(report, results):
    if not report['input']['source_usable'] or any(f['severity']=='CRITICAL' and not f['resolved'] and f['external_decision'] for f in report['findings']):
        return 'BLOCKED'
    return 'READY' if all(results.values()) else 'NEEDS_REVISION'
def walk(value):
    if isinstance(value,dict):
        yield value
        for v in value.values(): yield from walk(v)
    elif isinstance(value,list):
        for v in value: yield from walk(v)
def canonical_report_hash(report):
    payload={k:v for k,v in report.items() if k!='report_hash'}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()

def parse_requirement_matrix(source):
    marker='## 요구사항 → AC → task → verification 매핑'
    lines=source.splitlines()
    try: start=lines.index(marker)+1
    except ValueError: return []
    rows=[]
    for line in lines[start:]:
        if not line.startswith('|'):
            if rows: break
            continue
        cells=[part.strip() for part in line.strip().strip('|').split('|')]
        if len(cells)<4 or not re.match(r'^R-[0-9]{2}\b',cells[0]):
            continue
        values=[]
        for cell,pattern in zip(cells[:4],[r'R-[0-9]{2}',r'AC-[0-9]{2}',r'T-[0-9]{2}',r'V-[0-9]{2}']):
            values.append(re.findall(pattern,cell))
        rows.append({'requirement_id':values[0][0],'acceptance_ids':values[1],'task_ids':values[2],'verification_ids':values[3]})
    return rows

def validate_requirement_map(actual, expected):
    schema=json.loads((ROOT/'schemas/workflow-record.schema.json').read_text())['$defs']['requirement_map']
    errors=['schema '+str(list(e.path))+': '+e.message for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(actual)]
    if not isinstance(actual,list) or not isinstance(expected,list): return errors+['requirement map must be arrays']
    actual_ids=[x.get('requirement_id') for x in actual if isinstance(x,dict)]
    expected_ids=[x.get('requirement_id') for x in expected if isinstance(x,dict)]
    if len(actual_ids)!=len(set(actual_ids)): errors.append('duplicate requirement_id')
    if len(expected_ids)!=len(set(expected_ids)): errors.append('authoritative matrix has duplicate requirement_id')
    if actual_ids!=expected_ids: errors.append('requirement ID registry mismatch')
    if actual!=expected: errors.append('requirement map differs from authoritative matrix')
    return errors

def validate_spec_plan_crosswalk(spec_report,plan_report,crosswalk,spec_source,plan_source):
    errors=[]
    spec_ids=[item['requirement_id'] for item in spec_report['requirements']]
    plan_ids=[item['requirement_id'] for item in plan_report['requirements']]
    rows=crosswalk.get('mapping',[])
    mapped_ids=[item.get('spec_requirement_id') for item in rows]
    if len(mapped_ids)!=len(set(mapped_ids)): errors.append('duplicate Spec requirement mapping')
    if mapped_ids!=spec_ids: errors.append('crosswalk does not cover the Spec requirement registry in order')
    matrix=parse_requirement_matrix(plan_source)
    matrix_by_id={row['requirement_id']:row for row in matrix}
    plan_link_by_id={row['requirement_id']:row for row in plan_report['requirement_links']}
    for item in rows:
        spec_evidence=item.get('spec_evidence',{})
        spec_quotes=spec_evidence.get('quotes') or ([spec_evidence['quote']] if spec_evidence.get('quote') else [])
        if not spec_quotes or any(quote not in spec_source for quote in spec_quotes): errors.append(f"Spec quote invalid for {item.get('spec_requirement_id')}")
        if item.get('coverage') not in ('FULL','PARTIAL','UNMAPPED'): errors.append('unknown crosswalk coverage value')
        links=item.get('plan_links',[])
        link_ids=[link.get('plan_requirement_id') for link in links]
        if len(link_ids)!=len(set(link_ids)): errors.append(f"duplicate Plan link for {item.get('spec_requirement_id')}")
        for link in links:
            rid=link.get('plan_requirement_id')
            expected=matrix_by_id.get(rid)
            if expected is None or plan_link_by_id.get(rid)!=expected: errors.append(f"dangling Plan requirement link {rid}")
            evidence=link.get('source_evidence',{})
            if not evidence.get('quote') or evidence['quote'] not in plan_source: errors.append(f"Plan quote invalid for {rid}")
            if evidence.get('input_sha256')!=plan_report['input_hash']: errors.append(f"Plan evidence hash mismatch for {rid}")
            for key in ('acceptance_ids','task_ids','verification_ids'):
                if link.get(key)!=expected.get(key) if expected else True: errors.append(f"Plan trace links mismatch for {rid}")
        if item.get('coverage')=='FULL' and not links: errors.append(f"FULL Spec requirement has no Plan links: {item.get('spec_requirement_id')}")
        if item.get('coverage') in ('PARTIAL','UNMAPPED') and not item.get('uncovered_clause'): errors.append(f"uncovered Spec requirement lacks explanation: {item.get('spec_requirement_id')}")
    unmapped=[item.get('spec_requirement_id') for item in rows if item.get('coverage')!='FULL']
    computed='FULL' if not errors and not unmapped and len(rows)==len(spec_ids) else 'PARTIAL'
    expected_gate='READY' if computed=='FULL' else 'BLOCKED'
    if crosswalk.get('overall_coverage')!=computed: errors.append('crosswalk overall coverage mismatch')
    if crosswalk.get('gate_result')!=expected_gate: errors.append('crosswalk gate result mismatch')
    if crosswalk.get('unmapped_spec_requirement_ids')!=unmapped: errors.append('crosswalk unmapped requirement registry mismatch')
    return {'errors':errors,'overall_coverage':computed,'gate_result':expected_gate,'unmapped_spec_requirement_ids':unmapped}

def validate_approval_record(record,current_hashes,expected_scope,plan_ready,execution_state,evidence_rows=None,approval_file_hash=None,workflow_id=None):
    schema=json.loads((ROOT/'schemas/workflow-record.schema.json').read_text())['$defs']['approval_record']
    errors=['schema '+str(list(e.path))+': '+e.message for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(record)]
    if errors: return errors
    status_value=record['status']
    nullable_fields=['approval_id','scope','spec_hash','plan_hash','input_hash','approver_role','decision_at','evidence_id','supersedes_approval_id','invalidation_reason']
    executing=execution_state in ('RUNNING','CHECKPOINTED','COMPLETE')
    if status_value=='NOT_REQUESTED' and any(record[k] is not None for k in nullable_fields): errors.append('NOT_REQUESTED must have null approval fields')
    if status_value=='PENDING':
        if not plan_ready: errors.append('PENDING requires Plan Gate READY')
        if record['scope']!=expected_scope or any(record[k]!=current_hashes[k] for k in ('spec_hash','plan_hash','input_hash')): errors.append('PENDING approval hash/scope mismatch')
        if any(record[k] is not None for k in ('approval_id','approver_role','decision_at','evidence_id','supersedes_approval_id','invalidation_reason')): errors.append('PENDING has decision-only fields')
    if status_value in ('APPROVED','DECLINED'):
        if record['scope']!=expected_scope or any(record[k]!=current_hashes[k] for k in ('spec_hash','plan_hash','input_hash')): errors.append('approval hash/scope mismatch')
        if not all(record[k] is not None for k in ('approval_id','approver_role','decision_at','evidence_id')): errors.append('decided approval fields missing')
        if record['approver_role']!='USER' or record['invalidation_reason'] is not None: errors.append('invalid decision metadata')
        if evidence_rows is None:
            errors.append('approval evidence report unavailable')
        else:
            matches=[e for e in evidence_rows if e['evidence_id']==record['evidence_id']]
            expected_path=f'.sdd-local/runs/{workflow_id}/approval-record.json' if workflow_id else None
            if len(matches)!=1 or matches[0]['kind']!='MANUAL' or matches[0]['relative_path']!=expected_path or matches[0]['sha256']!=approval_file_hash or matches[0]['result']!='PASS': errors.append('approval evidence reference/hash mismatch')
    if status_value=='INVALIDATED':
        if record['invalidation_reason'] is None or record['approval_id'] is None or record['supersedes_approval_id'] is None: errors.append('INVALIDATED event linkage missing')
        if not all(record[k] is not None for k in ('scope','spec_hash','plan_hash','input_hash','approver_role','decision_at','evidence_id')): errors.append('INVALIDATED must preserve prior approval values')
    if executing and status_value!='APPROVED': errors.append('execution requires APPROVED record')
    if executing and not plan_ready: errors.append('execution requires Plan Gate READY')
    return errors

def validate_workflow_record(record,expected_matrix,gate_reports=None,approval_file_hash=None,previous_record=None,crosswalk=None,spec_report=None,plan_assessment=None,spec_source=None,plan_source=None):
    schema=json.loads((ROOT/'schemas/workflow-record.schema.json').read_text())
    errors=['schema '+str(list(e.path))+': '+e.message for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(record)]
    if errors: return errors
    if record['storage']['relative_path']!=f".sdd-local/runs/{record['workflow_id']}/": errors.append('storage path must match workflow_id')
    errors.extend(validate_requirement_map(record['requirement_map'],expected_matrix))
    if crosswalk is not None:
        if spec_report is None or plan_assessment is None or spec_source is None or plan_source is None: errors.append('crosswalk provenance inputs missing')
        else:
            cross=validate_spec_plan_crosswalk(spec_report, plan_assessment, crosswalk, spec_source, plan_source)
            errors.extend(cross['errors'])
            if cross['gate_result']=='BLOCKED' and record['gate_state_map']['PLAN_ASSESSMENT']['status']!='BLOCKED': errors.append('Plan Gate must be BLOCKED for incomplete Spec traceability')
            if cross['gate_result']=='READY' and record['gate_state_map']['PLAN_ASSESSMENT']['status']!='READY': errors.append('Plan Gate must be READY for complete Spec traceability')
    errors.extend(validate_retry_counters(record['retry_counters']))
    refs={(x['gate_name'],x['report_id']):x for x in record['gate_report_refs']}
    if len(refs)!=len(record['gate_report_refs']): errors.append('duplicate gate/report reference')
    gate_reports=gate_reports or []
    plan_gate_report=None
    for report in gate_reports:
        errors.extend(validate_gate_report(report,record))
        gate_name=report['gate_name']; state=record['gate_state_map'][gate_name]
        ref=refs.get((gate_name,report['report_id']))
        if ref is None or ref['report_hash']!=report['report_hash'] or ref['status']!=report['status']: errors.append('gate report reference missing or mismatched')
        if state['report_id']!=report['report_id'] or state['status']!=report['status'] or state['input_hash']!=report['input_hash']: errors.append('gate state does not match report')
        if gate_name=='PLAN_ASSESSMENT': plan_gate_report=report
    if record['sandbox']['status']=='VERIFIED':
        probes=record['sandbox']['probes']
        by_kind={p['kind']:p for p in probes if p['attempted']}
        if set(by_kind)!={'OUT_OF_SCOPE_WRITE','SCOPED_OUTPUT'}: errors.append('VERIFIED sandbox requires both probes')
        else:
            denied=by_kind['OUT_OF_SCOPE_WRITE']; allowed=by_kind['SCOPED_OUTPUT']
            if denied['expected_result']!='BLOCKED' or denied['observed_result']!='BLOCKED' or denied['exit_code']==0 or not denied['evidence_id']: errors.append('sandbox deny probe evidence invalid')
            if allowed['expected_result']!='SUCCESS' or allowed['observed_result']!='SUCCESS' or allowed['exit_code']!=0 or not allowed['evidence_id']: errors.append('sandbox scoped-output probe evidence invalid')
        if not record['sandbox']['policy_hash'] or not record['sandbox']['profile_hash']: errors.append('VERIFIED sandbox hashes missing')
    for gate_name,state in record['gate_state_map'].items():
        if state['status']=='NOT_RUN' and state['attempt']!=0: errors.append(f'{gate_name} NOT_RUN attempt must be zero')
        if state['status']!='NOT_RUN' and state['attempt']<1: errors.append(f'{gate_name} run attempt must be positive')
    plan_ready=record['gate_state_map']['PLAN_ASSESSMENT']['status']=='READY'
    current={'spec_hash':record['spec_hash'],'plan_hash':record['plan_hash'],'input_hash':record['plan_hash']}
    evidence=plan_gate_report.get('evidence',[]) if plan_gate_report else None
    if record['approval_record']['status'] in ('APPROVED','DECLINED') and plan_gate_report is None: errors.append('decided approval requires a Plan Gate report')
    if record['approval_record']['status']=='INVALIDATED' and record['supersedes_workflow_id'] is None: errors.append('invalidated approval requires a superseding workflow')
    errors.extend(validate_approval_record(record['approval_record'],current,'SDD_V02_IMPLEMENTATION_RELEASE',plan_ready,record['execution_state'],evidence,approval_file_hash,record['workflow_id']))
    if previous_record is not None:
        old_hashes={'spec_hash':previous_record['spec_hash'],'plan_hash':previous_record['plan_hash'],'input_hash':previous_record['plan_hash']}
        errors.extend(validate_approval_invalidation(old_hashes,current,previous_record['approval_record'],record['approval_record'],previous_record['workflow_id'],record['workflow_id'],'SDD_V02_IMPLEMENTATION_RELEASE','SDD_V02_IMPLEMENTATION_RELEASE'))
        if record['supersedes_workflow_id']!=previous_record['workflow_id']: errors.append('supersedes_workflow_id must match previous workflow')
    if record['execution_state'] in ('RUNNING','CHECKPOINTED','COMPLETE') and record['sandbox']['status']!='VERIFIED': errors.append('execution requires VERIFIED sandbox')
    text=json.dumps(record,ensure_ascii=False)
    if re.search(r'/(?:Users|home)/',text): errors.append('privacy violation: absolute home path')
    return errors

def safe_relative_path(value):
    if not isinstance(value,str) or not value or "\\" in value: return False
    path=PurePosixPath(value)
    return not path.is_absolute() and all(part not in ("..","") for part in path.parts)

def validate_tool_trace(trace):
    schema=json.loads((ROOT/'schemas/tool-trace.schema.json').read_text())
    errors=['schema '+str(list(e.path))+': '+e.message for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(trace)]
    if errors: return errors
    if not safe_relative_path(trace['relative_cwd']): errors.append('trace cwd must be safe and relative')
    if trace['ended_at']<trace['started_at']: errors.append('trace end precedes start')
    if len(trace['artifact_hashes'])!=len(set(trace['artifact_hashes'])): errors.append('duplicate artifact hash')
    text=json.dumps(trace,ensure_ascii=False)
    if re.search(r'/(?:Users|home)/',text): errors.append('privacy violation: absolute home path')
    return errors

def validate_gate_report(report,workflow_record=None,source=None):
    schema=json.loads((ROOT/'schemas/gate-report.schema.json').read_text())
    errors=['schema '+str(list(e.path))+': '+e.message for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(report)]
    if not report.get('requirement_links'):
        errors.append('requirement_links must be non-empty for every gate')
    if errors: return errors
    if canonical_report_hash(report)!=report['report_hash']: errors.append('report hash mismatch')
    if report['status']=='READY' and report['gate_name']!='PLAN_ASSESSMENT': errors.append('READY is only valid for PLAN_ASSESSMENT')
    if source is not None and hashlib.sha256(source.encode('utf-8')).hexdigest()!=report['input_hash']: errors.append('source hash mismatch')
    evidence_id_list=[e['evidence_id'] for e in report['evidence']]
    evidence_ids=set(evidence_id_list)
    if len(evidence_ids)!=len(evidence_id_list): errors.append('duplicate evidence_id')
    if any(not safe_relative_path(e['relative_path']) for e in report['evidence']): errors.append('evidence path must be safe and relative')
    for row in report['checklist']:
        if not set(row['evidence_ids'])<=evidence_ids: errors.append('checklist has dangling evidence ID')
        if row['status']=='N_A_WITH_RATIONALE' and not row['rationale']: errors.append('N/A checklist requires rationale')
        if row['status']=='N_A_WITH_RATIONALE' and not row['evidence_ids']: errors.append('N/A checklist requires evidence')
    for row in report['findings']:
        if not set(row['evidence_ids'])<=evidence_ids: errors.append('finding has dangling evidence ID')
        if report['status'] in ('READY','PASS') and row['severity']=='CRITICAL' and row['disposition']=='OPEN': errors.append('open critical finding blocks READY/PASS')
    for row in report['errors']:
        if not set(row['evidence_ids'])<=evidence_ids: errors.append('error has dangling evidence ID')
    for evidence in report['evidence']:
        if evidence['result']=='N_A_WITH_RATIONALE' and not any(evidence['evidence_id'] in c['evidence_ids'] and c['status']=='N_A_WITH_RATIONALE' and c['rationale'] for c in report['checklist']): errors.append('N/A evidence lacks a rationale checklist row')
    if workflow_record is not None:
        if report['workflow_id']!=workflow_record['workflow_id']: errors.append('workflow ID mismatch')
        gate_name=report['gate_name']
        if gate_name=='SPECIFICATION_ASSESSMENT' and report['input_hash']!=workflow_record['spec_hash']: errors.append('Spec Gate input hash mismatch')
        elif gate_name=='PLAN_ASSESSMENT' and report['input_hash']!=workflow_record['plan_hash']: errors.append('Plan Gate input hash mismatch')
        elif gate_name not in ('SPECIFICATION_ASSESSMENT','PLAN_ASSESSMENT'):
            gate_input=workflow_record['gate_state_map'][gate_name]['input_hash']
            if gate_input is None or report['input_hash']!=gate_input: errors.append(f'{gate_name} input hash differs from its gate state')
            if gate_name in ('INDEPENDENT_VERIFICATION','RELEASE_READINESS'):
                freeze=next((cp for cp in workflow_record['checkpoints'] if cp['task_id']=='T-09' and cp['state']=='COMPLETE'),None)
                if freeze is None or report['input_hash'] not in freeze['artifact_hashes']: errors.append(f'{gate_name} input hash is not bound to the T-09 frozen candidate')
                peer='RELEASE_READINESS' if gate_name=='INDEPENDENT_VERIFICATION' else 'INDEPENDENT_VERIFICATION'
                peer_hash=workflow_record['gate_state_map'][peer]['input_hash']
                if peer_hash is not None and peer_hash!=report['input_hash']: errors.append('Independent Verification and Release Readiness candidate hashes differ')
        if report['status']=='NOT_REQUIRED' and (report['gate_name']!='RELEASE_READINESS' or workflow_record['release_in_scope']): errors.append('NOT_REQUIRED only allowed for out-of-scope release')
        if report['gate_name']=='SPECIFICATION_ASSESSMENT':
            if any(row not in workflow_record['requirement_map'] for row in report['requirement_links']): errors.append('Spec Gate requirement links must be exact rows from workflow requirement_map')
        elif report['requirement_links']!=workflow_record['requirement_map']:
            errors.append('gate requirement map mismatch')
        if report['gate_name']=='AGENT_EXECUTION' and report['status']=='PASS':
            if workflow_record['sandbox']['status']!='VERIFIED': errors.append('Execution PASS requires VERIFIED sandbox')
            probe_ids={p['evidence_id'] for p in workflow_record['sandbox']['probes'] if p['attempted']}
            if len(probe_ids)!=2 or not probe_ids<=evidence_ids: errors.append('Execution PASS requires both sandbox probe evidence rows')
        if report['gate_name']=='RELEASE_READINESS' and report['status']=='PASS':
            checks={c['check_id']:c for c in report['checklist']}
            for check_id in ('SECURITY','ROLLBACK','OPERATIONS'):
                if check_id not in checks or checks[check_id]['status']!='PASS' or not checks[check_id]['evidence_ids']: errors.append(f'Release PASS requires {check_id} evidence')
            slo=checks.get('SLO')
            if slo is None or slo['status'] not in ('PASS','N_A_WITH_RATIONALE') or not slo['evidence_ids']: errors.append('Release PASS requires SLO evidence or evidence-backed N/A')
    text=json.dumps(report,ensure_ascii=False)
    if re.search(r'/(?:Users|home)/',text): errors.append('privacy violation: absolute home path')
    return errors

def validate_retry_counters(counters,previous=None):
    errors=[]
    limits={'refine_reassess_attempt':5,'whole_prompt_fallback_count':1}
    for key,maximum in limits.items():
        value=counters.get(key)
        if type(value) is not int or value<0 or value>maximum: errors.append(f'{key} exceeds its bound or has wrong type')
    if type(counters.get('prompt_version')) is not int or counters['prompt_version']<1: errors.append('prompt_version must be a positive integer')
    if type(counters.get('execution_attempt')) is not int or counters['execution_attempt']<0: errors.append('execution_attempt must be a nonnegative integer')
    if previous is not None:
        for key in ('refine_reassess_attempt','whole_prompt_fallback_count','execution_attempt'):
            if counters.get(key,0)<previous.get(key,0) or counters.get(key,0)>previous.get(key,0)+1: errors.append(f'{key} must advance by at most one')
        if counters.get('prompt_version',1)<previous.get('prompt_version',1): errors.append('prompt_version cannot decrease')
        if counters.get('prompt_version',1)>previous.get('prompt_version',1)+1: errors.append('prompt_version cannot skip a version')
    return errors

def validate_approval_invalidation(previous_hashes,current_hashes,previous_approval,current_approval,previous_workflow_id,current_workflow_id,previous_scope,current_scope):
    changed=[key for key in ('spec_hash','plan_hash','input_hash') if previous_hashes.get(key)!=current_hashes.get(key)]
    if previous_scope!=current_scope: changed.append('scope')
    if not changed: return []
    errors=[]
    if current_workflow_id==previous_workflow_id: errors.append('hash/scope change requires a new workflow ID')
    if current_approval.get('status')!='INVALIDATED': errors.append('hash/scope change requires INVALIDATED approval record')
    expected_reason={'spec_hash':'SPEC_HASH_CHANGED','plan_hash':'PLAN_HASH_CHANGED','input_hash':'INPUT_HASH_CHANGED','scope':'SCOPE_CHANGED'}[changed[0]]
    if current_approval.get('invalidation_reason')!=expected_reason: errors.append('approval invalidation reason mismatch')
    if current_approval.get('supersedes_approval_id')!=previous_approval.get('approval_id'): errors.append('approval invalidation must reference prior approval')
    if current_approval.get('approval_id')==previous_approval.get('approval_id'): errors.append('invalidation event requires a new approval ID')
    return errors

ALLOWED_TRANSITIONS={
 'NOT_RUN':{'IN_PROGRESS'},
 'IN_PROGRESS':{'NEEDS_REVISION','READY','PASS','BLOCKED','FAIL'},
 'NEEDS_REVISION':{'IN_PROGRESS','BLOCKED','FAIL'},
 'READY':set(),'PASS':set(),'BLOCKED':set(),'FAIL':set(),'NOT_REQUIRED':set()
}
def validate_gate_transition(gate_name,previous_status,next_status,release_in_scope=True,previous_report_id=None,next_report_id=None,supersedes_report_id=None):
    allowed=set(ALLOWED_TRANSITIONS.get(previous_status,set()))
    if gate_name=='RELEASE_READINESS' and not release_in_scope and previous_status=='IN_PROGRESS': allowed.add('NOT_REQUIRED')
    if gate_name!='RELEASE_READINESS' or release_in_scope: allowed.discard('NOT_REQUIRED')
    if previous_status in {'READY','PASS','BLOCKED','FAIL','NOT_REQUIRED'} and next_status=='IN_PROGRESS':
        new_attempt=(previous_report_id and next_report_id and next_report_id!=previous_report_id and supersedes_report_id==previous_report_id)
        if new_attempt: return []
    return [] if next_status in allowed else [f'invalid gate transition {previous_status}->{next_status}']

def downstream_gates_invalidated(changed_input):
    return {
      'specification':{'PLAN_ASSESSMENT','AGENT_EXECUTION','INDEPENDENT_VERIFICATION','RELEASE_READINESS'},
      'plan':{'PLAN_ASSESSMENT','AGENT_EXECUTION','INDEPENDENT_VERIFICATION','RELEASE_READINESS'},
      'package':{'INDEPENDENT_VERIFICATION','RELEASE_READINESS'}
    }.get(changed_input,set())

def validate_downstream_invalidation(gate_state_map,changed_input):
    errors=[]
    for gate_name in downstream_gates_invalidated(changed_input):
        state=gate_state_map.get(gate_name,{})
        if state.get('status')!='NOT_RUN' and not state.get('superseded_by_report_id'):
            errors.append(f'{gate_name} was not invalidated after {changed_input} input change')
    return errors

def validate(report, source=None):
    errors=[]; unverified=[]
    schema=json.loads((ROOT/'schemas/assessment.schema.json').read_text())
    for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(report): errors.append('schema '+str(list(e.path))+': '+e.message)
    if errors: return dict(passed=[],failed=errors,unverified=['semantic checks skipped: schema invalid'])
    def check(condition,message):
        if not condition: errors.append(message)
    dims=report['dimensions']; check([d['dimension_id'] for d in dims]==list(DIMENSIONS),'dimension uniqueness/order')
    for d in dims:
        check(d['weight']==DIMENSIONS[d['dimension_id']], 'incorrect dimension weight')
        check(Decimal(str(d['weighted_score']))==Decimal(d['weight'])*d['score']/5,'weighted arithmetic')
        check(bool(d['evidence']) or bool(d['evidence_gaps']),'missing dimension evidence')
        for cap in d['score_caps']: check(d['score']<=cap['maximum'],'score cap exceeded')
    check(sum(d['weight'] for d in dims)==100,'weight sum')
    check(Decimal(str(report['total_score']))==sum(Decimal(str(d['weighted_score'])) for d in dims),'total arithmetic')
    check(canonical_report_hash(report)==report['report_hash'],'canonical report hash')
    ids={}
    for collection,key in [('requirements','requirement_id'),('components','component_id'),('findings','finding_id'),('integration_gaps','gap_id'),('recommendations','recommendation_id')]:
        values=[x[key] for x in report[collection]]; check(len(values)==len(set(values)),'duplicate '+key); ids[key]=set(values)
    mapping={'related_component_ids':'component_id','component_ids':'component_id','requirement_ids':'requirement_id','dependencies':'requirement_id','acceptance_criteria_ids':'requirement_id','finding_ids':'finding_id','remaining_finding_ids':'finding_id'}
    for item in walk(report):
        for key,target in mapping.items():
            if key in item and isinstance(item[key],list): check(set(item[key])<=ids[target], 'dangling '+key)
        if {'quote','location','gap'}<=item.keys():
            check(bool(item['quote']) or bool(item['gap']),'missing evidence quote or gap')
            if source is not None and item['quote']: check(item['quote'] in source,'source quote mismatch')
        if {'status','value','reason','evidence'}<=item.keys():
            if item['status']=='NOT_APPLICABLE': check(bool(item['reason']),'non-applicability reason missing')
            if item['status']=='SPECIFIED': check(bool(item['value']) and bool(item['evidence']),'specified contract lacks evidence')
    if report['gate_name']=='PLAN_ASSESSMENT':
        check(report['plan_hash']==report['input_hash'],'plan hash must equal exact input hash')
        if source is not None:
            expected_matrix=parse_requirement_matrix(source)
            check(bool(expected_matrix),'authoritative requirement matrix missing from source')
            if expected_matrix:
                check(not validate_requirement_map(report['requirement_links'],expected_matrix),'requirement_links differ from authoritative source matrix')
        requirement_ids=[r['requirement_id'] for r in report['requirements']]
        check([r['requirement_id'] for r in report['requirement_links']]==requirement_ids,'requirement_links do not cover report requirement registry')
    expected={f['finding_id'] for f in report['findings'] if f['severity']=='CRITICAL' and not f['resolved']}
    check(set(report['critical_blockers'])==expected and len(report['critical_blockers'])==len(expected),'critical blocker mismatch')
    scores={d['dimension_id']:d for d in dims}
    caps={}
    for c in report['components']:
        if c['critical'] and any(c[k]['status']=='UNSPECIFIED' for k in ('inputs','outputs')): caps['interface_contracts']=3
        if c['critical'] and any(c[k]['status']=='UNSPECIFIED' for k in ('owner','integration_boundaries')): caps['agent_executability']=3
    for key, maximum in caps.items(): check(scores[key]['score']<=maximum and bool(scores[key]['score_caps']),'mandatory contract cap')
    # Evidence gaps are explicit machine-checkable absence declarations.
    absence_caps={'NO_OBJECTIVE_ACCEPTANCE':('testability',3),'NO_REPRODUCIBILITY_CONTROLS':('reproducibility',3),'CRITICAL_CONTRADICTION':('clarity',2)}
    for token,(key,maximum) in absence_caps.items():
        if any(token in gap for d in dims for gap in d['evidence_gaps']): check(scores[key]['score']<=maximum and bool(scores[key]['score_caps']),'mandatory absence cap '+token)
    results=gates(report); check(results==report['acceptance_gates'],'gate mismatch'); check(report['status']==status(report,results),'status mismatch')
    meta=report['run_metadata']; check(set(meta['used_capabilities'])<=set(meta['available_capabilities']),'unavailable capability claimed')
    if meta['subagents_used']: check('subagents' in meta['used_capabilities'],'subagent capability claim')
    if meta['independent_review']:
        check(meta['subagents_used'],'independent review without actual subagents')
        reviewers=meta['reviewers']; check(len({r['reviewer_id'] for r in reviewers})==len(reviewers),'duplicate reviewer')
        for d,(primary,secondary) in zip(DIMENSIONS,ASSIGNMENTS):
            check(sum(d in r['primary'] and r['role']==primary for r in reviewers)==1 and sum(d in r['secondary'] and r['role']==secondary for r in reviewers)==1,'review coverage '+d)
    if report['reassessment']:
        check(report['reassessment']['policy']==report['policy'] and report['reassessment']['rubric_version']==report['rubric_version'],'reassessment policy drift')
        if report['status']=='READY': check(report['reassessment']['preservation_verified'],'unverified preservation')
    if source is None: unverified.append('source provenance: source unavailable')
    else:
        check(report['input']['source_hash']==hashlib.sha256(source.encode()).hexdigest(),'source hash mismatch')
        check(bool(source.strip())==report['input']['source_usable'],'source usability mismatch')
    return dict(passed=['schema','arithmetic','gates','references','capabilities','caps'] if not errors else ['schema'],failed=errors,unverified=unverified)
def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--report',required=True,type=Path); parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    try:
        report=json.loads(args.report.read_text()); source=args.source.read_text() if args.source else None
    except json.JSONDecodeError as e:
        print(json.dumps(dict(passed=[],failed=['JSON parsing: '+str(e)],unverified=[]))); return 1
    except (OSError,UnicodeError) as e:
        print('input/output error: '+str(e),file=sys.stderr); return 2
    result=validate(report,source); print(json.dumps(result,sort_keys=True)); return 1 if result['failed'] else 0
if __name__=='__main__': sys.exit(main())
