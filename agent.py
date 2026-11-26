"""Read-only evidence tools and separately persisted review decisions."""
import json
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from build import DB, ROOT
import models

REQUESTS=('Prepare a case summary','Review account activity','Check linked disputes')
LOG=ROOT/'reviews.db'
def clock(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def connect_data(path=DB):
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    return db

def app_log(path=LOG):
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS runs(id integer primary key, alert text, request text, created text, status text, draft text, trace text, usage text, elapsed real);
    CREATE TABLE IF NOT EXISTS decisions(run_id integer primary key references runs, reviewer text, decision text, comment text, final_text text, decided text);
    CREATE TABLE IF NOT EXISTS pilot(run_id integer primary key references decisions, manual real check(manual>0), assisted real check(assisted>0));
    """)
    db.execute('PRAGMA foreign_keys=ON')
    return db

def get_alert_context(db,alert):
    if not re.fullmatch(r'AL[0-9]{6}',alert): raise ValueError('Enter an alert ID such as AL000001.')
    row=db.execute("""SELECT a.*,t.merchant_raw,t.amount_direction,t.txn_ts_raw,t.brand_status,b.acct_type
      FROM fact_alert a JOIN silver_transactions t USING(txn_id) JOIN dim_account b ON b.acct_id=a.acct_id WHERE a.alert_id=?""",(alert,)).fetchone()
    if row is None: raise ValueError('Alert ID is absent from the validated extract.')
    return dict(row)

def get_account_activity(db,context,acct):
    if acct!=context['acct_id']: raise ValueError('The requested account is outside this alert.')
    if context['ts_convention']!='UTC': return None
    end=context['txn_ts_raw']
    start=(datetime.fromisoformat(end.replace('Z','+00:00'))-timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    return [dict(r) for r in db.execute("""SELECT txn_id,channel,cents,amount_direction FROM silver_transactions
        WHERE acct_id=? AND ts_convention='UTC' AND txn_ts_raw BETWEEN ? AND ? ORDER BY txn_ts_raw DESC, txn_id LIMIT 20""",(acct,start,end))]

def get_notes(db,alert):
    return [dict(r) for r in db.execute('SELECT line_no,text,evidence_status FROM silver_notes WHERE alert_id=? ORDER BY line_no LIMIT 10',(alert,))]

def calculate_case_indicators(rows):
    card=[r for r in rows if r['amount_direction']=='spend']
    return len(rows),sum(r['cents'] for r in card)/100,[r['txn_id'] for r in rows]

def prepare(db,log,alert,request,mode):
    started=time.monotonic(); alert=alert.strip().upper(); trace=[]
    try:
        if request not in REQUESTS: raise ValueError('Choose a supported analyst request.')
        c=get_alert_context(db,alert); trace.append('get_alert_context '+alert+' → '+c['txn_id'])
        plan=['get_notes']
        if request!=REQUESTS[2] and c['ts_convention']=='UTC': plan+=['get_account_activity','calculate_case_indicators']
        if request==REQUESTS[2]: plan+=['get_linked_disputes']
        trace.append('Plan: '+' → '.join(plan+['draft','submit_draft_for_review']))
        notes=get_notes(db,alert); trace.append(f'get_notes → {len(notes)} supplied')
        lead='Review the linked transaction and its source record.'
        action='Verify the transaction evidence before accepting this summary.'
        limitations=['Rule definition unavailable. Use the reported code.']
        detail=[f"{alert} · {c['alert_dt']} · rule {c['rule_id']}\nTransaction {c['txn_id']} is a {c['channel']} entry on {c['acct_type']} account ending {c['acct_id'][-4:]}."]
        money={'spend':'card spend','unverified':'positive recorded amount; P2P direction unverified','in':'money in','out':'money out','none':'no monetary movement'}
        detail.append(f"Recorded amount: ${abs(c['amount']):,.2f} ({money[c['amount_direction']]}).")
        if c['merchant_raw']: detail.append(f"Source label: {c['merchant_raw']}."+(f" Candidate brand: {c['merchant_brand']}; grouping awaits review." if c['merchant_brand'] else f" Classification: {c['brand_status']}."))
        if not notes:
            limitations.append('No analyst note supplied.');lead='The alert has no supplied analyst note.';action='Seek corroborating evidence before completing the case note.'
        note_lines=[]
        for n in notes:
            note_lines.append(f"analyst_notes.jsonl line {n['line_no']} [{n['evidence_status']}]: {n['text']}")
        if any(n['evidence_status']=='channel conflict' for n in notes):
            lead='The note describes a wire and the linked transaction records another channel.'
            action='Reconcile the note with the transaction channel before accepting the case note.'
            limitations.append(lead)
        if c['ts_convention']=='LOCAL':
            limitations.append('Local timezone unconfirmed. Account time-window calculation withheld.')
        if 'get_account_activity' in plan:
            rows=get_account_activity(db,c,c['acct_id'])
            n,total,refs=calculate_case_indicators(rows)
            trace+=['get_account_activity → same-account UTC records, seven days through alert transaction, maximum 20','calculate_case_indicators → '+', '.join(refs)]
            detail.append(f"UTC activity sample: {n} record(s), ${total:,.2f} card spend. Includes the anchor when returned. Limit 20, ending at the flagged transaction. Sources: "+', '.join(refs)+'.')
        if 'get_linked_disputes' in plan:
            ds=[dict(r) for r in db.execute('SELECT dispute_id,reason,status FROM fact_dispute WHERE txn_id=? AND acct_id=? ORDER BY dispute_id',(c['txn_id'],c['acct_id']))]
            trace.append(f"get_linked_disputes → {len(ds)} separate filings")
            detail.append(f"Linked disputes: {len(ds)}. "+' '.join(f"{r['dispute_id']} ({r['reason']}, {r['status']})." for r in ds))
            if len(ds)>1: limitations.append('Multiple filings concern this transaction. Verify each dispute ID separately.')
        selection,usage=models.draft(mode,list(dict.fromkeys([lead,'Review the transaction evidence for this alert.'])),list(dict.fromkeys([action,'Check the cited source records with the reviewing analyst.'])))
        body=selection['lead']+'\n\n'+'\n'.join(detail)+'\n\nEvidence limits\n'+'\n'.join(limitations)
        if note_lines: body+='\n\nAttributed note evidence\n'+'\n'.join(note_lines)
        body+='\n\nProposed next step\n'+selection['follow_up']
        trace+=['draft → evidence-constrained wording','submit_draft_for_review → awaiting human decision']
        state='Pending'
    except Exception as exc:
        with log:
            log.execute('INSERT INTO runs(alert,request,created,status,draft,trace,usage,elapsed) VALUES(?,?,?,?,?,?,?,?)',
                        (alert,request,clock(),'Failed','',json.dumps(trace+[str(exc)]),json.dumps({'provider':mode,'usage':'unavailable'}),time.monotonic()-started))
        raise
    with log:
        key=log.execute('INSERT INTO runs(alert,request,created,status,draft,trace,usage,elapsed) VALUES(?,?,?,?,?,?,?,?)',
            (alert,request,clock(),state,body,json.dumps(trace,ensure_ascii=False),json.dumps(usage),time.monotonic()-started)).lastrowid
    return key

def decide(log,run,reviewer,decision,comment,final_text):
    reviewer=reviewer.strip(); comment=comment.strip(); final_text=final_text.strip()
    if not reviewer: raise ValueError('Enter reviewer initials.')
    if decision not in ('Approved','Revision requested'): raise ValueError('Choose a human review decision.')
    if decision=='Revision requested' and not comment: raise ValueError('Record the revision the author needs to make.')
    if decision=='Approved' and not final_text: raise ValueError('An approved note needs text.')
    with log:
        original=log.execute('SELECT status,draft FROM runs WHERE id=?',(run,)).fetchone()
        if not original or original['status']!='Pending':
            raise ValueError('Only a pending draft can receive a decision.')
        if decision=='Approved' and '[channel conflict]' in original['draft'] and not comment:
            raise ValueError('Document how you handled the conflicting note before approval.')
        changed=log.execute("UPDATE runs SET status=? WHERE id=? AND status='Pending'",(decision,run))
        if changed.rowcount!=1: raise ValueError('Only a pending draft can receive a decision.')
        log.execute('INSERT INTO decisions VALUES(?,?,?,?,?,?)',(run,reviewer,decision,comment,final_text if decision=='Approved' else '',clock()))

def record_timing(log,run,manual,assisted):
    if not(0<manual<=1440 and 0<assisted<=1440): raise ValueError('Enter both measured durations in minutes, between 0 and 1,440.')
    with log:
        if not log.execute("SELECT 1 FROM decisions WHERE run_id=? AND decision='Approved'",(run,)).fetchone():
            raise ValueError('Pilot measurements require an approved case.')
        log.execute('INSERT INTO pilot VALUES(?,?,?)',(run,manual,assisted))

