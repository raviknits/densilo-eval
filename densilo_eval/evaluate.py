import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from .dataset import canonical


def parse_answer(text):
    text=text.strip()
    if text.startswith('```'):
        lines=text.splitlines();text='\n'.join(lines[1:-1])
    value=json.loads(text)
    if not isinstance(value,dict):raise ValueError('final answer must be object')
    return value


def evaluate(task, text):
    try:a=parse_answer(text)
    except Exception:return {'success':False,'reason':'invalid_final_json'}
    p=task['private'];cat=task['category']
    if cat=='structured':return {'success':canonical(a.get('answer'))==canonical(p['answer'])}
    if cat=='review':
        actual=a.get('findings',[]);expected=p['findings']
        if not isinstance(actual,list) or not all(isinstance(x,str) for x in actual):return {'success':False,'reason':'invalid_findings'}
        return {'success':sorted(actual)==sorted(expected),'true_positives':len(set(actual)&set(expected)),'false_positives':len(set(actual)-set(expected)),'false_negatives':len(set(expected)-set(actual))}
    code=a.get('code')
    if not isinstance(code,str):return {'success':False,'reason':'missing_code'}
    worker=str(Path(__file__).with_name('grade_worker.py'));cmd=[str(Path(sys.executable).resolve()),'-I',worker]
    if platform.system()=='Darwin':
        # No access to home, credentials, other fixtures, network or writable files.
        profile='(version 1)(allow default)(deny network*)(deny file-write*)(deny file-read* (subpath "/Users"))(allow file-read* (subpath '+json.dumps(str(Path(sys.executable).parent.parent))+'))'
        cmd=['/usr/bin/sandbox-exec','-p',profile]+cmd
    else:
        # Linux must be run inside the documented no-network container.
        if os.environ.get('CONTEXTBENCH_CONTAINER')!='1':return {'success':False,'reason':'sandbox_unavailable','invalid':True}
    try:
        r=subprocess.run(cmd,input=json.dumps({'code':code,'fn':p['fn'],'cases':p['cases']}),text=True,capture_output=True,timeout=5,env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8'})
        if r.returncode!=0:return {'success':False,'reason':'worker_failed','detail':r.stderr[:180]}
        return json.loads(r.stdout)
    except subprocess.TimeoutExpired:return {'success':False,'reason':'timeout'}
