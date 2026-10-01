"""Deterministically generate an n8n 1.112.6 workflow. No embedded credentials."""
import json
from pathlib import Path
from uuid import uuid5,NAMESPACE_DNS
nodes=[]; connections={}
def add(name,typ,version,parameters,x,y,**kwargs):
    nodes.append(dict(id=str(uuid5(NAMESPACE_DNS,'zorgagent-'+name)),name=name,type='n8n-nodes-base.'+typ,typeVersion=version,parameters=parameters,position=[x,y],**kwargs))
def link(src,dst,output=0):
    main=connections.setdefault(src,{'main':[]})['main']
    while len(main)<=output: main.append([])
    main[output].append({'node':dst,'type':'main','index':0})
def http(name,path,body,x,y,method='POST',scenario=False,error=True):
    headers=[{'name':'X-Internal-Key','value':'={{ $env.INTERNAL_KEY }}'}]
    if scenario: headers.append({'name':'X-Demo-Scenario','value':"={{ $('Aanvraag').item.json.headers['x-demo-scenario'] || '' }}"})
    p={'method':method,'url':'http://api:8000'+path,'sendHeaders':True,'headerParameters':{'parameters':headers},'options':{'timeout':10000}}
    if body is not None: p.update(sendBody=True,specifyBody='json',jsonBody='={{ '+body+' }}')
    add(name,'httpRequest',4.2,p,x,y,onError='continueErrorOutput')
    if error: link(name,'Log technische fout',1)
def iff(name,expr,x,y):
    add(name,'if',2.2,{'conditions':{'options':{'caseSensitive':True,'leftValue':'','typeValidation':'strict','version':2},'conditions':[{'id':name,'leftValue':'={{ '+expr+' }}','rightValue':True,'operator':{'type':'boolean','operation':'true','singleValue':True}}],'combinator':'and'},'options':{}},x,y)
def response(name,body,code,x,y):
    add(name,'respondToWebhook',1.4,{'respondWith':'json','responseBody':'={{ '+body+' }}','options':{'responseCode':code}},x,y)
add('Aanvraag','webhook',2,{'httpMethod':'POST','path':'wmo-aanvraag','responseMode':'responseNode','options':{}},0,0,webhookId='c42ef4a5-c1fe-4f05-bc7f-095446ae9376')
http('Prepare','/prepare','$json.body',220,0)
iff('Geldig?','$json.valid',440,0)
http('Policy','/policy/household_support',None,660,-100,'GET')
http('AI','/ai/propose',"{input: $('Prepare').item.json.aiInput, policy: $('Policy').item.json}",880,-100,scenario=True)
http('Assess','/assess',"{input: $('Prepare').item.json.aiInput, policy: $('Policy').item.json, proposal: $('AI').item.json}",1100,-100)
http('Opslaan','/cases',"{caseId: $('Prepare').item.json.caseId, token: $('Prepare').item.json.token, aiInput: $('Prepare').item.json.aiInput, policy: $('Policy').item.json, proposal: $('AI').item.json, assessment: $('Assess').item.json}",1320,-100)
iff('Prioriteit?','$json.requiresPriorityReview',1540,-100)
standard='Uw aanvraag is ontvangen en voorbereid met behulp van AI. Een medewerker beoordeelt uw aanvraag en neemt de beslissing. Er is nog geen voorziening toegekend.'
review='Uw aanvraag is ontvangen. Voor een zorgvuldige beoordeling is extra aandacht van een medewerker nodig. AI heeft geholpen bij de voorbereiding; een medewerker neemt de beslissing.'
for name,message,y in [('Reviewbericht',review,-200),('Standaardbericht',standard,0)]:
    response(name,"{caseId: $('Opslaan').item.json.caseId, status: $('Opslaan').item.json.status, aiInput: $('Opslaan').item.json.aiInput, message: "+json.dumps(message)+'}',200,1770,y)
http('Log validatiefout','/audit/events',"{eventType:'validation_failed', errorCode: $('Prepare').item.json.errorCode}",660,180)
response('Ongeldige aanvraag',"{errorCode: $('Prepare').item.json.errorCode, message: $('Prepare').item.json.message}",400,900,180)
http('Log technische fout','/audit/events',"{eventType:'technical_failure',errorCode:'SERVICE_UNAVAILABLE'}",1100,440,error=False)
response('Technische fout',"{errorCode:'SERVICE_UNAVAILABLE',message:'De aanvraag kon niet veilig worden verwerkt. Probeer later opnieuw.'}",503,1350,440)
link('Log technische fout','Technische fout',0);link('Log technische fout','Technische fout',1)
for a,b in [('Aanvraag','Prepare'),('Prepare','Geldig?'),('Geldig?','Policy'),('Policy','AI'),('AI','Assess'),('Assess','Opslaan'),('Opslaan','Prioriteit?'),('Prioriteit?','Reviewbericht'),('Log validatiefout','Ongeldige aanvraag')]: link(a,b)
link('Geldig?','Log validatiefout',1);link('Prioriteit?','Standaardbericht',1)
w={'id':'zorgagentDemo01','name':'WMO — Zelfstandige Zorgagent (synthetische demo)','nodes':nodes,'connections':connections,'active':True,'settings':{'executionOrder':'v1','saveDataErrorExecution':'none','saveDataSuccessExecution':'none','saveManualExecutions':False,'executionTimeout':60},'pinData':{},'tags':[]}
p=Path(__file__).resolve().parents[1]/'n8n'/'workflow.json'
p.write_text(json.dumps(w,ensure_ascii=False,indent=2)+'\n')
print(p)
