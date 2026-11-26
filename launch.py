"""Start the local Next.js app and open the demo in the default browser."""
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from urllib.request import urlopen
from build import ROOT, DB, build
URL='http://127.0.0.1:3301/dashboard'
def live():
    try:
        with urlopen('http://127.0.0.1:3301/api/dashboard',timeout=3) as r:return b'pilot_pairs' in r.read()
    except OSError:return False
def open_when_ready():
    for _ in range(80):
        if live():webbrowser.open(URL);return
        time.sleep(1)
if __name__=='__main__':
    if live():webbrowser.open(URL);sys.exit(0)
    if not DB.exists():build()
    web=ROOT/'web'; npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    if not npm:sys.exit('Install Node.js 22.12+ and reopen the launcher.')
    if not (web/'node_modules/next').exists():subprocess.run([npm,'ci','--no-audit','--no-fund'],cwd=web,check=True)
    threading.Thread(target=open_when_ready,daemon=True).start()
    sys.exit(subprocess.call([npm,'run','dev'],cwd=web,env={**os.environ,'NEXT_TELEMETRY_DISABLED':'1','NORTHGATE_PYTHON':sys.executable}))

