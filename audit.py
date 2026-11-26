"""Independently compare teammate exports with the Bronze-derived data product."""
from collections import Counter
from decimal import Decimal, InvalidOperation
import sqlite3
from build import DB, ROOT, EVIDENCE, export, load_sources, read_csv

GRAINS={'fact_alert':'alert_id','fact_dispute':'dispute_id','dim_rule':'rule_id','v_workload_by_rule':'rule_id','v_dashboard_summary':None}
NUMBERS=set('alert_count recorded_minutes analyst_hours total_analyst_hours minutes_per_alert false_positive_pct note_coverage_pct amount minutes_spent score is_false_positive has_note dispute_seq_on_txn disputes_on_txn resolved_late open_overdue_at_snapshot'.split())

def equivalent(key,a,b):
    if key in NUMBERS:
        try: return Decimal(str(a))==Decimal(str(b))
        except InvalidOperation: return False
    return str(a)==str(b)

def audit():
    data,_=load_sources()
    db=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    result=[]; diffs=[]
    for name,grain in GRAINS.items():
        supplied=read_csv(ROOT/'data'/'teammate_exports'/(name+'.csv'))
        expected=[dict(r) for r in db.execute(f'SELECT * FROM {name}')]
        fields=set(expected[0]); actual_fields=set(supplied[0]) if supplied else set()
        if fields!=actual_fields: diffs.append((name,'schema','columns',str(sorted(fields)),str(sorted(actual_fields))))
        def index(rows):
            out={}
            for n,row in enumerate(rows):
                k=row.get(grain) if grain else str(n)
                if k in out: diffs.append((name,k,'duplicate key','unique','repeated'))
                out[k]=row
            return out
        x,y=index(expected),index(supplied)
        for k in sorted(set(x)|set(y)):
            if k not in x or k not in y:
                diffs.append((name,k,'key membership',str(k in x),str(k in y)));continue
            for field in fields & actual_fields:
                if not equivalent(field,x[k][field],y[k][field]): diffs.append((name,k,field,x[k][field],y[k][field]))
        result.append({'file':name+'.csv','grain':grain or 'whole extract','bronze_derived_rows':len(expected),'supplied_rows':len(supplied),'compared_columns':len(fields & actual_fields),'differences':sum(d[0]==name for d in diffs)})
    export('teammate_audit.csv',result,result[0])
    cols=['table','key','field','bronze_derived','teammate']
    export('teammate_differences.csv',[dict(zip(cols,d)) for d in diffs],cols)
    t=data['transactions']; a=data['alerts']; notes=data['notes']; disputes=data['disputes']
    notes_ids={r['alert_id'] for r in notes}; dist=Counter(r['txn_id'] for r in disputes)
    issues=[
        ('transactions','US-formatted local date fails ISO parser',sum('/' in r['txn_ts'] for r in t),'Attempt ISO parse; inspect rejected source form','Reparse month/day/year and time; validate normalized local clock by txn_id.','Rows reenter Silver. Timezone remains unknown.'),
        ('transactions','Timestamp lacks offset',sum(not r['txn_ts'].endswith('Z') for r in t),'Check UTC suffix','Preserve source time. Omit cross-convention windows.','Local activity cannot be ordered against UTC.'),
        ('transactions','Netflix label variation',sum(r['merchant_raw'] in ('NETFLIX.COM','Netflix Inc') for r in t),'Count both raw spellings','Retain raw and mark brand as candidate.','Grouped activity requires Data Lead sign-off.'),
        ('transactions','BRANCH in merchant field',sum(r['merchant_raw']=='BRANCH' for r in t),'Match literal and cash-deposit channel','Quarantine classification, classify location, revalidate by txn_id.','Preserves cash deposits without overstating merchants.'),
        ('transactions','Unverified P2P direction',sum(r['channel']=='P2P' for r in t),'All P2P amounts are positive in extract','Show amount and flag direction.','Exclude from money-in and out totals.'),
        ('alerts and notes','No supplied note',sum(r['alert_id'] not in notes_ids for r in a),'Left anti-join on alert_id','Keep alert and label missing evidence.','Coverage denominator includes every alert.'),
        ('notes','Repeated stock wording',len(notes),'Count distinct text and frequency; all seven phrases recur','Retain note per alert and attribute to author.','Identical wording is weak corroboration.'),
        ('notes and transactions','Wire narrative conflicts with linked channel',db.execute("SELECT count(*) FROM silver_notes WHERE evidence_status='channel conflict'").fetchone()[0],'Compare Large wire wording to linked channel','Quarantine claim, keep attributed note and discrepancy, require human verification.','Prevents prose from turning a conflicting note into an established fact.'),
        ('disputes','Multiple filings on a transaction',sum(n for n in dist.values() if n>1),'Group by txn_id having count greater than one','Keep individual dispute_id and chronological sequence.','Transaction-grain counting loses distinct filings.'),
        ('rule dictionary','No authoritative rule definition',len({r['rule_id'] for r in a}),'Count distinct rule codes with blank supplied descriptions','Retain code alone.','Cannot attribute a rule trigger mechanism.'),
    ]
    cols=['source','finding','affected_rows','detection','processing_rule','impact']
    export('quality_log.csv',[dict(zip(cols,r)) for r in issues],cols)
    # Independent controls for dashboard, including rule and month slices.
    controls=[]
    for month in ['All']+sorted({r['alert_dt'][:7] for r in a}):
        for rule in ['All']+sorted({r['rule_id'] for r in a}):
            selected=[r for r in a if (month=='All' or r['alert_dt'][:7]==month) and (rule=='All' or r['rule_id']==rule)]
            if not selected: continue
            n=len(selected); minutes=sum(int(r['minutes_spent']) for r in selected)
            raw=[n,sum(r['disposition']=='False positive' for r in selected),minutes,sum(r['alert_id'] in notes_ids for r in selected)]
            fact=list(db.execute("""SELECT count(*),sum(is_false_positive),sum(minutes_spent),sum(has_note) FROM fact_alert
             WHERE (?='All' OR alert_month=?) AND (?='All' OR rule_id=?)""",(month,month,rule,rule)).fetchone())
            if raw!=fact: raise ValueError(f'Workload control mismatch: {month}, {rule}')
            controls.append(dict(month=month,rule=rule,alerts=n,false_positives=raw[1],historical_minutes=minutes,alerts_with_notes=raw[3],result='matches Bronze'))
    export('dashboard_checks.csv',controls,controls[0])
    db.close()
    return result,diffs

if __name__=='__main__':
    for row in audit()[0]: print(row)

