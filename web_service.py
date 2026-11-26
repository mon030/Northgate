"""Private JSON bridge between Next.js and the same tested agent tools."""
import json
import sys
from contextlib import closing
from datetime import datetime
import agent
import models
from build import METRICS
from business import scenarios

def dashboard(db,log,args):
    months=[r[0] for r in db.execute('SELECT DISTINCT alert_month FROM fact_alert ORDER BY 1')]
    rules=[r[0] for r in db.execute('SELECT rule_id FROM dim_rule ORDER BY 1')]
    month=args.get('month','All'); rule=args.get('rule','All')
    if month not in ['All',*months] or rule not in ['All',*rules]: raise ValueError('Unknown month or rule.')
    where=" FROM fact_alert WHERE (?='All' OR alert_month=?) AND (?='All' OR rule_id=?)"
    params=(month,month,rule,rule)
    def query(select,suffix=''):
        return [dict(r) for r in db.execute('SELECT '+select+where+suffix,params)]
    totals=query(METRICS)[0]
    cases={r['alert_id'] for r in query('alert_id')}
    pairs=[r[1] for r in log.execute('SELECT r.alert,p.manual-p.assisted FROM pilot p JOIN runs r ON r.id=p.run_id') if r[0] in cases]
    totals.update(observed_minutes_saved=round(sum(pairs)/len(pairs),2) if pairs else None,pilot_pairs=len(pairs))
    by_rule=query('rule_id,'+METRICS,' GROUP BY rule_id ORDER BY sum(minutes_spent) DESC,rule_id')
    by_month=query('alert_month,'+METRICS,' GROUP BY alert_month ORDER BY alert_month')
    return dict(months=months,rules=rules,month=month,rule=rule,totals=totals,by_rule=by_rule,by_month=by_month)

def run_data(log,key):
    row=log.execute('SELECT * FROM runs WHERE id=?',(int(key),)).fetchone()
    if not row:raise ValueError('Run not found.')
    run=dict(row);run['usage']=json.loads(run['usage']);run['trace']=json.loads(run['trace'])
    for key,table in [('decision','decisions'),('timing','pilot')]:
        item=log.execute(f'SELECT * FROM {table} WHERE run_id=?',(run['id'],)).fetchone()
        run[key]=dict(item) if item else None
    return run

def execute(op,args):
    with closing(agent.connect_data()) as db,closing(agent.app_log()) as log:
        if op=='alerts':
            term=str(args.get('q','')).strip().upper()[:40]; kind=args.get('kind','All')
            conditions={'All':'1','Missing note':'a.has_note=0','Conflicting note':"EXISTS(SELECT 1 FROM silver_notes n WHERE n.alert_id=a.alert_id AND n.evidence_status='channel conflict')",'Local timestamp':"a.ts_convention='LOCAL'",'Linked disputes':'EXISTS(SELECT 1 FROM silver_disputes d WHERE d.txn_id=a.txn_id)'}
            if kind not in conditions:raise ValueError('Unknown case filter.')
            where=" FROM fact_alert a WHERE (instr(a.alert_id,?) OR instr(a.txn_id,?) OR a.rule_id=? OR ?='') AND "+conditions[kind]
            params=(term,term,term,term)
            total=db.execute('SELECT count(*)'+where,params).fetchone()[0]
            pages=max(1,(total+19)//20); page=min(pages,max(1,int(args.get('page',1))))
            items=[dict(r) for r in db.execute('SELECT a.alert_id,a.txn_id,a.alert_dt,a.rule_id,a.channel,a.has_note,a.ts_convention'+where+' ORDER BY a.alert_id LIMIT 20 OFFSET ?',(*params,(page-1)*20))]
            return dict(items=items,page=page,pages=pages,total=total,kinds=list(conditions))
        if op=='quality':
            summary=[dict(r) for r in db.execute('SELECT issue,outcome,count(*) AS records FROM quarantine_history GROUP BY issue,outcome ORDER BY records DESC')]
            examples=[dict(r) for r in db.execute("""SELECT i.source_key,i.issue,i.raw_value,h.after_value,h.rule,h.outcome FROM quarantine_intake i
                JOIN quarantine_history h USING(source,source_key,issue) WHERE i.source_key IN (SELECT min(source_key) FROM quarantine_intake GROUP BY issue) ORDER BY i.issue""")]
            return dict(summary=summary,examples=examples)
        if op=='dashboard':return dashboard(db,log,args)
        if op=='economics':return scenarios()
        if op=='history':return [dict(r) for r in log.execute('SELECT id,alert,status,created FROM runs ORDER BY id DESC LIMIT 50')]
        if op=='run':return run_data(log,args['id'])
        if op=='prepare':
            mode=args.get('mode',models.LOCAL)
            if mode==models.GEMINI:
                if args.get('cloudConsent') is not True:raise ValueError('Confirm the displayed Gemini data transfer first.')
                models.session_gemini_key=args.get('apiKey')
            key=agent.prepare(db,log,args['alert'],args['request'],mode)
            return run_data(log,key)
        if op=='review':
            agent.decide(log,int(args['id']),args['reviewer'],args['decision'],args.get('comment',''),args['text'])
            return run_data(log,args['id'])
        if op=='timing':
            agent.record_timing(log,int(args['id']),float(args['manual']),float(args['assisted']))
            return run_data(log,args['id'])
        raise ValueError('Unknown operation.')

if __name__=='__main__':
    sys.stdin.reconfigure(encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8')
    try:
        req=json.load(sys.stdin); result=execute(req['op'],req.get('args',{}))
        print(json.dumps({'data':result}))
    except Exception as exc:
        print(json.dumps({'error':str(exc) if isinstance(exc,(ValueError,RuntimeError)) else 'Request failed. Check the inputs and review history.'}))

