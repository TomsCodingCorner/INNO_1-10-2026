"""Backend checks only. These tests DO NOT demonstrate n8n orchestration."""
import copy
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app import main

INTERNAL = {'X-Internal-Key': 'test-internal'}
REVIEWER = {'X-Reviewer-Key': 'test-reviewer'}

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DB_PATH', str(tmp_path / 'audit.db'))
    monkeypatch.setattr(main, 'IDENTITY_PATH', str(tmp_path / 'identity.db'))
    monkeypatch.setattr(main, 'DATABASE_URL', '')
    monkeypatch.setattr(main, 'IDENTITY_DATABASE_URL', '')
    monkeypatch.setattr(main, 'DB_DRIVER', 'sqlite')
    monkeypatch.setattr(main, 'REVIEWER_KEY', 'test-reviewer')
    monkeypatch.setattr(main, 'INTERNAL_KEY', 'test-internal')
    monkeypatch.setattr(main, 'DEMO_MODE', True)
    with TestClient(main.app) as value:
        yield value

@pytest.fixture
def application():
    return json.loads((ROOT / 'fixtures/01-low-risk.json').read_text())

def prepared(client, application):
    response = client.post('/prepare', json=application, headers=INTERNAL)
    assert response.status_code == 200
    data = response.json()
    assert data['valid'] is True
    return data

def chain(client, application, fairness=False):
    """Exercise individual backend endpoints; deliberately not an E2E claim."""
    prep = prepared(client, application)
    policy = client.get('/policy/household_support', headers=INTERNAL).json()
    headers = {**INTERNAL, **({'X-Demo-Scenario': 'fairness'} if fairness else {})}
    proposal = client.post('/ai/propose', json={'input':prep['aiInput'],'policy':policy}, headers=headers).json()
    assessment = client.post('/assess', json={'input':prep['aiInput'],'policy':policy,'proposal':proposal}, headers=INTERNAL).json()
    body = {'caseId':prep['caseId'],'token':prep['token'],'aiInput':prep['aiInput'],'policy':policy,'proposal':proposal,'assessment':assessment}
    response = client.post('/cases', json=body, headers=INTERNAL)
    assert response.status_code == 200, response.text
    return body, response.json()

@pytest.mark.parametrize('severity,count,fairness,status,score', [
    ('low',1,False,'pending_standard_review',0),
    ('high',2,False,'pending_priority_review',100),
    ('low',1,True,'pending_priority_review',0),
    ('low',2,False,'pending_priority_review',30),
])
def test_backend_scenarios(client, application, severity,count,fairness,status,score):
    application.update(severity=severity,problemCount=count)
    body,result = chain(client, application, fairness)
    assert result['status'] == status
    assert body['assessment']['riskScore'] == score
    if fairness:
        assert 'fairness:geslacht' in body['assessment']['flags']
    rows = client.get('/reviews', headers=REVIEWER).json()
    assert rows[0]['caseId'] == body['caseId']
    audit = client.get('/audit', headers=REVIEWER).json()
    assert [event['eventType'] for event in reversed(audit)] == ['application_prepared','ai_preparation','review_ready']
    serialized = json.dumps(audit)
    for value in [application['name'],application['address'],application['citizenId'],application['dateOfBirth']]:
        assert value not in serialized
    overview = client.get('/cases', headers=REVIEWER).json()
    assert overview['counts']['total'] == 1
    assert overview['cases'][0]['caseId'] == body['caseId']
    assert overview['cases'][0]['statusLabel'] in {'Wacht op beoordeling','Extra beoordeling nodig'}
    detail = client.get('/cases/' + body['caseId'], headers=REVIEWER).json()
    assert detail['aiInput'] == body['aiInput']
    assert detail['proposal'] == body['proposal']
    assert detail['humanDecision'] is None
    assert [item['eventType'] for item in detail['timeline']] == ['application_prepared','ai_preparation','review_ready']


def test_consent_failure_no_ai_call_backend_only(client, application):
    before = client.get('/metrics', headers=REVIEWER).json()['aiCalls']
    application['consentAI'] = False
    response = client.post('/prepare', json=application, headers=INTERNAL)
    assert response.json()['valid'] is False
    assert response.json()['errorCode'] == 'AI_CONSENT_REQUIRED'
    assert client.get('/metrics', headers=REVIEWER).json()['aiCalls'] == before
    assert client.get('/reviews', headers=REVIEWER).json() == []

@pytest.mark.parametrize('field,value', [('name','Secret Person'),('address','Secret Street'),('dateOfBirth','1999-01-01'),('citizenId','secret-id'),('token','secret-token')])
def test_ai_rejects_identifying_extra_fields(client, application, field,value):
    prep = prepared(client, application)
    assert set(prep['aiInput']) == {'ageGroup','requestType','severity','problemCount','limitations','existingSupport'}
    prep['aiInput'][field] = value
    policy = client.get('/policy/household_support', headers=INTERNAL).json()
    response = client.post('/ai/propose', json={'input':prep['aiInput'],'policy':policy}, headers=INTERNAL)
    assert response.status_code == 400
    assert value not in response.text
    assert client.get('/metrics',headers=REVIEWER).json()['aiCalls'] == 0

@pytest.mark.parametrize('change', [{'consentAI':'true'},{'severity':'urgent'},{'dateOfBirth':'2999-01-01'},{'problemCount':True},{'limitations':['Secret Person']},{'freeText':'secret'}])
def test_invalid_input_safe_message(client, application, change):
    application.update(change)
    response = client.post('/prepare', json=application, headers=INTERNAL)
    assert response.json()['valid'] is False
    assert response.json()['errorCode'] == 'INVALID_INPUT'
    assert application['name'] not in response.text


def test_unknown_policy_reference_causes_review(client, application):
    body,_ = chain(client, application)
    body['proposal']['policyReferences'] = ['NONEXISTENT']
    response = client.post('/assess', json={'input':body['aiInput'],'policy':body['policy'],'proposal':body['proposal']},headers=INTERNAL)
    value = response.json()
    assert value['requiresPriorityReview'] is True
    assert value['reasoningValid'] is False
    assert 'reasoning:invalid' in value['flags']


def test_decision_preserves_initial_audit_and_requires_auth(client, application):
    body,_ = chain(client, application)
    initial = client.get('/audit',headers=REVIEWER).json()[0]
    path = '/reviews/' + body['caseId'] + '/decision'
    decision = {'decision':'approved','reasoning':'Zelf beoordeeld op basis van aanvullende informatie.'}
    assert client.post(path,json=decision).status_code == 401
    assert client.post(path,json=decision,headers=REVIEWER).status_code == 200
    assert client.get('/reviews',headers=REVIEWER).json() == []
    overview = client.get('/cases', headers=REVIEWER).json()
    assert overview['counts']['completed'] == 1
    assert overview['cases'][0]['statusLabel'] == 'Toegekend door medewerker'
    detail = client.get('/cases/' + body['caseId'], headers=REVIEWER).json()
    assert detail['humanDecision']['decision'] == 'approved'
    events = client.get('/audit',headers=REVIEWER).json()
    assert events[0]['eventType'] == 'human_decision'
    assert events[1] == initial
    assert client.post(path,json=decision,headers=REVIEWER).status_code == 409


def test_case_save_is_idempotent_and_conflicting_retry_rejected(client, application):
    body,_ = chain(client, application)
    assert client.post('/cases',json=body,headers=INTERNAL).status_code == 200
    assert len(client.get('/audit',headers=REVIEWER).json()) == 3
    changed = copy.deepcopy(body)
    changed['proposal']['proposal'] += ' Extra tekst.'
    assert client.post('/cases',json=changed,headers=INTERNAL).status_code == 409


def test_internal_and_reviewer_endpoints_require_separate_keys(client, application):
    assert client.post('/prepare',json=application).status_code == 401
    assert client.post('/prepare',json=application,headers=REVIEWER).status_code == 401
    for path in ['/reviews','/audit','/metrics','/cases']:
        assert client.get(path).status_code == 401
        assert client.get(path,headers=INTERNAL).status_code == 401


def test_database_survives_application_restart(client, application):
    body,_ = chain(client, application)
    # Same persistent SQLite files, new application lifespan. Not a Docker restart test.
    with TestClient(main.app) as restarted:
        assert restarted.get('/reviews',headers=REVIEWER).json()[0]['caseId'] == body['caseId']
