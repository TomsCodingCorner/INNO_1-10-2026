#!/usr/bin/env python3
"""Call the actual n8n webhook. Never fall back to individual backend endpoints.
Run after publishing the workflow; requires REVIEWER_KEY in .env or environment.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_env():
    values = {}
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                key,value=line.split('=',1)
                values[key.strip()]=value.strip().strip('\"\'')
    return {**values,**os.environ}

def request(url,body=None,headers=None):
    data = None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json',**(headers or {})})
    try:
        with urllib.request.urlopen(req,timeout=35) as response:
            return response.status,json.load(response)
    except urllib.error.HTTPError as exc:
        raw=exc.read().decode()
        try: content=json.loads(raw)
        except ValueError: content={'message':raw[:200]}
        return exc.code,content

def ensure(condition,message):
    if not condition: raise AssertionError(message)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--webhook',default='http://localhost:5678/webhook/wmo-aanvraag')
    parser.add_argument('--api',default='http://localhost:8000')
    parser.add_argument('--output',default=str(ROOT/'test-artifacts/e2e-results.json'))
    args=parser.parse_args()
    env=read_env()
    key=env.get('REVIEWER_KEY','')
    headers={'X-Reviewer-Key':key}
    results=[]
    setup_error=None
    try:
        ensure(bool(key),'REVIEWER_KEY ontbreekt; maak .env met de reviewer-sleutel.')
        code,health=request(args.api+'/health')
        ensure(code==200,'Backend healthcheck mislukt.')
        ensure(health.get('demoMode') is True,'DEMO_MODE moet true zijn voor de fairness-fixture.')
        code,_=request(args.api+'/metrics',headers=headers)
        ensure(code==200,'Reviewer-key geeft geen toegang tot metrics.')
    except Exception as exc:
        setup_error=f'{type(exc).__name__}: {exc}'
    for filename,name,expected in [
        ('01-low-risk.json','low_risk','pending_standard_review'),
        ('02-high-risk.json','high_risk','pending_priority_review'),
        ('03-fairness.json','fairness','pending_priority_review'),
        ('04-no-consent.json','no_consent',None),
    ]:
        entry={'test':name,'transport':'actual_n8n_webhook','status':'not_run'}
        if setup_error:
            entry['reason']=setup_error
            results.append(entry)
            continue
        try:
            payload=json.loads((ROOT/'fixtures'/filename).read_text())
            before=request(args.api+'/metrics',headers=headers)[1]['aiCalls']
            prior_event_ids={e['id'] for e in request(args.api+'/audit',headers=headers)[1]}
            code,value=request(args.webhook,body=payload,headers={'X-Demo-Scenario':'fairness'} if name=='fairness' else {})
            entry['httpStatus']=code
            ensure(isinstance(value,dict),'Webhook gaf geen JSON-object.')
            if name=='no_consent':
                after=request(args.api+'/metrics',headers=headers)[1]['aiCalls']
                entry['aiCallsBefore']=before
                entry['aiCallsAfter']=after
                ensure(code==400,f'Verwacht HTTP 400, ontvangen {code}.')
                ensure('toestemming' in value.get('message','').lower(),'Duidelijke toestemmingsmelding ontbreekt.')
                ensure(after==before,'De teller voor AI-aanroepen veranderde bij geweigerde toestemming.')
                events=request(args.api+'/audit',headers=headers)[1]
                ensure(any(e['id'] not in prior_event_ids and e['eventType']=='validation_failed' and e['data'].get('errorCode')=='AI_CONSENT_REQUIRED' for e in events),'Validatiefout ontbreekt in audit.')
            else:
                ensure(code==200,f'Verwacht HTTP 200, ontvangen {code}.')
                ensure(value.get('status')==expected,f'Onjuiste status: {value.get("status")}.')
                ensure(bool(value.get('message')),'Burgerbericht ontbreekt.')
                ensure('geslacht' not in value['message'].lower(),'Fairness-output lekte naar burgerbericht.')
                case_id=value.get('caseId')
                ensure(bool(case_id),'caseId ontbreekt.')
                entry['caseId']=case_id
                rows=request(args.api+'/reviews',headers=headers)[1]
                row=next((r for r in rows if r['caseId']==case_id),None)
                ensure(row is not None,'Geen reviewtaak opgeslagen.')
                ensure(row['status']==expected,'Reviewstatus verschilt van burgerresponse.')
                if name=='fairness': ensure('fairness:geslacht' in row['flags'],'Fairness-flag ontbreekt.')
                if name=='high_risk': ensure(row['riskScore']==100,'Hoge risicoscore ontbreekt.')
                code,cases=request(args.api+'/cases?q='+case_id,headers=headers)
                ensure(code==200,'Volledig aanvragenoverzicht niet beschikbaar.')
                ensure(cases['counts']['total']==1,'Zoeken op dossiernummer vond niet exact deze zaak.')
                ensure(cases['cases'][0]['caseId']==case_id,'Zoekresultaat hoort niet bij de nieuwe zaak.')
                code,detail=request(args.api+'/cases/'+case_id,headers=headers)
                ensure(code==200,'Aanvraagdetails niet beschikbaar.')
                ensure(detail['caseId']==case_id,'Detail hoort niet bij de nieuwe zaak.')
                ensure(detail['aiInput']==value['aiInput'],'Detail toont niet de werkelijk teruggegeven AI-input.')
                ensure(any(t['eventType']=='ai_preparation' for t in detail['timeline']),'Tijdlijn mist AI-voorbereiding.')
                events=request(args.api+'/audit',headers=headers)[1]
                matching=[e for e in events if e['caseId']==case_id and e['eventType']=='ai_preparation']
                ensure(bool(matching),'Auditrecord ontbreekt.')
                ai=matching[0]['data']['aiInput']
                ensure(set(ai)=={'ageGroup','requestType','severity','problemCount','limitations','existingSupport'},'AI-input wijkt af van allowlist.')
                if name == 'low_risk':
                    code,decision=request(args.api+'/reviews/'+case_id+'/decision',body={'decision':'needs_information','reasoning':'Demo: medewerker vraagt eerst aanvullende informatie op.'},headers=headers)
                    ensure(code==200,'Menselijke beslissing kon niet worden opgeslagen.')
                    ensure(decision['status']=='needs_information','Besluitstatus werd niet bijgewerkt.')
                    code,detail=request(args.api+'/cases/'+case_id,headers=headers)
                    ensure(detail['humanDecision']['decision']=='needs_information','Menselijke beslissing staat niet in details.')
                    code,cases=request(args.api+'/cases?status=needs_information',headers=headers)
                    ensure(any(c['caseId']==case_id for c in cases['cases']),'Afgehandelde zaak is niet vindbaar in volledig overzicht.')
                    rows=request(args.api+'/reviews',headers=headers)[1]
                    ensure(all(r['caseId']!=case_id for r in rows),'Afgehandelde zaak staat nog in de werkvoorraad.')
            entry['status']='passed'
        except Exception as exc:
            entry['status']='failed'
            entry['reason']=f'{type(exc).__name__}: {exc}'
        results.append(entry)
    access={'test':'reviewer_access_controls','transport':'backend_after_n8n_setup','status':'not_run'}
    if setup_error:
        access['reason']=setup_error
    else:
        try:
            code,_=request(args.api+'/cases')
            ensure(code==401,'/cases zonder reviewer-key moet worden geweigerd.')
            code,_=request(args.api+'/cases',headers={'X-Reviewer-Key':'wrong'})
            ensure(code==401,'/cases met verkeerde reviewer-key moet worden geweigerd.')
            code,_=request(args.api+'/audit')
            ensure(code==401,'/audit zonder reviewer-key moet worden geweigerd.')
            access['status']='passed'
        except Exception as exc:
            access['status']='failed'
            access['reason']=f'{type(exc).__name__}: {exc}'
    results.append(access)
    report={'executedAt':datetime.now(timezone.utc).isoformat(),'webhook':args.webhook,'scope':'actual n8n orchestration; no backend fallback','tests':results}
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for entry in results:
        print(f'{entry["test"]}: {entry["status"]}'+(f' — {entry["reason"]}' if 'reason' in entry else ''))
    print(f'Resultaat: {path}')
    return 0 if all(r['status']=='passed' for r in results) else 1

if __name__=='__main__': sys.exit(main())
