"""Northgate Bank desktop case preparation workbench. Python standard library only."""
import json
import math
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import agent
import models
from build import DB, METRICS as MEASURES
from business import scenarios

class Workbench:
    def __init__(self,root):
        self.root=root
        root.title('Northgate | Alert case preparation')
        root.geometry('1040x765'); root.minsize(860,620)
        root.configure(bg='#132f3b')
        self.db=agent.connect_data(); self.log=agent.app_log()
        self.events=queue.Queue(); self.current=None
        style=ttk.Style(); style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10))
        style.configure('TFrame',background='#f5f6f2')
        style.configure('TLabel',background='#f5f6f2',foreground='#16313b')
        style.configure('Title.TLabel',font=('Georgia',18,'bold'))
        style.configure('Primary.TButton',background='#006253',foreground='white',padding=(12,7))
        style.map('Primary.TButton',background=[('active','#004b40')])
        style.configure('TNotebook.Tab',padding=(18,8))
        header=tk.Frame(root,bg='#132f3b');header.pack(fill='x')
        tk.Label(header,text='Northgate Bank',font=('Georgia',20,'bold'),bg='#132f3b',fg='white').pack(side='left',padx=20,pady=12)
        tk.Label(header,text='Fraud operations  /  Analyst workspace',bg='#132f3b',fg='#c6dcd4',font=('Segoe UI',11)).pack(side='left')
        self.tabs=ttk.Notebook(root);self.tabs.pack(fill='both',expand=True,padx=12,pady=(0,12))
        self.case=self.page('Case preparation');self.dash=self.page('Workload');self.cost=self.page('Business case');self.history=self.page('Review history')
        self.case_page(); self.dashboard(); self.cost_page();self.history_page()
        self.tabs.bind('<<NotebookTabChanged>>',lambda _: (self.refresh_history(),self.refresh_dashboard()))
    def page(self,name):
        frame=ttk.Frame(self.tabs,padding=13);self.tabs.add(frame,text=name);return frame
    def field(self,parent,label,values=None,width=16,default=''):
        frame=ttk.Frame(parent);frame.pack(side='left',padx=(0,10))
        ttk.Label(frame,text=label).pack(anchor='w')
        var=tk.StringVar(value=default)
        w=ttk.Combobox(frame,values=values,textvariable=var,state='readonly',width=width) if values else ttk.Entry(frame,textvariable=var,width=width)
        w.pack();return var,w
    def case_page(self):
        controls=ttk.Frame(self.case);controls.pack(fill='x')
        self.alert,_=self.field(controls,'Alert ID',width=12,default='AL000029')
        self.intent,_=self.field(controls,'Analyst request',agent.REQUESTS,25,agent.REQUESTS[0])
        self.mode,_=self.field(controls,'Drafting engine',[models.LOCAL,models.GEMINI,models.RULES],14,models.LOCAL)
        self.go=ttk.Button(controls,text='Prepare draft',command=self.prepare,style='Primary.TButton');self.go.pack(side='left',padx=4,pady=(14,0))
        self.connect=ttk.Button(controls,text='Connect Gemini',command=self.gemini);self.connect.pack(side='left',padx=4,pady=(14,0))
        self.status=tk.StringVar(value='Ready. Enter an alert ID to gather case evidence.')
        ttk.Label(self.case,textvariable=self.status,wraplength=900).pack(anchor='w',pady=8)
        self.draftbox=ScrolledText(self.case,wrap='word',font=('Segoe UI',11),height=10,padx=12,pady=10,foreground='#193640',relief='solid',bd=1)
        self.draftbox.pack(fill='both',expand=True);self.draftbox.configure(state='disabled')
        ttk.Label(self.case,text='Tool trace and token meter').pack(anchor='w',pady=(7,2))
        self.trace=ScrolledText(self.case,wrap='word',font=('Consolas',9),height=4,relief='flat',bg='#e4eeea')
        self.trace.pack(fill='x');self.trace.configure(state='disabled')
        review=ttk.Frame(self.case);review.pack(fill='x',pady=(9,0))
        self.reviewer,_=self.field(review,'Reviewer initials',width=12)
        self.comment,_=self.field(review,'Correction or review comment',width=32)
        self.approve=ttk.Button(review,text='Approve note',command=lambda:self.review('Approved'));self.approve.pack(side='left',pady=(17,0))
        self.revise=ttk.Button(review,text='Request revision',command=lambda:self.review('Revision requested'));self.revise.pack(side='left',padx=5,pady=(17,0))
        self.pilot=ttk.Button(review,text='Log paired timing',command=self.record_pilot);self.pilot.pack(side='left',pady=(17,0))
        self.buttons('')
    def buttons(self,status):
        for b in [self.approve,self.revise]: b.configure(state='normal' if status=='Pending' else 'disabled')
        self.pilot.configure(state='normal' if status=='Approved' else 'disabled')
    def gemini(self):
        key=simpledialog.askstring('Connect Gemini','Paste an API key from your confirmed free-tier project.\nThe key is held only for this app session.',show='*',parent=self.root)
        if key and key.strip():
            models.session_gemini_key=key.strip()
            self.mode.set(models.GEMINI);self.status.set('Gemini selected. Only generic review wording is sent to Google.')
    def prepare(self):
        if self.mode.get()==models.GEMINI and not (models.session_gemini_key or os.getenv('GEMINI_API_KEY')):
            self.gemini()
            if not models.session_gemini_key:return
        args=(self.alert.get(),self.intent.get(),self.mode.get())
        self.current=None;self.buttons('');self.go.configure(state='disabled')
        self.show_text(self.draftbox,'');self.show_text(self.trace,'')
        self.status.set('Retrieving evidence and preparing a proposal…')
        def run():
            db=agent.connect_data(); log=agent.app_log()
            try:self.events.put((agent.prepare(db,log,*args),None))
            except Exception as e:self.events.put((None,str(e)))
            finally:db.close();log.close()
        threading.Thread(target=run,daemon=True).start();self.root.after(100,self.poll)
    def poll(self):
        if self.events.empty():self.root.after(100,self.poll);return
        run,error=self.events.get();self.go.configure(state='normal')
        if error:self.status.set('Draft withheld. '+error);return
        self.load_run(run)
    def show_text(self,w,txt,editable=False):
        w.configure(state='normal');w.delete('1.0','end');w.insert('1.0',txt);w.configure(state='normal' if editable else 'disabled')
    def load_run(self,run):
        r=self.log.execute('SELECT * FROM runs WHERE id=?',(run,)).fetchone()
        self.current=run;self.alert.set(r['alert']);self.intent.set(r['request']);self.comment.set('')
        usage=json.loads(r['usage']);self.mode.set(usage['provider'])
        decision=self.log.execute('SELECT * FROM decisions WHERE run_id=?',(run,)).fetchone()
        body=decision['final_text'] if decision and decision['decision']=='Approved' else r['draft']
        self.show_text(self.draftbox,body,r['status']=='Pending')
        meter=f"{usage.get('model',usage['provider'])}  |  input {usage.get('input','?')}  |  output {usage.get('output','?')}  |  {r['elapsed']:.2f} seconds"
        self.show_text(self.trace,'\n'.join(json.loads(r['trace']))+'\n'+meter)
        self.status.set(f"Run {run} · {r['status']}"+(f" · {decision['reviewer']} · {decision['comment']}" if decision else ''))
        self.buttons(r['status']);self.tabs.select(self.case)
    def review(self,decision):
        try:agent.decide(self.log,self.current,self.reviewer.get(),decision,self.comment.get(),self.draftbox.get('1.0','end'))
        except ValueError as e:messagebox.showinfo('Review',str(e));return
        self.load_run(self.current)
    def record_pilot(self):
        if self.log.execute('SELECT 1 FROM pilot WHERE run_id=?',(self.current,)).fetchone():messagebox.showinfo('Timing','This run already has paired timings.');return
        values=[]
        for title in ['Manual preparation on this same alert','Assisted preparation including human review']:
            v=simpledialog.askfloat('Paired case timing',title+' (measured minutes)',minvalue=.001,parent=self.root)
            if v is None:return
            if not math.isfinite(v):return
            values.append(v)
        with self.log:self.log.execute('INSERT INTO pilot VALUES(?,?,?)',(self.current,*values))
        self.status.set('Paired human timings recorded. Workload now includes this observation.')
    def dashboard(self):
        ttk.Label(self.dash,text='Alert workload',style='Title.TLabel').pack(anchor='w')
        filters=ttk.Frame(self.dash);filters.pack(anchor='w',pady=10)
        self.filters=[]
        for label,col in [('Alert month','alert_month'),('Rule code','rule_id')]:
            vals=['All']+[r[0] for r in self.db.execute(f'SELECT DISTINCT {col} FROM fact_alert ORDER BY 1')]
            v,w=self.field(filters,label,vals,13,'All');self.filters.append(v);w.bind('<<ComboboxSelected>>',lambda _:self.refresh_dashboard())
        self.metrics=ttk.Label(self.dash,font=('Segoe UI',12),wraplength=850,justify='left');self.metrics.pack(anchor='w',pady=7)
        self.rules=self.table(self.dash,['Rule','Alerts','Hours','Minutes per alert','False positive %','Note coverage %'])
    def table(self,parent,cols):
        tree=ttk.Treeview(parent,columns=cols,show='headings',height=12)
        for col in cols: tree.heading(col,text=col);tree.column(col,width=105,anchor='center',stretch=True)
        tree.pack(fill='both',expand=True,pady=8);return tree
    def refresh_dashboard(self):
        month,rule=[v.get() for v in self.filters]; args=(month,month,rule,rule)
        where=" FROM fact_alert WHERE (?='All' OR alert_month=?) AND (?='All' OR rule_id=?)"
        row=self.db.execute('SELECT '+MEASURES+where,args).fetchone()
        pilot=self.log.execute('SELECT r.alert,p.manual-p.assisted FROM pilot p JOIN runs r ON r.id=p.run_id').fetchall()
        allowed={r[0] for r in self.db.execute('SELECT alert_id'+where,args)}
        obs=[r[1] for r in pilot if r[0] in allowed]
        observed=f'{sum(obs)/len(obs):.1f} min ({len(obs)} pairs)' if obs else 'awaiting paired timings'
        self.metrics.configure(text=f"{row[0]:,} alerts     •     {row[1]}% recorded false positive     •     {row[2]} historical hours\n{row[3]} minutes per alert     •     {row[4]}% note coverage     •     Pilot savings: {observed}")
        self.rules.delete(*self.rules.get_children())
        for r in self.db.execute('SELECT rule_id,'+MEASURES+where+' GROUP BY rule_id ORDER BY sum(minutes_spent) DESC',args):
            self.rules.insert('','end',values=[r[0],r[1],r[3],r[4],r[2],r[5]])
    def cost_page(self):
        ttk.Label(self.cost,text='Pilot economics',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self.cost,text='Three-year capacity-value scenarios • illustrative labor and adoption assumptions',wraplength=800).pack(anchor='w',pady=8)
        tree=self.table(self.cost,['Scenario','Build + training','Annual run¹','Year 1 net²','Year 2 net²','Year 3 net²','Payback'])
        for r in scenarios():
            nums=[r[k] for k in ['annual_total_run_usd','year1_cumulative_usd','year2_cumulative_usd','year3_cumulative_usd']]
            tree.insert('','end',values=[r['scenario'],f"${(r['annual_net_capacity_usd']-r['year1_cumulative_usd']):,.0f}",*[f'${n:,.0f}' for n in nums],f"{r['payback_months']:.1f} mo" if r['payback_months'] else 'Unreached'])
        ttk.Label(self.cost,text='¹ Includes assisted analyst review, quality assurance, maintenance and compute. Local inference has zero API fees.\n² Cumulative economic value after costs. Time released becomes cash savings only if a spending line falls.\nPilot gate: compare manual and assisted work on the same alerts, including review and corrections.',wraplength=850).pack(anchor='w',pady=10)
    def history_page(self):
        ttk.Label(self.history,text='Review history',style='Title.TLabel').pack(anchor='w')
        self.runs=self.table(self.history,['Run','Alert','Created UTC','Status','Engine'])
        ttk.Button(self.history,text='Open selected run',command=self.open_selected).pack(anchor='w')
        self.runs.bind('<Double-1>',lambda _:self.open_selected())
    def refresh_history(self):
        self.runs.delete(*self.runs.get_children())
        for r in self.log.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 100'):
            self.runs.insert('','end',iid=str(r['id']),values=[r['id'],r['alert'],r['created'],r['status'],json.loads(r['usage'])['provider']])
    def open_selected(self):
        if self.runs.selection():self.load_run(int(self.runs.selection()[0]))

if __name__=='__main__':
    if not DB.exists():
        from build import build
        build()
    root=tk.Tk(); Workbench(root); root.mainloop()


