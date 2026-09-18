"""Broad source-dependent engineering fixtures, not an independent customer holdout."""
import hashlib
import json
from pathlib import Path
import random


def build(seed=918204):
    rng=random.Random(seed);cases=[]
    def add(family,v,prompt,resources,answer,kind='answer',extra=None,phases=None):
        task={'id':f'{family}-{v:02}','family':family,'kind':kind,'phases':phases or [{'prompt':prompt,'resources':resources,'expected':answer}],'provenance':'Original generated fixture, MIT; same operator as candidate. Broad engineering test, not independent customer evidence.'}
        if extra:task.update(extra)
        task['sha256']=hashlib.sha256(json.dumps(task,sort_keys=True).encode()).hexdigest();cases.append(task)
    for v in range(3):
        records=[{'transaction_id':f'T-{rng.randrange(100000,999999)}','customer_id':f'C-{i%17}','amount_cents':rng.randrange(-9999,15000),'status':'void' if i%11==0 else 'settled','region':'north' if i%2 else 'south'} for i in range(180)]
        records += [dict(records[23]),dict(records[81])]
        chosen=f'C-{rng.randrange(17)}';subset=[r for r in records if r['customer_id']==chosen and r['status']=='settled']
        add('structured_aggregation',v,f'For customer {chosen}, give count and sum_cents over settled transactions only. Duplicate rows count separately. Return {{"answer":{{"count":N,"sum_cents":N}}}}.',{'ledger.json':json.dumps(records,indent=2)},{'count':len(subset),'sum_cents':sum(r['amount_cents'] for r in subset)})
        target=records[rng.randrange(100,170)]['transaction_id'];matches=[r for r in records if r['transaction_id']==target]
        add('structured_lookup',v,f'Return every complete record with transaction_id {target} as an array in answer. Preserve nulls, signs and duplicate rows.',{'records.json':json.dumps(records,indent=2)},matches)
        docs=[]
        for i in range(35):
            docs.append({'url':f'https://fixture.invalid/policy/{v}/{i}','title':f'Engineering service bulletin {i}','updated':f'2026-08-{i%28+1:02}','region':'west' if i%3 else 'east','retry_limit':rng.randrange(1,12),'snippet':'This published bulletin concerns the service deployment and retry configuration. '+('Background: deployments are reviewed by the operations team. '*8)})
        latest=max((d for d in docs if d['region']=='east'),key=lambda d:d['updated'])
        add('search_evidence',v,'From the search results, identify the most recently updated east-region bulletin. Return answer with url and retry_limit. Use the updated date, not list order.',{'search_results.json':json.dumps(docs,indent=2)},{'url':latest['url'],'retry_limit':latest['retry_limit']})
        limit=rng.randrange(100,900);old=limit+rng.randrange(10,80);identifier=f'POL-{rng.randrange(10000,99999)}'
        sections=[f'# Archive notice\nSource: archive-{v}\nStatus: superseded\nPolicy {identifier} previously allowed {old} requests.\n']
        sections += [f'# Background source {i}\nSource: background-{v}-{i}\n'+('The service runs in several regions. Operators review all changes before deployment. '*30) for i in range(5)]
        sections.insert(3,f'# Final signed decision\nSource: decision-{v}\nStatus: effective\nPolicy {identifier} now allows {limit} requests. The archive value is superseded. The exception applies only to region north; south keeps the current default.\n')
        add('research_conflicts',v,f'What is the effective request limit for policy {identifier}, and which region has the exception? Return answer with limit, region and source. Cite the effective source ID, not the archive.',{'sources.md':'\n'.join(sections)},{'limit':limit,'region':'north','source':f'decision-{v}'})
        service=f'service-{rng.randrange(1000,9999)}';code=f'E{rng.randrange(100,999)}';shard=rng.randrange(50)
        lines=[f'INFO heartbeat worker={i%5} cycle={i} completed successfully' for i in range(320)]
        lines[137]=f'ERROR root_cause service={service} code={code} shard={shard}; retries failed'
        add('log_diagnosis',v,'Find the recorded root cause. Return answer with service, code and shard as an integer.',{'run.log':'\n'.join(lines)},{'service':service,'code':code,'shard':shard})
        n=rng.randrange(180,330);m=rng.randrange(50,100);raw='INFO heartbeat healthy\n'*n+'WARN queue delay\n'+'INFO heartbeat healthy\n'*m+'ERROR stop\n'
        add('log_exact_count',v,'Count every INFO heartbeat line and every WARN line. Return answer with heartbeats and warnings. Repeated identical lines count separately.',{'events.log':raw},{'heartbeats':n+m,'warnings':1})
        mapping={f'item_{rng.randrange(10000,99999)}':rng.randrange(-999,999) for _ in range(7)}
        logs=('INFO helper ready\n'*150)+'\n'.join(f'FAIL resolve({key!r}): expected {value}, observed 0' for key,value in mapping.items())
        extra={'private':{'fn':'resolve','cases':[([k],n) for k,n in mapping.items()]+[(['missing'],None)],'oracle':'def resolve(key):\n    return '+repr(mapping)+'.get(key)\n'},'category':'debugging'}
        add('code_repair',v,'Repair resolve(key) using all expected mappings in test.log. Return None for unknown keys. Return {"code":"complete Python module"}.',{'app.py':'def resolve(key):\n    return 0\n','test.log':logs},None,kind='code',extra=extra)
        wrong={rng.randrange(4,12),rng.randrange(16,24)};source=[]
        for i in range(30):source.append(f'def add_{i}(a, b):\n    """Return a plus b."""\n    return a {"-" if i in wrong else "+"} b\n')
        add('code_review',v,'Identify every function violating its documented contract. Return answer as a sorted array of function names, with no correct functions included.',{'module.py':'\n'.join(source)},sorted(f'add_{i}' for i in wrong))
        color=rng.choice(['teal','amber','violet']);place=f'zone-{rng.randrange(100,999)}';budget=rng.randrange(1000,9999)
        history=[{'role':'user','content':f'For my project, the region is {place}, the budget is {budget}, and my color preference is red.'},{'role':'assistant','content':'Recorded your project preferences.'}]
        for i in range(18):history.extend([{'role':'user','content':f'Note {i}: the project team meets regularly to discuss progress.'},{'role':'assistant','content':'Acknowledged. '+('The next project review will cover progress and open questions. '*12)}])
        history.extend([{'role':'user','content':f'Correction: replace my red preference with {color}. Region and budget remain unchanged.'},{'role':'assistant','content':'I have recorded that correction.'}])
        add('long_conversation',v,'Return my current project preferences as answer with region, budget (integer) and color.',{}, {'region':place,'budget':budget,'color':color},extra={'history':history})
        count=rng.randrange(500,999);delta=rng.randrange(5,60);stock=[{'warehouse':f'W-{i}','available':rng.randrange(1000),'snapshot':1} for i in range(110)];stock[47]['available']=count
        updated=[dict(x) for x in stock];updated[47]['available']=count-delta
        for row in updated:row['snapshot']=2
        phases=[{'prompt':'For W-47, return answer with available and snapshot from the supplied inventory.','resources':{'inventory.json':json.dumps(stock,indent=2)},'expected':{'available':count,'snapshot':1}}, {'prompt':'The inventory tool has refreshed. For W-47, return the NEW available and snapshot. Do not reuse the earlier answer.','resources':{'inventory.json':json.dumps(updated,indent=2)},'expected':{'available':count-delta,'snapshot':2}}]
        add('session_freshness',v,'',{},None,phases=phases)
    return cases


def write_suite(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    cases=build()
    for task in cases:(directory/(task['id']+'.json')).write_text(json.dumps(task,indent=2)+'\n')
    manifest={'seed':918204,'tasks':{t['id']:t['sha256'] for t in cases},'families':sorted({t['family'] for t in cases}),'scope':'30 generated source-dependent tasks in ten families; same author, correlated variants, not real-customer or independent evidence.'}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return cases

if __name__=='__main__':print(len(write_suite('proxy-tasks')))
