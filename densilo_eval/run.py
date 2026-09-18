"""Run paired development fixtures through already-running full proxies."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,random
from pathlib import Path
from . import driver

def main():
 p=argparse.ArgumentParser();p.add_argument('--ports',required=True);p.add_argument('--auth',choices=['codex','api'],required=True);p.add_argument('--model',required=True);p.add_argument('--output',required=True);p.add_argument('--repeats',type=int,default=1);a=p.parse_args()
 ports=json.loads(a.ports)
 if not {'native','candidate'}<=set(ports) or any(type(v) is not int or not 1024<=v<=65535 for v in ports.values()) or len(set(ports.values()))!=len(ports):raise ValueError('Distinct local full-proxy ports required')
 driver.PORTS=ports;driver.MODEL=a.model;driver.AUTH=a.auth
 root=Path(a.output);root.mkdir(parents=True,exist_ok=False)
 manifest=json.loads(Path('manifest.json').read_text());tasks=[]
 for item in manifest['tasks']:
  raw=Path(item['path']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Fixture checksum changed')
  if not item['id'].endswith('-00'):tasks.append(json.loads(raw))
 record={'dataset':manifest,'arms':ports,'model':a.model,'auth':a.auth,'repeats':a.repeats,'same_family_development_only':True,'provider_dollar_savings_established':False,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('densilo_eval').glob('*.py')}}
 (root/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
 jobs=[(t,r) for r in range(a.repeats) for t in tasks];random.Random(918519).shuffle(jobs)
 def run(arm):
  for task,repeat in jobs:print(*driver.run_one(task,arm,repeat,root),flush=True)
 with ThreadPoolExecutor(max_workers=len(ports)) as workers:list(workers.map(run,ports))

if __name__=='__main__':main()
