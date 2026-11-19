from scripts.preservation import check_preservation
import pytest
OLD=[dict(requirement_id='R-001',description='Latency must be <= 20 ms',status='EXPLICIT')]
def mapping(**kw): return [dict(requirement_id='R-001',classification='UNCHANGED',revised_location='line 1',preservation_status='PRESERVED',explanation='same meaning',**kw)]
def test_unchanged(): assert check_preservation(OLD,OLD,mapping())['passed']
def test_clarified():
 new=[dict(OLD[0],description='Response latency must be <= 20 ms')]; assert check_preservation(OLD,new,mapping(semantic_review=True))['passed']
def test_semantic_unverified():
 new=[dict(OLD[0],description='Usually latency <= 20 ms')]; assert check_preservation(OLD,new,mapping())['unverified']
def test_removed(): assert check_preservation(OLD,[],mapping())['failed']
def test_numeric_weakened(): assert check_preservation(OLD,[dict(OLD[0],description='Latency <= 200 ms')],mapping())['failed']
def test_default_promoted():
 assert check_preservation([dict(OLD[0],status='PROPOSED_DEFAULT')],OLD,mapping())['failed']
def test_contradiction(): assert check_preservation(OLD,[dict(OLD[0],contradiction_unresolved=True)],mapping())['failed']
def test_decision_hidden(): assert check_preservation([dict(OLD[0],status='DECISION_REQUIRED')],OLD,mapping())['failed']
def test_authorized_removal():
 m=mapping(authorization='user approved removal'); m[0]['classification']='REMOVED_WITH_AUTHORIZATION'; assert check_preservation(OLD,[],m)['passed']
