"""Auditable paired evaluation gates. Never infer paid savings from token counts.

Costs and success are equally weighted by independent source cluster. The
quality bound conservatively treats any regression within a cluster as a loss;
Clopper-Pearson bounds its probability without crediting improvements elsewhere.
This requires the independent sampling contract stated in the preregistration.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import sys


def fingerprint(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Invalid or unknown ' + name)
    return value


def percentile(values, q):
    values = sorted(values)
    if not values:
        raise ValueError('Empty sample')
    return values[max(0, min(len(values)-1, math.ceil(q * len(values))-1))]


def loss_upper(losses, n, alpha=.05):
    """One-sided exact binomial upper bound, computed in log space."""
    if losses == n:
        return 1.0
    if losses == 0:
        return 1 - alpha**(1/n)
    constants = [math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1) for k in range(losses+1)]
    low, high = losses/n, 1.0
    for _ in range(65):
        p = (low+high)/2
        logs = [v+k*math.log(p)+(n-k)*math.log1p(-p) for k,v in enumerate(constants)]
        largest = max(logs)
        cdf = math.exp(largest)*sum(math.exp(v-largest) for v in logs)
        if cdf > alpha:
            low = p
        else:
            high = p
    return high


def evaluate(protocol, manifest, observations):
    if protocol.get('schema_version') != 1 or manifest.get('schema_version') != 1:
        raise ValueError('Unsupported evaluation schema')
    if protocol['manifest_sha256'] != fingerprint(manifest):
        raise ValueError('Manifest differs from preregistration')
    for key, low, high in (("quality_margin",0,.01), ("net_savings_target",.15,1),
                           ("latency_ratio_limit",1,1.1), ("optimizer_p95_ms_limit",1,50)):
        value = number(protocol[key], key)
        if not low <= value <= high:
            raise ValueError("Protocol weakens or invalidates a release gate: " + key)
    for key in ("minimum_clusters", "minimum_tasks"):
        if type(protocol[key]) is not int or protocol[key] < 1:
            raise ValueError("Positive sample size requirements are mandatory")
    candidate, baseline = protocol['candidate'], protocol['baseline']
    if not all(isinstance(a, str) and a for a in (candidate, baseline)) or candidate == baseline:
        raise ValueError('Two distinct pinned arms are required')
    tasks = {}
    for task in manifest['tasks']:
        if task['id'] in tasks or not isinstance(task['cluster'], str) or not task['cluster']:
            raise ValueError('Duplicate task or missing source cluster')
        if not isinstance(task['sha256'], str) or len(task['sha256']) != 64:
            raise ValueError('Missing fixture checksum')
        tasks[task['id']] = task
    if not tasks:
        raise ValueError('Empty manifest')
    rows = {}
    for row in observations:
        key = (row['task_id'], row['arm'])
        if key in rows or key[0] not in tasks or key[1] not in (candidate, baseline):
            raise ValueError('Duplicate, unregistered task or unregistered arm')
        if row['fixture_sha256'] != tasks[key[0]]['sha256']:
            raise ValueError('Fixture checksum mismatch')
        if row['cluster'] != tasks[key[0]]['cluster']:
            raise ValueError('Source cluster changed after preregistration')
        if row.get('cost_complete') is not True:
            raise ValueError('Unknown attempt charges cannot be treated as zero')
        if type(row['success']) is not bool or type(row['critical_failure']) is not bool:
            raise ValueError('Explicit quality verdicts required')
        if type(row['attempts']) is not int or row['attempts'] < 1:
            raise ValueError('All attempts must be accounted for')
        costs = row['cost_microusd']
        if set(costs) != {'provider_all_attempts', 'gateway_fee', 'deployment'}:
            raise ValueError('Explicit provider, fee and deployment costs required')
        total = sum(number(value, 'cost') for value in costs.values())
        latency = number(row['latency_ms'], 'latency')
        if latency == 0:
            raise ValueError('Positive measured end-to-end latency required')
        if key[1] == candidate:
            number(row['optimizer_ms'], 'optimizer overhead')
        rows[key] = {**row, 'total_cost': total}
    if len(rows) != len(tasks)*2:
        raise ValueError('Missing paired outcomes; failed tasks cannot be omitted')
    groups = defaultdict(list)
    for task in tasks.values():
        groups[task['cluster']].append((rows[(task['id'],candidate)], rows[(task['id'],baseline)]))
    samples, loss_clusters = [], 0
    for pairs in groups.values():
        n = len(pairs)
        samples.append(tuple(sum(pair[arm][field] for pair in pairs)/n
            for arm, field in ((0,'total_cost'), (0,'success'), (1,'total_cost'), (1,'success'))))
        loss_clusters += int(any(not c['success'] and b['success'] for c,b in pairs))

    def savings(sample):
        sums = [sum(v[i] for v in sample) for i in range(4)]
        cc, cs, bc, bs = sums
        if cs == 0 or bs == 0 or bc == 0:
            return None
        return 1 - (cc/cs)/(bc/bs)

    saving = savings(samples)
    draws = protocol['bootstrap_draws']
    if type(draws) is not int or not 1000 <= draws <= 10000:
        raise ValueError('Bootstrap draws must be an integer from 1000 to 10000')
    rng = random.Random(protocol['bootstrap_seed'])
    distribution = [savings([samples[rng.randrange(len(samples))] for _ in samples]) for _ in range(draws)]
    bounded = all(v is not None for v in distribution)
    interval = [percentile(distribution,.025),percentile(distribution,.975)] if bounded else None
    quality_lower = -loss_upper(loss_clusters,len(samples))
    quality_delta = sum(s[1]-s[3] for s in samples)/len(samples)
    baseline_p95 = percentile([r['latency_ms'] for (task,arm),r in rows.items() if arm == baseline],.95)
    candidate_p95 = percentile([r['latency_ms'] for (task,arm),r in rows.items() if arm == candidate],.95)
    optimizer_p95 = percentile([r['optimizer_ms'] for (task,arm),r in rows.items() if arm == candidate],.95)
    critical = sum(r['critical_failure'] for (task,arm),r in rows.items() if arm == candidate)
    gates = {
        'independent_holdout': manifest.get('split') == 'sealed_holdout' and manifest.get('independent_sources') is True,
        'minimum_clusters': len(samples) >= protocol['minimum_clusters'],
        'minimum_tasks': len(tasks) >= protocol['minimum_tasks'],
        'quality_noninferiority': quality_lower >= -protocol['quality_margin'],
        'no_observed_critical_failures': critical == 0,
        'net_cost_target': saving is not None and saving >= protocol['net_savings_target'],
        'positive_cost_confidence_bound': bounded and interval[0] > 0,
        'end_to_end_latency': candidate_p95/baseline_p95 <= protocol['latency_ratio_limit'],
        'optimizer_latency': optimizer_p95 <= protocol['optimizer_p95_ms_limit'],
    }
    return {'schema_version':1, 'decision':'PASS' if all(gates.values()) else 'NOT_ESTABLISHED',
            'candidate':candidate,'baseline':baseline,'protocol_sha256':fingerprint(protocol),
            'manifest_sha256':fingerprint(manifest),'tasks':len(tasks),'clusters':len(samples),
            'weighting':'equal_source_cluster','gates':gates,'net_cost_saving':saving,
            'net_cost_saving_95pct_cluster_bootstrap':interval,'quality_delta':quality_delta,
            'quality_lower_95pct_conservative':quality_lower,'regression_clusters':loss_clusters,
            'critical_failures':critical,'candidate_p95_ms':candidate_p95,'baseline_p95_ms':baseline_p95,
            'optimizer_p95_ms':optimizer_p95,'all_attempts':sum(r['attempts'] for r in observations),
            'limitation':'Statistical gates rely on independently sampled source clusters, complete costs and trustworthy graders. A PASS is not universal superiority or production certification.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Evaluate a preregistered paired Densilo comparison')
    parser.add_argument('--protocol',required=True)
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--observations',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    try:
        report = evaluate(json.loads(Path(args.protocol).read_text()), json.loads(Path(args.manifest).read_text()),
                          [json.loads(line) for line in Path(args.observations).read_text().splitlines() if line.strip()])
    except (ValueError, KeyError, TypeError) as exc:
        parser.exit(2,'Invalid evidence: '+str(exc)+'\n')
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(report['decision'])
    return 0 if report['decision'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
