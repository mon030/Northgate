"""Exercise the public Next.js routes as a named QA fixture; leave pilot timings empty."""
import json
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from build import EVIDENCE, export
BASE='http://127.0.0.1:3301'
def api(op,body=None,**query):
    req=Request(BASE+'/api/'+op+'?'+urlencode(query),data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','Origin':BASE})
    with urlopen(req,timeout=85) as response:return json.load(response)
def main():
    records=[]
    def check(name,ok,detail):
        if not ok:raise AssertionError(name)
        records.append(dict(check=name,result='PASS',observed=detail))
    d=api('alerts',page=81)
    check('Last page reachable',d['total']==1613 and d['items'][-1]['alert_id']=='AL001613','1,613 unique alert IDs available across 81 pages')
    d=api('alerts',kind='Conflicting note');check('Conflict filter',d['total']==45,'45 matched alerts')
    check('Missing-note filter',api('alerts',kind='Missing note')['total']==1188,'1,188 matched alerts')
    check('Exact ID search',api('alerts',q='AL000071')['total']==1,'One matching alert')
    check('Empty search',api('alerts',q='AL999999')['total']==0,'Zero results')
    totals=api('dashboard',rule='R07')['totals'];check('Rule filter',totals['alert_count']==829 and totals['total_analyst_hours']==414.7,'R07 reconciled to Bronze')
    for alert,decision,comment in [('AL000029','Revision requested','QA fixture: wire narrative conflicts with the card transaction. Seek corroboration.'),
                                    ('AL000002','Approved','QA fixture: checked the source transaction and missing-note disclosure.')]:
        r=api('prepare',{'alert':alert,'request':'Prepare a case summary','mode':'Local model'})
        check('Draft stops for review '+alert,r['status']=='Pending' and r['usage']['input']>0,'Real model usage logged; original draft pending')
        final=api('review',dict(id=r['id'],decision=decision,reviewer='QA demo',comment=comment,text=r['draft']))
        saved=api('run',id=r['id'])
        check('Review persistence '+alert,final['status']==decision and saved['decision']['decision']==decision,'Run '+str(r['id'])+' recorded '+decision+' under QA demo')
        check('Human timing separation '+alert,saved['timing'] is None,'No synthetic timing pair created')
    export('web_checks.csv',records,records[0]);print(len(records),'web checks passed')
if __name__=='__main__':main()

