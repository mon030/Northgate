"""Build a case-preparation data product from the six immutable Northgate extracts."""
import csv
import hashlib
import json
import os
import sqlite3
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BRONZE = ROOT / 'data' / '2_Northgate_Bank' / 'bronze'
EVIDENCE = ROOT / 'evidence'
DB = ROOT / 'northgate.db'
SNAPSHOT = '2026-09-06'
SOURCES = {
    'customers': ('core_banking/customers.csv', 'cust_id first_name last_name dob address city state phone email segment'),
    'accounts': ('core_banking/accounts.csv', 'acct_id cust_id acct_type open_dt status'),
    'transactions': ('transactions/transactions.csv', 'txn_id acct_id txn_ts channel amount merchant_raw mcc counterparty device_id ip_country'),
    'alerts': ('fraud_engine/alerts.csv', 'alert_id txn_id acct_id rule_id score alert_dt disposition analyst_id minutes_spent'),
    'notes': ('fraud_engine/analyst_notes.jsonl', 'alert_id analyst_id text'),
    'disputes': ('disputes/card_disputes.csv', 'dispute_id acct_id txn_id filed_dt reason amount due_dt status resolved_dt provisional_credit'),
}
BRAND_LABELS = {
    'Netflix': ['NETFLIX.COM','Netflix Inc'], 'Apple': ['Apple Store R112','APPLE.COM/BILL'],
    'Techbay': ['TECHBAY*ORDER','TECHBAY LTD'], 'Target': ['Target T-2201','TARGET 00014'],
    'Kroger': ['Kroger Fuel Ctr','KROGER #512'], 'Uber': ['Uber BV','UBER *TRIP'],
    'Home Depot': ['HOME DEPOT #4112','THE HOME DEPOT 0621'], 'Starbucks': ['Starbucks Store 1182','STARBUCKS #9921'],
    'Shell': ['SHELL OIL 5744','SHELL #221','Shell Service Stn'],
    'Amazon': ['Amazon Mktp US','AMZN MKTP US*2K4','AMAZON.COM*M81'],
    'Walmart': ['WAL-MART #1043','Wal-Mart Supercenter','WALMART.COM'],
}
BRANDS = {label:brand for brand,labels in BRAND_LABELS.items() for label in labels}

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def export(name, rows, columns):
    with (EVIDENCE/name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def load_sources():
    data, lineage = {}, []
    manifest = {r['file']:r for r in read_csv(BRONZE/'_manifest.csv')}
    for name,(filename,header) in SOURCES.items():
        path = BRONZE/filename
        raw = path.read_bytes()
        records = [json.loads(line) for line in raw.splitlines() if line.strip()] if name=='notes' else read_csv(path)
        if any(set(r)!=set(header.split()) for r in records) or not records:
            raise ValueError(f'{filename}: schema changed. Data Lead must review before publishing.')
        if len(records)!=int(manifest[filename]['records']):
            raise ValueError(f'{filename}: manifest count changed.')
        data[name] = records
        lineage.append((filename,len(records),len(raw),hashlib.sha256(raw).hexdigest(),datetime.now(timezone.utc).isoformat()))
    return data,lineage

def table(db,name,schema,rows):
    db.execute(f'CREATE TABLE {name} ({schema})')
    for row in rows:
        db.execute(f'INSERT INTO {name} VALUES ({",".join("?" for _ in row)})',tuple(row))

METRICS = """count(*) alert_count, round(100.0*avg(is_false_positive),1) false_positive_pct,
 round(sum(minutes_spent)/60.0,1) total_analyst_hours, round(avg(minutes_spent),1) minutes_per_alert,
 round(100.0*avg(has_note),1) note_coverage_pct"""

def stage_exceptions(db,data):
    """Capture source values before any cleansing so every intake must reconcile."""
    incoming=[]
    channels={r['txn_id']:r['channel'] for r in data['transactions']}
    alerts={r['alert_id']:r['txn_id'] for r in data['alerts']}
    for r in data['transactions']:
        if '/' in r['txn_ts']:
            incoming.append(('transactions',r['txn_id'],'timestamp format',r['txn_ts']))
        if r['channel']=='Cash deposit' and r['merchant_raw']=='BRANCH':
            incoming.append(('transactions',r['txn_id'],'merchant classification',r['merchant_raw']))
    for n,r in enumerate(data['notes'],1):
        if 'Large wire' in r['text'] and channels[alerts[r['alert_id']]]!='Wire':
            incoming.append(('notes',f"{r['alert_id']}/line {n}",'note describes wire',r['text']))
    table(db,'quarantine_intake','source text, source_key text, issue text, raw_value text, primary key(source,source_key,issue)',incoming)

def populate(db):
    data,lineage=load_sources()
    stage_exceptions(db,data)
    table(db,'lineage','file text primary key, records integer, bytes integer, sha256 text, loaded_at text',lineage)
    table(db,'dim_customer','cust_id text primary key, segment text',((r['cust_id'],r['segment']) for r in data['customers']))
    table(db,'dim_account','acct_id text primary key, cust_id text references dim_customer, acct_type text, open_dt text, status text',
          ([r[k] for k in SOURCES['accounts'][1].split()] for r in data['accounts']))
    events=[]
    txns=[]
    for r in data['transactions']:
        ch,raw,ts=r['channel'],r['merchant_raw'],r['txn_ts']
        conv='UTC' if ts.endswith('Z') else 'LOCAL'
        try:
            parsed=datetime.fromisoformat(ts.replace('Z','+00:00'))
        except ValueError:
            parsed=datetime.strptime(ts,'%m/%d/%Y %H:%M')
            events.append(('transactions',r['txn_id'],'timestamp format',ts,parsed.isoformat(),
                           'Parse documented US-style date and retain local clock without conversion.','reprocessed'))
        if (ch in ('Login','Card'))!=(conv=='UTC'):
            raise ValueError(f"Timestamp convention mismatch on {r['txn_id']}")
        value=Decimal(r['amount'])
        direction=('spend' if ch=='Card' else 'unverified' if ch=='P2P' else 'in' if value>0 else 'out' if value<0 else 'none')
        status='candidate' if raw in BRANDS else 'unmapped' if raw else 'not supplied'
        if status=='unmapped' and ch=='Cash deposit' and raw=='BRANCH':
            status='branch location'
            events.append(('transactions',r['txn_id'],'merchant classification','BRANCH','branch location','Cash deposit with BRANCH identifies a location. Exclude from merchant grouping.','reprocessed'))
        txns.append((r['txn_id'],r['acct_id'],ts,parsed.isoformat(),conv,ch,int(value*100),direction,raw,BRANDS.get(raw,''),status))
    table(db,'silver_transactions','txn_id text primary key, acct_id text references dim_account, txn_ts_raw text, source_clock_iso text, ts_convention text, channel text, cents integer, amount_direction text, merchant_raw text, merchant_brand text, brand_status text',txns)
    db.execute('CREATE INDEX activity_idx ON silver_transactions(acct_id,ts_convention,txn_ts_raw)')
    table(db,'silver_alerts','alert_id text primary key, txn_id text references silver_transactions, acct_id text references dim_account, rule_id text, score real check(score between 0 and 1), alert_dt text, disposition text, analyst_id text, minutes_spent integer check(minutes_spent>=0)',
        ([r[k] for k in SOURCES['alerts'][1].split()] for r in data['alerts']))
    channels=dict(db.execute('SELECT a.alert_id,t.channel FROM silver_alerts a JOIN silver_transactions t USING(txn_id)'))
    notes=[]
    for i,r in enumerate(data['notes'],1):
        text=r['text']; key=r['alert_id']; channel=channels[key]
        conflict='Large wire' in text and channel!='Wire'
        status='channel conflict' if conflict else 'unverified testimony'
        if conflict:
            events.append(('notes',f'{key}/line {i}','note describes wire',channel,status,'Preserve note verbatim, flag conflict against transaction and require analyst reconciliation.','reprocessed with limitation'))
        notes.append((i,key,r['analyst_id'],text,status))
    table(db,'silver_notes','line_no integer primary key, alert_id text references silver_alerts, analyst_id text, text text, evidence_status text',notes)
    table(db,'silver_disputes','dispute_id text primary key, acct_id text references dim_account, txn_id text references silver_transactions, filed_dt text, reason text, amount numeric, due_dt text, status text, resolved_dt text, provisional_credit text',
        ([r[k] for k in SOURCES['disputes'][1].split()] for r in data['disputes']))
    for name in ('silver_disputes','silver_alerts'):
        if db.execute(f'SELECT count(*) FROM {name} a JOIN silver_transactions t USING(txn_id) WHERE a.acct_id<>t.acct_id').fetchone()[0]:
            raise ValueError(f'{name}: account conflict. Previous release retained.')
    table(db,'quarantine_history','source text, source_key text, issue text, before_value text, after_value text, rule text, outcome text, primary key(source,source_key,issue)',events)
    for first,second in [('quarantine_intake','quarantine_history'),('quarantine_history','quarantine_intake')]:
        unmatched=db.execute(f'SELECT source,source_key,issue FROM {first} EXCEPT SELECT source,source_key,issue FROM {second}').fetchone()
        if unmatched:raise ValueError(f'Unreconciled exception {unmatched}. Previous release retained.')
    db.executescript(f"""
    CREATE VIEW dim_rule AS SELECT DISTINCT rule_id, '' AS description FROM silver_alerts;
    CREATE VIEW fact_alert AS SELECT a.alert_id,a.txn_id,a.acct_id,c.cust_id,c.segment,a.rule_id,a.alert_dt,substr(a.alert_dt,1,7) alert_month,
    a.disposition,(a.disposition='False positive') is_false_positive,a.analyst_id,a.minutes_spent,a.score,t.channel,t.cents/100.0 amount,t.merchant_brand,t.ts_convention,
    EXISTS(SELECT 1 FROM silver_notes n WHERE n.alert_id=a.alert_id) has_note
    FROM silver_alerts a JOIN dim_account b ON b.acct_id=a.acct_id JOIN dim_customer c USING(cust_id) JOIN silver_transactions t ON a.txn_id=t.txn_id;
    CREATE INDEX note_idx ON silver_notes(alert_id);
    CREATE VIEW fact_dispute AS SELECT *,count(*) over(partition by txn_id) disputes_on_txn,
    row_number() over(partition by txn_id order by filed_dt,dispute_id) dispute_seq_on_txn,
    (status='Closed' and resolved_dt>due_dt) resolved_late,(status='Open' and due_dt<'{SNAPSHOT}') open_overdue_at_snapshot FROM silver_disputes;
    CREATE VIEW v_dashboard_summary AS SELECT {METRICS} FROM fact_alert;
    CREATE VIEW v_workload_by_rule AS SELECT rule_id,count(*) alert_count,sum(minutes_spent) recorded_minutes,
    round(sum(minutes_spent)/60.0,1) analyst_hours,round(avg(minutes_spent),1) minutes_per_alert,
    round(100.0*avg(is_false_positive),1) false_positive_pct,round(100.0*avg(has_note),1) note_coverage_pct FROM fact_alert GROUP BY rule_id;
    """)
    if db.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('Foreign key checks failed')
    for src,key,target in [('transactions','txn_id','silver_transactions'),('notes','line_no','silver_notes')]:
        missing=db.execute(f"""SELECT count(*) FROM quarantine_history q WHERE source=? AND NOT EXISTS
         (SELECT 1 FROM {target} s WHERE q.source_key={('s.txn_id' if src=='transactions' else "s.alert_id || '/line ' || s.line_no")}
          AND q.after_value={("CASE WHEN q.issue='timestamp format' THEN s.source_clock_iso ELSE s.brand_status END" if src=='transactions' else 's.evidence_status')})""",(src,)).fetchone()[0]
        if missing: raise ValueError(f'{src}: recovery validation failed')
    counts={}
    for src,target in zip(SOURCES,['dim_customer','dim_account','silver_transactions','fact_alert','silver_notes','fact_dispute']):
        count=db.execute(f'SELECT count(*) FROM {target}').fetchone()[0]
        if count!=len(data[src]): raise ValueError(f'{src}: record loss')
        counts[src]={'source':src,'bronze':len(data[src]),'published':count,'distinct_rows_reprocessed':len({e[1] for e in events if e[0]==src}),'processed_exceptions':sum(e[0]==src for e in events)}
    return list(counts.values())

def build():
    EVIDENCE.mkdir(exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=ROOT,suffix='.building'); os.close(fd)
    try:
        db=sqlite3.connect(tmp)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            counts=populate(db)
            db.commit()
        finally: db.close()
        try: os.replace(tmp,DB)
        except PermissionError:
            # SQLite's online backup publishes atomically when Windows readers hold the old file open.
            from contextlib import closing
            with closing(sqlite3.connect(tmp)) as source, closing(sqlite3.connect(DB)) as dest:
                source.backup(dest)
        export('layer_counts.csv',counts,counts[0])
    finally: Path(tmp).unlink(missing_ok=True)

if __name__=='__main__':
    build()
    print('Rebuilt northgate.db from all six Bronze files.')

