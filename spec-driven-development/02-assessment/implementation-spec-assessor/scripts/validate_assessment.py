#!/usr/bin/env python3
"""Validate existing judgments; never generate scores from source instructions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from decimal import Decimal
from jsonschema import Draft202012Validator
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
def validate(report, source=None):
    errors=[]; unverified=[]
    schema=json.loads((ROOT/'schemas/assessment.schema.json').read_text())
    for e in Draft202012Validator(schema).iter_errors(report): errors.append('schema '+str(list(e.path))+': '+e.message)
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
