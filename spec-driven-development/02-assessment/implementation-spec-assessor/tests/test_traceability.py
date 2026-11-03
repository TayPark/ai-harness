from scripts.validate_assessment import validate
import pytest
@pytest.mark.parametrize('mutation',[lambda r:r['requirements'].append(r['requirements'][0]),lambda r:r['requirements'][0].update(dependencies=['R-404']),lambda r:r.update(critical_blockers=['F-404']),lambda r:r['recommendations'].append(dict(recommendation_id='REC-1',finding_ids=['F-404'],mandatory=True,priority=1,change='fix',verification='test')),lambda r:r['run_metadata'].update(independent_review=True),lambda r:r['run_metadata'].update(used_capabilities=['network']),lambda r:r['dimensions'][0].update(evidence=[],evidence_gaps=[])])
def test_reference_rejections(report,mutation):
 mutation(report); assert validate(report)['failed']
def test_missing_source_unverified(report): assert validate(report)['unverified']==['source provenance: source unavailable']
def test_false_quote(report,source):
 report['dimensions'][0]['evidence'][0]['quote']='not in source'; assert validate(report,source)['failed']
def test_bad_hash(report,source):
 report['input']['source_hash']='bad'; assert validate(report,source)['failed']
def test_normalized_schema(report,source):
 import json,hashlib
 from pathlib import Path
 from jsonschema import Draft202012Validator
 schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/normalized-requirements.schema.json').read_text())
 contract=dict(status='UNSPECIFIED',value=None,reason='Absent',evidence=[])
 normalized=dict(source_id='example',source_hash=hashlib.sha256(source.encode()).hexdigest(),requirements=report['requirements'],components=report['components'],system_contract={k:contract for k in schema['properties']['system_contract']['properties']})
 assert not list(Draft202012Validator(schema).iter_errors(normalized))
 normalized['requirements'][0]['status']='CONFIRMED_DEFAULT'
 assert list(Draft202012Validator(schema).iter_errors(normalized))
def test_reviewer_coverage_claim(report):
 report['run_metadata'].update(available_capabilities=['subagents'],used_capabilities=['subagents'],subagents_used=True,independent_review=True,reviewers=[])
 assert any('review coverage' in e for e in validate(report)['failed'])
