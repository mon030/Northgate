"""Generate the class handoff PDFs using ReportLab (authoring dependency only)."""
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from build import ROOT,EVIDENCE,read_csv
from statistics import mean

ink='#183936'; green='#17634f'; muted='#48635f'; line='#ccdbd1'; pale='#eaf2ed'
def color(s):return colors.HexColor(s)
def write(c,x,y,s,size=10,font='Helvetica',fill=ink):
    c.setFillColor(color(fill));c.setFont(font,size);c.drawString(x,y,s)
def rect(c,x,y,w,h,fill):
    c.setFillColor(color(fill));c.rect(x,y,w,h,stroke=0,fill=1)
def arrow(c,x,y,x2,y2):
    from math import atan2,cos,sin
    c.setStrokeColor(color(green));c.setLineWidth(1.7);c.line(x,y,x2,y2)
    a=atan2(y2-y,x2-x)
    for d in [-.55,.55]:c.line(x2,y2,x2-8*cos(a+d),y2-8*sin(a+d))
def arch():
    w,h=landscape(letter);c=canvas.Canvas(str(ROOT/'Architecture.pdf'),pagesize=(w,h))
    c.setTitle('Northgate evidence architecture')
    rect(c,0,h-17,w,17,green)
    write(c,32,h-48,'NORTHGATE BANK   /   FRAUD OPERATIONS',9,'Helvetica-Bold',green)
    write(c,32,h-87,'How an alert reaches human review',27,'Times-Bold')
    write(c,32,h-110,'The build reconciles all six extracts. Every corrected field keeps a source key and processing rule.',11)
    def box(x,y,w,h,title,lines,shade=pale):
        rect(c,x,y,w,h,shade);write(c,x+11,y+h-22,title,12,'Helvetica-Bold',green)
        yy=y+h-42
        for txt in lines:
            for piece in simpleSplit(txt,'Helvetica',9,w-22):write(c,x+11,yy,piece,9);yy-=12
            yy-=3
    box(32,322,137,132,'Source systems',['Core banking: customers, accounts','Processor and core: transactions','Fraud engine: alerts, notes','Disputes: card filings'])
    box(187,322,124,132,'Bronze lake',['6 original CSV / JSONL extracts','Manifest, load time and SHA-256','Raw notes and source values retained'])
    box(329,322,131,132,'Silver warehouse',['Typed keys, cents and source clocks','Keyed note evidence','Check account and transaction joins'])
    box(478,322,120,132,'Gold views',['One row per alert','Separate dispute grain','Account, customer segment, rule and alert month'])
    box(616,322,143,132,'Next.js app',['Porter: six measures and filters','Tommy: scoped evidence tools and a proposed case note'])
    for x in [169,311,460,598]:arrow(c,x,390,x+17,390)
    box(188,167,272,113,'Quarantine and reprocessing',['9,376 local clocks normalized. 1,470 branch classifications overlap those transactions.','45 wire-note conflicts retained with both evidence sources. Analyst reconciliation required.'],'#f8f0dc')
    arrow(c,353,322,353,282);arrow(c,430,282,430,322)
    write(c,270,301,'Detect and record',8,'Helvetica',muted);write(c,437,301,'Revalidate',8,'Helvetica',muted)
    box(510,167,248,113,'Human approval and application log',['Analyst edits, approves or requests revision. A conflict requires an explanation.','Separate reviews.db stores original and accepted wording, trace, model usage and paired timings.'])
    arrow(c,685,322,685,282)
    write(c,32,135,'Why the layers differ',13,'Helvetica-Bold',green)
    for i,txt in enumerate(['Customer and account keys support structured joins. Transaction amounts, alerts and dispute dates need typed measures.',
        'Free-text notes remain verbatim in the lake and enter Silver as attributed evidence. Fact tables retain their own grains.',
        '9,421 distinct records received 10,891 treatments. All 31,254 transactions and 425 notes reached their published layer.',
        'Data Lead reviews new schema or ambiguous source corrections. Fraud Operations owns case acceptance. The agent reads evidence through fixed tools.']):
        write(c,32,113-16*i,txt,9.3)
    write(c,32,30,'Sources: Bronze manifest, build.py, layer_counts.csv and quarantine_history in northgate.db.',8,'Helvetica',muted)
    c.save()

class Brief:
    def __init__(self):
        self.c=canvas.Canvas(str(ROOT/'Funding brief.pdf'),pagesize=letter);self.c.setTitle('Northgate alert preparation pilot');self.n=0
    def page(self,section,title):
        if self.n:self.c.showPage()
        self.n+=1; self.y=680;c=self.c;rect(c,0,778,612,14,green)
        write(c,42,742,'NORTHGATE BANK   /   '+section.upper(),9,'Helvetica-Bold',green);write(c,42,700,title,26,'Times-Bold')
        write(c,42,27,'TEAM 09   /   BUAN 3301     •     NORTHGATE FRAUD OPERATIONS',8,'Helvetica',muted)
        write(c,550,27,str(self.n),9,'Helvetica',muted)
    def para(self,text,size=10.5):
        p=Paragraph(text,ParagraphStyle('body',fontName='Helvetica',fontSize=size,leading=size*1.45,textColor=color(ink)))
        _,height=p.wrap(528,1000);self.y-=height;p.drawOn(self.c,42,self.y);self.y-=9
        assert self.y>38,(self.n,self.y)
    def sub(self,s):
        self.y-=15;write(self.c,42,self.y,s,14,'Helvetica-Bold',green);self.y-=9
    def table(self,rows,widths):
        style=ParagraphStyle('cell',fontName='Helvetica',fontSize=9.3,leading=13,textColor=color(ink))
        cells=[[Paragraph(('<b>'+str(v)+'</b>') if i==0 else str(v),style) for v in row] for i,row in enumerate(rows)]
        t=Table(cells,colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),color(pale)),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.35,color(line)),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        _,h=t.wrap(528,1000);self.y-=h;t.drawOn(self.c,42,self.y);self.y-=9
        assert self.y>38,(self.n,self.y)
def report():
    b=Brief();b.page('Executive decision','Fund an alert preparation pilot')
    b.para('Authorize up to <b>$6,040 of one-time build and training effort</b> for a limited pilot owned by the fraud operations manager. Approve broader use only after analysts demonstrate sufficient time savings, traceable case notes and reliable human review.')
    b.sub('What the bank can establish today')
    b.para('Across January through June 2026, 1,613 alerts consumed 53,108 analyst minutes (885.1 hours). R07 alone accounted for 829 alerts and 414.7 hours. R09 averaged 62.6 minutes per alert. These figures identify queues where a preparation pilot could matter.')
    b.para('Historical dispositions include 1,457 false positives. Those reviews may have been necessary. The financial case values only preparation time that a paired human trial can demonstrate. It assigns no benefit to prevented fraud, avoided filings or disputed dollars.')
    b.sub('What changes for an analyst')
    b.para('The web app retrieves the flagged transaction, checks available notes, calculates supported indicators and proposes a cited case note. One real case, AL000029, links an $11.68 card purchase to a note describing a wire. The two records stay visible together. Approval requires the reviewer to document how that conflict was handled.')
    b.sub('Funding boundaries')
    b.table([['Decision','Evidence required'],['Run the pilot','Use the local agent, current six-source extract and an assigned reviewer. Capture manual and assisted minutes on the same alerts.'],['Expand','At assumed base adoption and rates, average time released must exceed 2.56 minutes per assisted alert for three-year break-even. Check accuracy and missing-evidence disclosures by rule and channel.'],['Rework or stop','Pause expansion if a note bypasses approval, a material claim lacks a source or the measured benefit falls below the funding threshold.']], [115,413])
    b.para('Source: Bronze alerts and notes, the submitted Team 09 outline, and evidence/dashboard_checks.csv. Pilot assumptions appear on the next page.',9)
    b.page('Finance','The cost of releasing analyst time')
    b.para('Model a steady annual workload of 3,226 eligible alerts, twice the six-month sample. Base adoption of 75% gives 2,419.5 expected assisted cases per year. Volumes, adoption, wages, costs and preparation times are planning assumptions. Analyst review remains in the running cost.')
    b.table([['Base item','Calculation','Value'],['Build and training','100 build hours × $55 + 12 training hours × $45','$6,040 once'],['Gross manual capacity','2,419.5 cases × 12 manual min ÷ 60 × $45','$21,776 / yr'],['Assisted work and review','2,419.5 cases × 5 assisted min ÷ 60 × $45','$9,073 / yr'],['Support, QA and compute','4 hours/month × $50 × 12 + $240 compute allowance','$2,640 / yr'],['API charges','Local model runs entirely on the workstation','$0 / yr'],['Net annual capacity','Gross manual capacity less $11,713 annual running cost','$10,062 / yr']], [132,273,123])
    b.sub('Three years at constant volume')
    b.table([['Sensitivity','Worst','Base','Best'],['Adoption / manual / assisted minutes','45% / 8 / 6','75% / 12 / 5','90% / 14 / 4'],['Build hours / monthly support hours','120 / 6','100 / 4','80 / 3'],['Cumulative net at year 1','-$8,802','$4,022','$14,795'],['Cumulative net at year 2','-$10,465','$14,085','$34,531'],['Cumulative net at year 3','-$12,127','$24,147','$54,266'],['Payback / 3-year economic ROI','Unreached / -31.7%','7.2 mo / 58.6%','3.0 mo / 145.9%']], [182,115,115,116])
    b.para('Net capacity is the economic value of freed time. Cash savings require a documented reduction in spending. Payback assumes even monthly benefit from launch. The model uses undiscounted dollars and excludes any personal Google AI Pro credits. Recalculate using business.py and the full-precision cost_model.csv.',9.5)
    b.page('Data and governance','What the team can trust')
    b.para('Every supplied teammate CSV was compared against a fresh build from Bronze at its declared grain. All 1,613 alert rows, 1,500 disputes, 12 rules, 12 rule summaries and the overall summary matched in every exported column. The handoff omitted the database, note text and transaction history needed for tools. The local warehouse supplies those missing inputs.')
    b.sub('Quarantine has a return path')
    b.para('The first ISO-only parser failed on a local clock. An explicit month/day/year parser now retains the raw clock and normalizes 9,376 rows without guessing the timezone. Of these, 1,470 also carry BRANCH in the merchant field and are classified as deposit locations. All 45 conflicting wire narratives return as attributed evidence with a conflict flag. The ledger reconciles 10,891 treatments across 9,421 distinct records.')
    b.para('All 31,254 transactions, 425 notes and 1,613 alerts survive. Only 425 alerts have notes. For the 1,188 without one, the draft discloses the absence. A single alert remains one fact even when notes or disputes fan out. The 210 filings on 75 repeated transaction IDs remain separate disputes. Deadline flags use the teammate’s stated September 6, 2026 snapshot.')
    b.sub('Where AI belongs in the work')
    b.table([['Task and maturity assessment','Approach and accountability'],['Established: keys, money, dates and KPI definitions','Deterministic rules in Silver and Gold. Romit owns corrections. Porter reconciles dashboard numerators and denominators to Bronze.'],['Growing: evidence collection and drafting','Agent plans bounded read-only lookups. The model chooses a supported lead and follow-up. Tommy owns tool scope, prompt version, regression results and escalation.'],['Early: predicting confirmed fraud','Historical dispositions label workflow. A predictive model would require validated outcomes. A human owns investigation, filings and account decisions.']], [185,343])
    b.para('Risk controls include a masked account display, exclusion of contact data, attributed untrusted text, source references, limited activity windows and separate approval storage. Named initials suit a classroom pilot. Production would require authenticated reviewers and approved retention and access policies.',9)
    b.page('Testing and economics','What the prototype demonstrated')
    test=read_csv(EVIDENCE/'test_results.csv');meters=read_csv(EVIDENCE/'local_token_runs.csv')
    avg_i=mean(int(r['input_tokens']) for r in meters);avg_o=mean(int(r['output_tokens']) for r in meters)
    b.para(f'<b>{sum(r["result"]=="PASS" for r in test)} of {len(test)} acceptance tests passed.</b> Ten local-model generations recorded real tokenizer usage. The test set includes missing notes, disputed channels, ambiguous clocks, candidate brands, signed amounts, malicious note text, blocked requests, tool failure, reviewer decisions and duplicate approval.')
    b.table([['Observed failure or boundary','Correction and verification'],['ISO-only parsing stopped on the first local clock.','Add an explicit format, retain raw values, replay the feed and verify all 9,376 repaired rows by transaction ID.'],['A stricter conflict gate changed the double-approval error.','Check the pending state before validating the reviewer comment. Regression test now checks missing initials, undocumented conflicts, edited notes and duplicate decisions.'],['A tool outage interrupted evidence retrieval.','Inject failure in an isolated test. Confirm Failed status, an empty proposal and no approval.'],['A note instructed the agent to approve.','Synthetic note stayed in an in-memory test copy. The note was quoted, excluded from the model prompt and the draft stayed Pending.']], [190,338])
    b.sub('Measured local inference')
    b.para(f'Ten runs averaged <b>{avg_i:.1f} input and {avg_o:.1f} output tokens</b>. At 2,419.5 expected runs/year and one run per assisted case, that projects to approximately {round((avg_i+avg_o)*2419.5/12):,} tokens/month and {round((avg_i+avg_o)*2419.5):,}/year. The local provider charge is $0 per run, $0/month and $0/year. Compute, maintenance and staff effort are included separately. Repeated drafts would increase token use.')
    b.para('Gemini is available as an optional adapter. The free-tier project was visible in AI Studio. Automatic approval review blocked the external case-derived prompt. No billable or free Gemini completion was observed. Google AI Pro currently includes eligible monthly Cloud credits through the Developer Program; personal credits are outside the bank forecast.')
    b.para('Sources: evidence/test_results.csv, local_token_runs.csv and example_run.json. Each application run records the model, prompt version, exact input and selection, tools, elapsed machine time and reviewer outcome when supplied.',9)
    b.page('Demo and learning','The Agent Builder’s evidence')
    b.sub('A 95-second demonstration')
    b.table([['Time','Action and explanation'],['0–20 s','From Porter’s Workload page, open AL000029. Select Local model and Prepare draft. Explain that the request and source clock control which tools run.'],['20–50 s','Open the tool trace. Point to T0000426 and note line 11. Show the card channel, $11.68 spend and attributed wire narrative. Explain why both must survive cleaning.'],['50–75 s','Enter your initials and describe the discrepancy. Request revision. Reopen the run in Review history to show the recorded decision.'],['75–95 s','Return to Business case. Separate model seconds from paid reviewer minutes. Show the base payback and the downside if the pilot saves only two minutes.']], [73,455])
    b.sub('Project lessons to personalize after rehearsal')
    b.para('<b>Evidence can disagree even when joins are correct.</b> The audit found zero export mismatches. Reading note text beside the linked channel exposed 45 conflicts. Explain which record you checked yourself and what wording you would accept.')
    b.para('<b>A passing query can still answer the wrong question.</b> Treating a local time as UTC would create a convincing but unsupported activity window. Demonstrate AL000001 and explain why a withheld comparison is useful to an analyst.')
    b.para('<b>Fast generation is only one part of the cost.</b> Most modeled run cost is analyst review. Time a manual and an assisted case, including corrections, and reflect on which step actually changed. Record what you observed in your own words.')
    b.sub('Remaining team evidence')
    b.para('Collect paired human timings on a mix of alerts, check note quality by rule and channel, validate wages and adoption with Samuel, and rehearse the strictly timed seven-minute pitch. Record individual contributions and any later AI-assisted edits. The pilot dashboard deliberately shows Pending until real pairs exist.')
    b.para('The prompt pack, AI log, stakeholder message and runnable instructions accompany this brief. The separate architecture sheet shows the source-to-approval flow.',9)
    from xml.sax.saxutils import escape
    import json
    b.page('Design and controls','Agent specification and AI map')
    b.para('The fraud analyst supplies an alert ID and an approved request. The agent returns a proposed note with transaction evidence, source identifiers, supported indicators, known limitations and a next step. A reviewer can edit the text, approve it or request revision. No account or filing action is available.')
    b.table([['Task','Technique and layer','Reason'],['Parse, reconcile and quarantine','Rules in Bronze intake and Silver','Schema, clock format and foreign keys have repeatable tests.'],['Workload and pilot metrics','Rules in Gold and application log','Agreed grains and denominators keep results reproducible.'],['Gather evidence','Policy-based agent in Python','Request, account scope and source clock determine which tools run.'],['Draft language','Constrained GenAI in the model layer','Select a lead and follow-up from fact-supported choices. Required limitations and amounts are inserted by deterministic code.'],['Predict fraud','ML deferred','An independent outcome label would be required before validating a classifier.'],['Accept a case note','Human analyst in Next.js','The separate application log preserves the original, edited note, decision, reviewer and time.']], [122,166,240])
    b.sub('Tool contract')
    b.para('get_alert_context validates a canonical ID and returns the linked transaction and masked account context. get_notes retrieves up to ten attributed notes. get_account_activity accepts only the linked account and up to twenty UTC records from the seven days ending at the flagged transaction. calculate_case_indicators totals card spend on the returned sample. An explicit dispute request retrieves each linked dispute separately. submit_draft_for_review records a pending proposal.')
    b.sub('Accountability and bias')
    b.para('Tommy owns failures in tool selection, prompts and source fidelity. Romit owns corrective rules and source disputes. Porter verifies dashboard statistics. Samuel owns the assumptions and financial interpretation. The analyst owns each accepted note; the fraud operations manager owns pilot continuation. R07 dominates volume. Sample across rules, segments, channels and missing-note cases; compare unsupported claims and correction rates before expansion. Never infer fraud from historical workflow dispositions.',9.6)
    b.page('Appendix A','Dashboard definitions and reconciliation')
    b.table([['Measure','Independent Bronze check','Whole sample'],['Alert count','Count distinct alert_id in alerts.csv','1,613'],['False positive share','1,457 recorded False positive ÷ 1,613 alerts','90.3%'],['Total historical hours','53,108 recorded analyst minutes ÷ 60','885.1 h'],['Minutes per alert','53,108 ÷ 1,613 alerts','32.9 min'],['Note coverage','425 distinct alert IDs in analyst_notes.jsonl ÷ 1,613','26.3%'],['Pilot time saved','Mean of paired manual minus assisted minutes, including review; effective denominator is completed matching observations','Pending at build verification']], [110,283,135])
    b.para('Dashboard checks compare counts, false-positive numerators, note numerators and total minutes by month and rule directly with Bronze. The displayed percentages and hours use those controls. The handoff comparison covers all 18 alert fields, 14 dispute fields, 2 rule fields, 7 rule-summary fields and 5 overall metrics.')
    b.sub('Layer reconciliation')
    counts=read_csv(EVIDENCE/'layer_counts.csv')
    b.table([['Source','Bronze rows','Published rows','Distinct rows reprocessed']]+[[r['source'],f"{int(r['bronze']):,}",f"{int(r['published']):,}",f"{int(r['distinct_rows_reprocessed']):,}"] for r in counts],[130,103,120,175])
    b.para('Fact alert grain is one alert_id. Fact dispute grain is one dispute_id. Keep note rows separate and use existence tests for coverage. Key paths run from alert to transaction and account, account to customer segment, and alert to rule and month. Open-overdue disputes use a strict due-date-before-snapshot comparison. The September snapshot is a documented secondary analysis.',9.5)
    rows=read_csv(EVIDENCE/'quality_log.csv')
    for i in range(2):
        b.page('Appendix B','Quantified data quality findings'+(' continued' if i else ''))
        b.para('Affected counts are per issue. A row can appear in several checks. The independent layer reconciliation counts distinct source records.')
        for r in rows[5*i:5*i+5]:
            b.sub(r['finding'])
            b.para('<b>'+escape(r['source'])+' · '+f"{int(r['affected_rows']):,}"+' affected.</b> '+escape(r['detection'])+'. '+escape(r['processing_rule'])+' '+escape(r['impact']),9.8)
    results=read_csv(EVIDENCE/'test_results.csv')
    for i in range(2):
        b.page('Appendix C','Agent acceptance tests'+(' continued' if i else ''))
        b.para('Tests use real alert data. Malicious text, simulated tool failure and reviewer actions use isolated test fixtures. Recorded outcomes below come from verify.py.')
        b.table([['Case and record','Expected behavior','Observed result']]+[[escape(r['test'])+'<br/>'+escape(r['record']),escape(r['expected']),'<b>'+r['result']+'</b> · '+escape(r['observed'])] for r in results[10*i:10*i+10]],[130,139,259])
    b.page('Appendix D','Production prompt and checked output')
    example=json.loads((EVIDENCE/'example_run.json').read_text(encoding='utf-8'))
    u=example['usage'];b.para('The production model receives the role, constraints, context and output format below. Approved sentences vary by evidence. All transaction values and required limitations stay under deterministic control.')
    b.sub('Actual model input')
    b.para(escape(u['prompt']).replace('\n','<br/>'),9.6)
    b.sub('Actual model output')
    b.para(escape(json.dumps(u['output_json'])),9.6)
    b.para(f"Model {u['model']}. Prompt {u['prompt_version']}. Provider reported {u['input']} input tokens and {u['output']} output tokens. The model's two selected strings were validated against the allowed values. T0000426 and note line 11 support the conflict flag. The complete output remained Pending.")
    b.sub('Checked stakeholder message')
    b.para('To the fraud operations manager: The six-month sample contains 1,613 alerts and 885.1 hours of recorded analyst work. We request $6,040 for a limited preparation pilot under the base staffing assumptions. We will compare manual and assisted preparation on the same alerts, including analyst review and corrections. The pilot must release about 2.56 minutes per assisted case to break even over three years.')
    b.para('Checks: alert counts and minutes from Bronze; threshold and ask from business.py. Measured time savings and prevented fraud losses were excluded from the message.',9)
    b.page('Appendix E','AI assistance and review evidence')
    b.table([['Prompt or request','Output and verification','Change made'],['Read the non-draft material and check the teammate data.','Compared five CSVs by record key and numerical value. Rebuilt missing keyed evidence from six sources.','Kept matched exports; added raw note and transaction fields for tools.'],['Cleanse and process quarantined records.','Tested ISO parsing; checked all intake keys against the recovery ledger and Silver values.','Added local-clock parser, branch classification and note conflict status.'],['Fix issues and show the app, costs and learning.','Tested reviewer decisions, machine usage and financial scenarios. A conflict check initially masked the repeat-decision error.','Corrected validation order. Model cost, staff review and support remain separate.'],['Use Google AI Pro or Gemini when useful.','Confirmed free-tier project. External case prompt blocked by automatic review.','Used ten successful local generations for token economics.'],['Build a Next.js and daisyUI web app; use existing npm packages.','Built App Router pages with daisyUI, Recharts and Lucide. Checked live case preparation in Edge.','Added a separate dashboard endpoint for Porter and fixed the extension-triggered hydration warning.'],['Only AL000029 is apparent; check the app yourself.','Added full alert browser and verified last-page access, searches, filters and both reviewer outcomes.','Linked case selection, preserved QA initials, and kept synthetic timings out of the pilot metric.']], [145,207,176])
    b.para('Team completion evidence: the local model, dashboard and case review work at the supplied scale. At verification, the 12 web checks passed. Paired human timings, individual reflections, the live seven-minute delivery and later individual teammate evaluations remain with the team. Sources: course brief and rubric, platform guide, submitted outline, Northgate dictionaries, Bronze manifest, teammate CSVs, test and cost artifacts.',9.6)
    b.c.save()
    from pypdf import PdfWriter
    from io import BytesIO
    merged=PdfWriter()
    merged.append(str(ROOT/'Funding brief.pdf'));merged.append(str(ROOT/'Architecture.pdf'))
    out=BytesIO();merged.write(out);merged.close()
    (ROOT/'Funding brief.pdf').write_bytes(out.getvalue())


def pitch_pdf():
    import json
    slides=json.loads((ROOT/'web/app/pitch/slides.json').read_text(encoding='utf-8'))
    c=canvas.Canvas(str(ROOT/'Team presentation.pdf'),pagesize=(960,540))
    c.setTitle('Northgate alert preparation pilot')
    sources=['Pilot staffing assumptions in business.py.','Bronze reconciliation and quarantine_history.',
        'Bronze alerts.csv and Gold workload by rule.','Bronze transaction T0000426 and analyst note line 11.',
        'Three-year scenario model in evidence/cost_model.csv.','Base-case break-even and 20 acceptance checks in evidence/test_results.csv.']
    for i,s in enumerate(slides):
        rect(c,0,0,960,540,'#f5f7f2');rect(c,0,0,14,540,green)
        write(c,52,492,'NORTHGATE BANK    /    FRAUD OPERATIONS',13,'Helvetica-Bold',green)
        write(c,52,451,s['owner'],14,'Helvetica',muted)
        write(c,52,383,s['title'],34,'Times-Bold')
        write(c,52,291,s['value'],66,'Times-Roman',green)
        y=230
        for text in simpleSplit(s['text'],'Helvetica',21,838):
            write(c,52,y,text,21);y-=30
        if 'link' in s:
            write(c,52,77,s['label'],14,'Helvetica-Bold',green)
            c.linkURL('http://127.0.0.1:3301'+s['link'],(52,71,405,93),relative=0)
        write(c,52,34,sources[i],10,'Helvetica',muted);write(c,873,34,f'{i+1} / {len(slides)}',10)
        c.showPage()
    c.save()

if __name__=='__main__':arch();report();pitch_pdf()

