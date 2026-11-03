import pytest
from scripts.validate_assessment import validate
@pytest.mark.parametrize('mutation',[lambda r:r['dimensions'][0].update(weight=9),lambda r:r['dimensions'][0].update(weighted_score=9.5),lambda r:r.update(total_score=99),lambda r:r['dimensions'][1].update(dimension_id='clarity'),lambda r:r['dimensions'][0].update(score_caps=[dict(maximum=3,reason='critical ambiguity')])])
def test_arithmetic_and_caps(report,mutation):
 mutation(report); assert validate(report)['failed']
def test_declared_absence_cap(report):
 report['dimensions'][5]['evidence_gaps']=['NO_OBJECTIVE_ACCEPTANCE']; assert validate(report)['failed']
def test_exact_total(report): assert report['total_score']==sum(d['weight']*d['score']/5 for d in report['dimensions'])
