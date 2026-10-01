"""Local synthetic-data WMO demo. n8n performs all orchestration."""
import json
import os
import re
import secrets
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

import httpx
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, ValidationError, field_validator

DB_PATH = os.getenv('DB_PATH', '/data/audit.db')
IDENTITY_PATH = os.getenv('IDENTITY_PATH', '/data/identity.db')
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'
REVIEWER_KEY = os.getenv('REVIEWER_KEY', '')
INTERNAL_KEY = os.getenv('INTERNAL_KEY', '')
N8N_URL = os.getenv('N8N_WEBHOOK_URL', 'http://n8n:5678/webhook/wmo-aanvraag')
app = FastAPI(title='Zelfstandige Zorgagent — fictieve demo', version='1.0.0')

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class AIInput(StrictModel):
    ageGroup: Literal['under_18', '18_64', '65_74', '75_plus']
    requestType: Literal['household_support']
    severity: Literal['low', 'medium', 'high']
    problemCount: Annotated[StrictInt, Field(ge=1, le=10)]
    limitations: list[Literal['cleaning', 'laundry', 'shopping']]=Field(min_length=1,max_length=3)
    existingSupport: StrictBool

class Application(StrictModel):
    citizenId: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=200)
    dateOfBirth: date
    consentAI: StrictBool
    requestType: Literal['household_support']
    severity: Literal['low', 'medium', 'high']
    problemCount: Annotated[StrictInt, Field(ge=1, le=10)]
    limitations: list[Literal['cleaning', 'laundry', 'shopping']]=Field(min_length=1,max_length=3)
    existingSupport: StrictBool

    @field_validator('citizenId','name','address')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('Leeg veld')
        return value.strip()

    @field_validator('dateOfBirth')
    @classmethod
    def dob(cls, value):
        if value > date.today() or value < date(1900,1,1):
            raise ValueError('Geboortedatum buiten toegestaan bereik')
        return value

class Rule(StrictModel):
    id: str
    description: str

class Policy(StrictModel):
    policyVersion: str
    rules: list[Rule]

POLICY = Policy(policyVersion='demo-v1',rules=[
    Rule(id='DEMO-01',description='Een beperking bij schoonmaken kan aanleiding zijn voor nader onderzoek naar ondersteuning.'),
    Rule(id='DEMO-02',description='Hoge ernst of meerdere problemen vereist uitgebreide menselijke beoordeling.')])

class AIRequest(StrictModel):
    input: AIInput
    policy: Policy

class Proposal(StrictModel):
    proposal: str = Field(max_length=2000)
    reasoning: str = Field(max_length=4000)
    policyReferences: list[str]
    missingInformation: list[str]

class AssessmentRequest(StrictModel):
    input: AIInput
    policy: Policy
    # Missing proposal fields are assessed as invalid, rather than bypassing review.
    proposal: dict

class Assessment(StrictModel):
    riskScore: int
    flags: list[str]
    reasoningValid: bool
    requiresPriorityReview: bool
    status: Literal['pending_standard_review','pending_priority_review']

class SaveCase(StrictModel):
    caseId: str
    token: str
    aiInput: AIInput
    policy: Policy
    proposal: Proposal
    assessment: Assessment

class Decision(StrictModel):
    decision: Literal['approved','rejected','needs_information']
    reasoning: str = Field(min_length=5,max_length=2000)
    @field_validator('reasoning')
    @classmethod
    def nonblank(cls,v):
        if len(v.strip()) < 5: raise ValueError('Licht de beslissing toe')
        return v.strip()

class AuditRequest(StrictModel):
    eventType: Literal['validation_failed','technical_failure']
    errorCode: Literal['AI_CONSENT_REQUIRED','INVALID_INPUT','SERVICE_UNAVAILABLE']
    correlationId: str | None = Field(default=None, max_length=80)

STATUS_LABELS = {
    'pending_standard_review': 'Wacht op beoordeling',
    'pending_priority_review': 'Extra beoordeling nodig',
    'approved': 'Toegekend door medewerker',
    'rejected': 'Afgewezen door medewerker',
    'needs_information': 'Meer informatie nodig',
}
REQUEST_LABELS = {'household_support': 'Huishoudelijke hulp'}
SEVERITY_LABELS = {'low': 'Laag', 'medium': 'Gemiddeld', 'high': 'Hoog'}

def connect(path= None):
    path = path or DB_PATH
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(path,timeout=10)
    c.row_factory=sqlite3.Row
    return c

def initialize():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS cases(case_id TEXT PRIMARY KEY, token TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_events(id INTEGER PRIMARY KEY AUTOINCREMENT,case_id TEXT,event_type TEXT NOT NULL,created_at TEXT NOT NULL,data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS metrics(name TEXT PRIMARY KEY,value INTEGER NOT NULL);
        INSERT OR IGNORE INTO metrics VALUES('ai_calls',0);
        ''')
    with connect(IDENTITY_PATH) as c:
        c.execute('CREATE TABLE IF NOT EXISTS identities(token TEXT PRIMARY KEY,citizen_id TEXT NOT NULL)')

@app.on_event('startup')
def startup(): initialize()

def auth(supplied, expected):
    if not expected or not supplied or not secrets.compare_digest(supplied,expected):
        raise HTTPException(401,'Geen geldige toegangssleutel.')

def internal(x_internal_key: str | None=Header(default=None)):
    auth(x_internal_key,INTERNAL_KEY)

def reviewer(x_reviewer_key: str | None=Header(default=None)):
    auth(x_reviewer_key,REVIEWER_KEY)

def event(c,kind,data,case_id=None):
    c.execute('INSERT INTO audit_events(case_id,event_type,created_at,data) VALUES(?,?,?,?)',
              (case_id,kind,datetime.now(timezone.utc).isoformat(),json.dumps(data,ensure_ascii=False)))

def risk_label(score: int):
    if score >= 70: return 'Hoog risico'
    if score >= 30: return 'Verhoogd risico'
    return 'Laag risico'

def review_reasons(ai_input: dict, assessment: dict):
    reasons = []
    if ai_input.get('severity') == 'high':
        reasons.append('Ernst is hoog')
    if ai_input.get('problemCount', 0) >= 2:
        reasons.append('Meerdere problemen gemeld')
    if assessment.get('riskScore', 0) >= 70:
        reasons.append('Risicoscore is hoog')
    if assessment.get('flags'):
        reasons.append('Fairness- of onderbouwingsflag aanwezig')
    if not assessment.get('reasoningValid', True):
        reasons.append('Onderbouwing of beleidsreferentie is ongeldig')
    return reasons or ['Menselijke beoordeling blijft vereist voordat een beslissing definitief is']

def parse_payload(row):
    payload = json.loads(row['payload'])
    payload.setdefault('caseId', row['case_id'])
    payload.setdefault('token', row['token'])
    return payload

def case_events(c, case_id: str):
    rows = c.execute('SELECT * FROM audit_events WHERE case_id=? ORDER BY id ASC',(case_id,)).fetchall()
    return [{'id':r['id'],'caseId':r['case_id'],'eventType':r['event_type'],'createdAt':r['created_at'],'data':json.loads(r['data'])} for r in rows]

def human_decision_from(events):
    for item in reversed(events):
        if item['eventType'] == 'human_decision':
            return item['data']
    return None

def timeline_from(events):
    labels = {
        'application_prepared': 'Aanvraag voorbereid',
        'ai_preparation': 'AI-voorstel en controles vastgelegd',
        'review_ready': 'Klaargezet voor menselijke beoordeling',
        'human_decision': 'Menselijke beslissing geregistreerd',
    }
    return [{'time':e['createdAt'],'eventType':e['eventType'],'label':labels[e['eventType']],'details':e['data']}
            for e in events if e['eventType'] in labels]

def case_summary(row, events=None):
    payload = parse_payload(row)
    ai_input = payload['aiInput']
    assessment = payload['assessment']
    events = events or []
    submitted = events[0]['createdAt'] if events else None
    last_changed = events[-1]['createdAt'] if events else None
    decision = human_decision_from(events)
    return {
        'caseId': row['case_id'],
        'submittedAt': submitted,
        'lastChangedAt': last_changed,
        'requestType': ai_input['requestType'],
        'requestTypeLabel': REQUEST_LABELS.get(ai_input['requestType'], ai_input['requestType']),
        'severity': ai_input['severity'],
        'severityLabel': SEVERITY_LABELS.get(ai_input['severity'], ai_input['severity']),
        'riskScore': assessment['riskScore'],
        'riskLabel': risk_label(assessment['riskScore']),
        'flags': assessment['flags'],
        'status': row['status'],
        'statusLabel': STATUS_LABELS.get(row['status'], row['status']),
        'requiresPriorityReview': assessment['requiresPriorityReview'],
        'reviewReasons': review_reasons(ai_input, assessment),
        'humanDecision': decision,
    }

@app.exception_handler(RequestValidationError)
async def invalid_request(request,exc):
    # Do not echo rejected input (it may contain identity data).
    return JSONResponse(status_code=400,content={'errorCode':'INVALID_INPUT','message':'Controleer de verplichte velden en toegestane waarden.'})

@app.get('/health')
def health():
    with connect() as c: c.execute('SELECT 1')
    return {'status':'ok','demoMode':DEMO_MODE,'ai':'deterministic-stub-v1'}

@app.post('/prepare',dependencies=[Depends(internal)])
def prepare(payload: object=Body(...)):
    try: a=Application.model_validate(payload)
    except ValidationError:
        return {'valid':False,'errorCode':'INVALID_INPUT','message':'Controleer de verplichte velden en toegestane waarden.'}
    if not a.consentAI:
        return {'valid':False,'errorCode':'AI_CONSENT_REQUIRED','message':'Uw aanvraag is niet met AI verwerkt, omdat u hiervoor geen toestemming heeft gegeven.'}
    age=date.today().year-a.dateOfBirth.year-((date.today().month,date.today().day)<(a.dateOfBirth.month,a.dateOfBirth.day))
    group='under_18' if age<18 else '18_64' if age<65 else '65_74' if age<75 else '75_plus'
    ai=AIInput(ageGroup=group,**a.model_dump(include={'requestType','severity','problemCount','limitations','existingSupport'}))
    token=str(uuid4())
    with connect(IDENTITY_PATH) as c: c.execute('INSERT INTO identities VALUES(?,?)',(token,a.citizenId))
    return {'valid':True,'caseId':str(uuid4()),'token':token,'aiInput':ai.model_dump()}

@app.get('/policy/household_support',dependencies=[Depends(internal)])
def policy(): return POLICY

@app.post('/ai/propose',dependencies=[Depends(internal)])
def propose(data: AIRequest,x_demo_scenario: str | None=Header(default=None)):
    if data.policy != POLICY: raise HTTPException(400,'Onbekende demoversie van beleid')
    with connect() as c: c.execute("UPDATE metrics SET value=value+1 WHERE name='ai_calls'")
    labels={'cleaning':'schoonmaken','laundry':'wassen','shopping':'boodschappen'}
    reason='De aanvraag vermeldt beperkingen bij '+', '.join(labels[x] for x in data.input.limitations)+'.'
    if DEMO_MODE and x_demo_scenario=='fairness':
        reason+=' Het geslacht van de aanvrager is bepalend voor dit voorstel.'
    return Proposal(proposal='Laat een medewerker de ondersteuningsbehoefte beoordelen.',reasoning=reason,
                    policyReferences=['DEMO-01'],missingInformation=['Omvang van benodigde ondersteuning'])

FORBIDDEN=['religie','ras','nationaliteit','geslacht','moslim','christen','joods','huidskleur','man','vrouw']
LABELS={'cleaning':'schoonmaken','laundry':'wassen','shopping':'boodschappen'}
def strings(value):
    if isinstance(value,str): return [value]
    if isinstance(value,list): return [s for v in value for s in strings(v)]
    if isinstance(value,dict): return [s for v in value.values() for s in strings(v)]
    return []

def assess_value(data):
    text=' '.join(strings(data.proposal)).casefold()
    flags=['fairness:'+word for word in FORBIDDEN if re.search(r'\b'+re.escape(word)+r'\b',text)]
    valid=True
    try: p=Proposal.model_validate(data.proposal)
    except ValidationError: valid=False; p=None
    if p:
        valid=bool(p.proposal.strip() and p.reasoning.strip() and p.policyReferences)
        valid=valid and set(p.policyReferences).issubset({r.id for r in data.policy.rules})
        valid=valid and any(LABELS[x] in p.reasoning.casefold() for x in data.input.limitations)
    if not valid: flags.append('reasoning:invalid')
    risk=min(100,(70 if data.input.severity=='high' else 0)+(30 if data.input.problemCount>=2 else 0))
    priority=bool(data.input.severity=='high' or data.input.problemCount>=2 or risk>=70 or flags)
    return Assessment(riskScore=risk,flags=flags,reasoningValid=valid,requiresPriorityReview=priority,
                      status='pending_priority_review' if priority else 'pending_standard_review')

@app.post('/assess',dependencies=[Depends(internal)])
def assess(data: AssessmentRequest): return assess_value(data)

@app.post('/cases',dependencies=[Depends(internal)])
def save_case(data: SaveCase):
    recomputed=assess_value(AssessmentRequest(input=data.aiInput,policy=data.policy,proposal=data.proposal.model_dump()))
    if data.policy != POLICY or recomputed != data.assessment: raise HTTPException(400,'Inconsistente beoordeling')
    with connect(IDENTITY_PATH) as c:
        if not c.execute('SELECT 1 FROM identities WHERE token=?',(data.token,)).fetchone(): raise HTTPException(400,'Onbekend token')
    payload=data.model_dump()
    with connect() as c:
        existing=c.execute('SELECT payload,status FROM cases WHERE case_id=?',(data.caseId,)).fetchone()
        if existing:
            if json.loads(existing['payload']) != payload: raise HTTPException(409,'Dossier bestaat met andere inhoud')
            return {'caseId':data.caseId,'status':existing['status'],'aiInput':data.aiInput.model_dump(),'requiresPriorityReview':data.assessment.requiresPriorityReview}
        c.execute('INSERT INTO cases VALUES(?,?,?,?)',(data.caseId,data.token,data.assessment.status,json.dumps(payload)))
        ai_input = data.aiInput.model_dump()
        assessment = data.assessment.model_dump()
        event(c,'application_prepared',{'token':data.token,'aiInput':ai_input},data.caseId)
        event(c,'ai_preparation',{'token':data.token,'aiVersion':'deterministic-stub-v1','policyVersion':data.policy.policyVersion,
              'proposal':data.proposal.model_dump(),'assessment':assessment,'aiInput':ai_input},data.caseId)
        event(c,'review_ready',{'status':data.assessment.status,'statusLabel':STATUS_LABELS[data.assessment.status],
              'reasons':review_reasons(ai_input,assessment)},data.caseId)
    return {'caseId':data.caseId,'status':data.assessment.status,'aiInput':data.aiInput.model_dump(),'requiresPriorityReview':data.assessment.requiresPriorityReview}

@app.get('/cases',dependencies=[Depends(reviewer)])
def list_cases(q: str | None = Query(default=None, max_length=120),
               status: str | None = Query(default=None, max_length=40),
               priority: bool | None = Query(default=None)):
    with connect() as c:
        rows=c.execute('SELECT * FROM cases ORDER BY rowid DESC').fetchall()
        summaries=[]
        for row in rows:
            events = case_events(c,row['case_id'])
            item = case_summary(row,events)
            if q and q.casefold() not in item['caseId'].casefold(): continue
            if status and status != 'all' and item['status'] != status: continue
            if priority is not None and item['requiresPriorityReview'] is not priority: continue
            summaries.append(item)
    counts = {
        'total': len(summaries),
        'pending': sum(1 for item in summaries if item['status'].startswith('pending_')),
        'priority': sum(1 for item in summaries if item['requiresPriorityReview']),
        'completed': sum(1 for item in summaries if not item['status'].startswith('pending_')),
    }
    return {'cases': summaries, 'counts': counts, 'statusLabels': STATUS_LABELS}

@app.get('/cases/{case_id}',dependencies=[Depends(reviewer)])
def case_detail(case_id: str):
    with connect() as c:
        row=c.execute('SELECT * FROM cases WHERE case_id=?',(case_id,)).fetchone()
        if not row: raise HTTPException(404,'Dossier niet gevonden')
        events=case_events(c,case_id)
    payload=parse_payload(row)
    summary=case_summary(row,events)
    return {
        **summary,
        'token': payload['token'],
        'pseudonymousApplication': {
            'token': payload['token'],
            'requestType': payload['aiInput']['requestType'],
            'requestTypeLabel': summary['requestTypeLabel'],
            'severity': payload['aiInput']['severity'],
            'severityLabel': summary['severityLabel'],
            'problemCount': payload['aiInput']['problemCount'],
            'limitations': payload['aiInput']['limitations'],
            'existingSupport': payload['aiInput']['existingSupport'],
        },
        'aiInput': payload['aiInput'],
        'policy': payload['policy'],
        'proposal': payload['proposal'],
        'assessment': payload['assessment'],
        'timeline': timeline_from(events),
        'auditEvents': events,
    }

@app.get('/reviews',dependencies=[Depends(reviewer)])
def reviews():
    with connect() as c: rows=c.execute("SELECT * FROM cases WHERE status LIKE 'pending_%' ORDER BY rowid DESC").fetchall()
    result=[]
    for r in rows:
        p=json.loads(r['payload'])
        result.append({'caseId':r['case_id'],'token':r['token'],'status':r['status'],'aiInput':p['aiInput'],**p['proposal'],**{k:v for k,v in p['assessment'].items() if k!='status'}})
    return result

@app.post('/reviews/{case_id}/decision',dependencies=[Depends(reviewer)])
def decision(case_id: str,data: Decision):
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT status FROM cases WHERE case_id=?',(case_id,)).fetchone()
        if not row: raise HTTPException(404,'Dossier niet gevonden')
        if not row['status'].startswith('pending_'): raise HTTPException(409,'Dossier is al beoordeeld')
        c.execute('UPDATE cases SET status=? WHERE case_id=?',(data.decision,case_id))
        event(c,'human_decision',{'decision':data.decision,'reasoning':data.reasoning,'actor':'local-demo-reviewer'},case_id)
    return {'caseId':case_id,'status':data.decision}

@app.get('/audit',dependencies=[Depends(reviewer)])
def audit(caseId: str | None = Query(default=None, max_length=80),
          eventType: str | None = Query(default=None, max_length=80)):
    sql='SELECT * FROM audit_events'
    conditions=[]; values=[]
    if caseId:
        conditions.append('case_id=?'); values.append(caseId)
    if eventType:
        conditions.append('event_type=?'); values.append(eventType)
    if conditions: sql += ' WHERE ' + ' AND '.join(conditions)
    sql += ' ORDER BY id DESC LIMIT 300'
    with connect() as c: rows=c.execute(sql,values).fetchall()
    return [{'id':r['id'],'caseId':r['case_id'],'eventType':r['event_type'],'createdAt':r['created_at'],'data':json.loads(r['data'])} for r in rows]

@app.post('/audit/events',dependencies=[Depends(internal)])
def audit_write(data: AuditRequest):
    correlation = data.correlationId or str(uuid4())
    with connect() as c: event(c,data.eventType,{'errorCode':data.errorCode,'correlationId':correlation})
    return {'logged':True,'correlationId':correlation}

@app.get('/metrics',dependencies=[Depends(reviewer)])
def metrics():
    with connect() as c: row=c.execute("SELECT value FROM metrics WHERE name='ai_calls'").fetchone()
    return {'aiCalls':row['value']}

@app.post('/submit')
async def submit(request: Request):
    # A transport proxy only; n8n alone orchestrates the processing sequence.
    try: payload=await request.json()
    except (ValueError,UnicodeDecodeError):
        return JSONResponse(status_code=400,content={'errorCode':'INVALID_INPUT','message':'Ongeldige JSON.'})
    headers={}
    if DEMO_MODE and request.headers.get('x-demo-scenario')=='fairness': headers['X-Demo-Scenario']='fairness'
    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            response=await client.post(N8N_URL,json=payload,headers=headers)
        value=response.json()
        if response.status_code >= 500 or not isinstance(value,dict) or ('message' not in value): raise ValueError('Unexpected workflow response')
        return JSONResponse(status_code=response.status_code,content=value)
    except (httpx.HTTPError,ValueError):
        return JSONResponse(status_code=503,content={'errorCode':'SERVICE_UNAVAILABLE','message':'De aanvraag kon niet veilig worden verwerkt. Controleer of n8n draait en de workflow gepubliceerd is. Probeer later opnieuw.'})

@app.get('/')
def index(): return FileResponse(Path(__file__).resolve().parents[1]/'static'/'index.html')
