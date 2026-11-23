import json,subprocess,sys
from pathlib import Path
import pytest
from scripts.validate_assessment import validate
ROOT=Path(__file__).resolve().parents[1]
def test_valid(report,source): assert not validate(report,source)['failed']
@pytest.mark.parametrize('mutation',[lambda r:r.pop('policy'),lambda r:r.update(extra=1),lambda r:r['dimensions'][0].update(score=6),lambda r:r['dimensions'][0].update(score=1.5),lambda r:r['dimensions'][0].update(dimension_id='unknown')])
def test_schema_rejections(report,mutation):
 mutation(report); assert validate(report)['failed']
def test_source_id_rejects_path_traversal(report):
 report['input']['source_id']='../private'; assert validate(report)['failed']
def test_repeat(report,source): assert validate(report,source)==validate(report,source)
def test_invalid_sample():
 r=json.loads((ROOT/'tests/fixtures/reports/invalid-ready.json').read_text()); assert validate(r)['failed']
def test_cli_io():
 p=subprocess.run([sys.executable,str(ROOT/'scripts/validate_assessment.py'),'--report','nonexistent'],capture_output=True); assert p.returncode==2
def test_cli_usage():
 p=subprocess.run([sys.executable,str(ROOT/'scripts/validate_assessment.py')],capture_output=True); assert p.returncode==2
def test_bad_json(tmp_path):
 f=tmp_path/'bad.json'; f.write_text('{'); p=subprocess.run([sys.executable,str(ROOT/'scripts/validate_assessment.py'),'--report',str(f)],capture_output=True); assert p.returncode==1
@pytest.mark.parametrize('name',['poor','adequate','excellent','contradictory','missing-contracts','injection-attempt'])
def test_calibration_reports(name):
 r=json.loads((ROOT/f'tests/fixtures/reports/{name}.json').read_text()); assert not validate(r)['failed']
 assert (r['status']=='READY')==(name=='excellent')
def test_cli_preserves_crlf_source_bytes_for_hash(tmp_path):
 import hashlib
 from scripts.validate_assessment import canonical_report_hash
 src_text=(ROOT/'tests/fixtures/excellent-prompt.md').read_text(encoding='utf-8').replace('\n','\r\n')
 src_file=tmp_path/'crlf-source.md'; src_file.write_bytes(src_text.encode('utf-8'))
 rep=json.loads((ROOT/'tests/fixtures/reports/excellent.json').read_text(encoding='utf-8'))
 rep['input']['source_hash']=hashlib.sha256(src_text.encode('utf-8')).hexdigest()
 rep['input_hash']=rep['input']['source_hash']
 rep['report_hash']=canonical_report_hash(rep)
 rep_file=tmp_path/'crlf-report.json'; rep_file.write_text(json.dumps(rep),encoding='utf-8')
 p=subprocess.run([sys.executable,str(ROOT/'scripts/validate_assessment.py'),'--report',str(rep_file),'--source',str(src_file)],capture_output=True,text=True)
 assert p.returncode==0, p.stdout+p.stderr
