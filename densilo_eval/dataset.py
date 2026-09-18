"""Original deterministic fixtures. No downloaded repositories or private data."""
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def build_tasks():
    tasks = []
    # Split whole templates, never individual parameter variants.
    dev = {"retry", "refund", "window", "access_review", "money_review", "ledger"}
    for variant in range(5):
        rng = random.Random(20260918 + variant)
        n = variant + 3
        families = []
        families.append(dict(family="retry", category="debugging", project="telemetry",
            prompt=f"Fix app.py: attempts are zero-based; retry exactly while attempt < {n}, except never retry status 400 or 401. Return code defining should_retry(attempt, status).",
            code=f"def should_retry(attempt, status):\n    return attempt <= {n} and status not in (400, 401)\n",
            oracle=f"def should_retry(attempt, status):\n    return attempt < {n} and status not in (400, 401)\n",
            fn="should_retry", cases=[([i,s], i<n and s not in (400,401)) for i in range(n+2) for s in (200,400,401,503)],
            signal=f"ERROR retry limit exceeded: attempt={n}; expected stop, observed retry"))
        families.append(dict(family="refund", category="debugging", project="billing",
            prompt=f"Fix app.py: refund_total(rows) sums amount_cents only for status='settled' and kind='refund'. Amounts remain signed integer cents. Inspect the failure log.",
            code="def refund_total(rows):\n    return sum(r['amount_cents'] for r in rows if r['kind'] == 'refund')\n",
            oracle="def refund_total(rows):\n    return sum(r['amount_cents'] for r in rows if r['kind'] == 'refund' and r['status'] == 'settled')\n",
            fn="refund_total",cases=[([[]],0),([[{'kind':'refund','status':s,'amount_cents':v} for s,v in [('pending',999),('settled',-n),('settled',n*100)]]],n*99),([[{'kind':'sale','status':'settled','amount_cents':900}]],0)],
            signal="FAILED billing: pending refunds were incorrectly included; negative adjustments must remain signed"))
        families.append(dict(family="stock", category="debugging", project="inventory",
            prompt="Fix available(events): replay delta events exactly once per event_id. Distinct events with equal deltas must both count. Return signed total; input may be empty.",
            code="def available(events):\n    return sum(set(e['delta'] for e in events))\n",
            oracle="def available(events):\n    seen = set()\n    total = 0\n    for e in events:\n        if e['event_id'] not in seen:\n            seen.add(e['event_id'])\n            total += e['delta']\n    return total\n",
            fn="available",cases=[([[]],0),([[{'event_id':'a','delta':n},{'event_id':'b','delta':n},{'event_id':'a','delta':n}]],2*n),([[{'event_id':'x','delta':-3},{'event_id':'y','delta':7}]],4)],
            signal="ERROR stock reconciliation: deduplication used delta value rather than event_id"))
        families.append(dict(family="window",category="implementation",project="scheduling",
            prompt=f"Implement in_window(values): retain original order and duplicates, keeping values in [{n}, {n+9}) (lower inclusive, upper exclusive).",
            code="def in_window(values):\n    raise NotImplementedError\n",
            oracle=f"def in_window(values):\n    return [v for v in values if {n} <= v < {n+9}]\n",
            fn="in_window",cases=[([[]],[]),([[n-1,n,n+8,n+9,n]], [n,n+8,n]),([[n+3,n+2]],[n+3,n+2])],signal="TODO implement half-open interval selection"))
        families.append(dict(family="orders",category="implementation",project="orders",
            prompt="Implement latest_orders(rows): for each order_id retain the greatest integer revision; on ties retain the LAST input record. Return records sorted lexicographically by order_id. Do not mutate input.",
            code="def latest_orders(rows):\n    raise NotImplementedError\n",
            oracle="def latest_orders(rows):\n    latest = {}\n    for row in rows:\n        if row['order_id'] not in latest or row['revision'] >= latest[row['order_id']]['revision']:\n            latest[row['order_id']] = row\n    return [latest[k] for k in sorted(latest)]\n",
            fn="latest_orders", cases=[([[]],[]),([[{'order_id':'b','revision':n,'v':1},{'order_id':'a','revision':1,'v':2},{'order_id':'b','revision':n,'v':3},{'order_id':'b','revision':n-1,'v':4}]], [{'order_id':'a','revision':1,'v':2},{'order_id':'b','revision':n,'v':3}])],signal="TODO implement latest revision merge; tie-breaking uses the final occurrence"))
        families.append(dict(family="roles",category="implementation",project="access",
            prompt="Implement authorized(user, resource): allow only when tenant matches AND user.active is True AND 'reader' is present in user.roles. Missing active or roles means deny. Missing tenant on either side means deny.",
            code="def authorized(user, resource):\n    raise NotImplementedError\n",
            oracle="def authorized(user, resource):\n    return 'tenant' in user and 'tenant' in resource and user['tenant'] == resource['tenant'] and user.get('active') is True and 'reader' in user.get('roles', [])\n",
            fn="authorized",cases=[([{'tenant':'a','active':True,'roles':['reader']},{'tenant':'a'}],True),([{'tenant':'a','active':True,'roles':['reader']},{'tenant':'b'}],False),([{'active':True,'roles':['reader']},{}],False),([{'tenant':'a','active':False,'roles':['reader']},{'tenant':'a'}],False),([{'tenant':'a'},{'tenant':'a'}],False)],signal="TODO tenant isolation and active-user check are mandatory"))
        reviews = [
            ('access_review','access',"Review app.py against the specification. Report ONLY incorrect function names as findings. authorized must require matching tenant AND reader role; enabled must default to False; key_for must include tenant and id.",
             "def authorized(user, resource):\n    return user['tenant'] == resource['tenant'] or 'reader' in user['roles']\n\ndef enabled(config):\n    return config.get('enabled', False)\n\ndef key_for(resource):\n    return resource['id']\n",['authorized','key_for']),
            ('money_review','billing',"Review app.py. Report ONLY incorrect function names as findings. charge must return quantity * integer unit_cents; refundable must be true only for settled payments; tax must use integer floor of amount*basis_points/10000.",
             "def charge(quantity, unit_cents):\n    return quantity * unit_cents\n\ndef refundable(payment):\n    return payment['status'] != 'failed'\n\ndef tax(amount, basis_points):\n    return amount * basis_points // 100\n",['refundable','tax']),
            ('schedule_review','scheduling',f"Review app.py. Report ONLY incorrect function names as findings. due(t) is true iff t < {n}; unique keeps first occurrence order; total sums ALL signed values.",
             f"def due(t):\n    return t <= {n}\n\ndef unique(items):\n    return list(dict.fromkeys(items))\n\ndef total(values):\n    return sum(v for v in values if v > 0)\n",['due','total'])]
        for family,project,prompt,code,findings in reviews:
            families.append(dict(family=family,category='review',project=project,prompt=prompt,code=code,findings=findings,signal='INFO review request: inspect all functions, including the end of the file'))
        ledger=[{'id':f'row-{i:04}','status':'settled' if i%7 else 'pending','amount_cents':rng.randint(-300,800),'tenant':'a' if i%3 else 'b'} for i in range(180+n*5)]
        families.append(dict(family='ledger',category='structured',project='billing',prompt="From records.json, return answer with count and total_cents for ALL rows with tenant='a' AND status='settled'. Count every row; signed amounts; no sampling.",records=ledger,answer={'count':sum(r['tenant']=='a' and r['status']=='settled' for r in ledger),'total_cents':sum(r['amount_cents'] for r in ledger if r['tenant']=='a' and r['status']=='settled')}))
        inventory=[{'sku':f'SKU-{i:03}','available':rng.randint(0,20),'reserved':rng.randint(0,20),'warehouse':'east' if i%2 else 'west'} for i in range(180+n)]
        families.append(dict(family='shortage',category='structured',project='inventory',prompt="From records.json, return answer as the sorted list of EVERY sku in warehouse='east' where reserved > available. Exact completeness is required.",records=inventory,answer=sorted(r['sku'] for r in inventory if r['warehouse']=='east' and r['reserved']>r['available'])))
        orders=[{'order_id':f'O-{i%45:03}','revision':i//45,'cancelled':bool(i%11==0),'amount':rng.randint(1,500)} for i in range(200+n)]
        latest={r['order_id']:r for r in orders}
        families.append(dict(family='latest',category='structured',project='orders',prompt="From records.json choose each order_id's greatest revision (last input on ties). Return answer with active_count and active_amount summing ONLY latest records where cancelled=false. Process every record.",records=orders,answer={'active_count':sum(not r['cancelled'] for r in latest.values()),'active_amount':sum(r['amount'] for r in latest.values() if not r['cancelled'])}))
        for f in families:
            task_id=f"{f['family']}-{variant:02}"
            resources={}
            if 'code' in f:
                resources['app.py']=f['code']
                lines=[f"INFO worker={i%8} heartbeat event={i} completed successfully" for i in range(240)]
                # Critical evidence can occur near the tail, middle or beginning.
                lines[(13,120,230,237,2)[variant]]=f['signal']
                resources['run.log']='\n'.join(lines)
                resources['README.md']=f"# {f['project']}\n\n{f['prompt']}\n"
            else:resources['records.json']=json.dumps(f['records'],indent=2)
            private={k:f[k] for k in ['fn','cases','oracle','findings','answer'] if k in f}
            task={'id':task_id,'family':f['family'],'project':f['project'],'category':f['category'],'split':'development' if f['family'] in dev else 'evaluation','prompt':f['prompt'],'resources':resources,'private':private,'provenance':'Original synthetic fixture; MIT; seed 20260918; no customer data'}
            task['sha256']=digest(task);tasks.append(task)
    return sorted(tasks,key=lambda t:t['id'])


def write_suite(root=ROOT):
    tasks=build_tasks();p=root/'tasks';p.mkdir(parents=True,exist_ok=True)
    for t in tasks:(p/(t['id']+'.json')).write_text(json.dumps(t,indent=2)+'\n')
    manifest={'version':'0.1.0','seed':20260918,'tasks':[{'id':t['id'],'sha256':t['sha256'],'split':t['split'],'family':t['family'],'category':t['category']} for t in tasks]}
    (p/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def load_suite(root=ROOT):
    manifest=json.loads((root/'tasks/manifest.json').read_text());tasks=[]
    for entry in manifest['tasks']:
        t=json.loads((root/'tasks'/(entry['id']+'.json')).read_text());claimed=t.pop('sha256')
        if digest(t)!=claimed or claimed!=entry['sha256']:raise ValueError('Task hash mismatch: '+entry['id'])
        t['sha256']=claimed;tasks.append(t)
    return tasks
