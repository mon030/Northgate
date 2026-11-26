"""Constrained drafting. Cloud calls receive only candidate sentences and evidence flags."""
import atexit
import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from build import ROOT

PROMPT_VERSION='case-review-1.0'
INSTRUCTION=('You are a fraud operations case preparation assistant. Choose a review lead from the supplied '
             'sentences and a follow-up from the permitted options. Prioritize contradictions and missing '
             'evidence. You prepare a proposal for an analyst. Return only the requested JSON object.')
MODEL='SmolLM2-360M-Instruct-Q8_0'
LOCAL='Local model'
GEMINI='Gemini API'
RULES='Rules only'
_worker=None
_local_url=None
_secret=None
session_gemini_key=None

def request_json(url, body, headers, timeout=45):
    request=Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json',**headers})
    try:
        with urlopen(request,timeout=timeout) as response: return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f'Model service returned HTTP {error.code}. Check model access and try again.') from None

def stop():
    global _worker
    if _worker and _worker.poll() is None:
        _worker.terminate()
        try: _worker.wait(5)
        except subprocess.TimeoutExpired: _worker.kill()
    _worker=None

atexit.register(stop)

def local_service():
    global _worker,_secret,_local_url
    if _worker and _worker.poll() is None: return _local_url
    exe=ROOT/'runtime/llama/llama-server.exe'
    model=ROOT/'runtime/model.gguf'
    if not exe.exists() or not model.exists(): raise ValueError('Local model missing. On Windows x64, run python setup_model.py from the project root, or select Rules only.')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    _secret=secrets.token_urlsafe(24)
    _local_url=f'http://127.0.0.1:{port}'
    _worker=subprocess.Popen([str(exe),'-m',str(model),'--host','127.0.0.1','--port',str(port),
        '--api-key',_secret,'-c','2048','-t','4','-np','1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    for _ in range(150):
        try:
            with urlopen(_local_url+'/health',timeout=1) as response:
                if response.status==200: return _local_url
        except (OSError,URLError): pass
        if _worker.poll() is not None: break
        time.sleep(.2)
    stop()
    raise RuntimeError('Local model could not start. Select Rules only for a deterministic demonstration.')

def draft(mode,leads,actions):
    instruction = os.getenv('NORTHGATE_AGENT_PROMPT', '').strip() or INSTRUCTION
    version = PROMPT_VERSION
    if instruction != INSTRUCTION:
        instruction += ('\nReturn a JSON object with lead and follow_up. Choose lead verbatim from '
                        'review_leads and follow_up verbatim from follow_ups. A human reviews the proposal.')
        version += '+' + hashlib.sha256(instruction.encode('utf-8')).hexdigest()[:12]
    prompt=instruction+'\n'+json.dumps({'review_leads':leads,'follow_ups':actions},ensure_ascii=True)
    schema={'type':'object','properties':{'lead':{'type':'string','enum':leads},'follow_up':{'type':'string','enum':actions}},
            'required':['lead','follow_up']}
    if mode==RULES:
        result={'lead':leads[0],'follow_up':actions[0]}
        model='fixed rules'; usage={'input':0,'output':0,'usd_api':0}
    elif mode==LOCAL:
        base=local_service()
        payload={'messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':160,
                 'response_format':{'type':'json_schema','json_schema':{'name':'draft','schema':schema}}}
        response=request_json(base+'/v1/chat/completions',payload,{'Authorization':'Bearer '+_secret})
        result=json.loads(response['choices'][0]['message']['content'])
        model=MODEL; u=response['usage'];usage={'input':u['prompt_tokens'],'output':u['completion_tokens'],'usd_api':0}
    elif mode==GEMINI:
        key=session_gemini_key or os.getenv('GEMINI_API_KEY')
        model=os.getenv('GEMINI_MODEL','').strip() or 'gemini-3.8-flash'
        if not key: raise ValueError('Gemini requires GEMINI_API_KEY in the launch environment. Local model is available.')
        if not re.fullmatch(r'[a-zA-Z0-9.\-]+',model): raise ValueError('Invalid Gemini model ID.')
        body={'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json','responseJsonSchema':schema}}
        response=request_json('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',body,{'x-goog-api-key':key})
        result=json.loads(''.join(p.get('text','') for p in response['candidates'][0]['content']['parts'] if not p.get('thought')))
        u=response['usageMetadata'];usage={'input':u['promptTokenCount'],'output':u.get('candidatesTokenCount',0),'thoughts':u.get('thoughtsTokenCount',0),'provider_usage':u,'usd_api':None}
        model=response.get('modelVersion',model)
    else: raise ValueError('Unsupported model selection.')
    if result.get('lead') not in leads or result.get('follow_up') not in actions: raise ValueError('Model returned unsupported wording. Draft withheld.')
    return result,{'provider':mode,'model':model,'prompt_version':version,'prompt':prompt,'output_json':result,**usage}

