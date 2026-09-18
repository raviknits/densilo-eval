"""Report actual provider usage, including failed answers and extra upstream calls."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random


def percentile(values, q):
    values = sorted(values)
    if not values:
        return None
    x = (len(values) - 1) * q
    lo = int(x)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (x - lo)


def summarize(rows):
    successes = sum(bool(r.get('success')) for r in rows)
    keys = ['input', 'output', 'cached_input', 'calls', 'unknown_usage', 'retrievals']
    result = {key: sum(r[key] for r in rows) for key in keys}
    result.update(n=len(rows), success=successes,
                  invalid=sum(not r['valid'] for r in rows),
                  total=result['input'] + result['output'],
                  p50_s=percentile([r['duration_s'] for r in rows], .5),
                  p95_s=percentile([r['duration_s'] for r in rows], .95))
    result['tokens_per_success'] = result['total'] / successes if successes else None
    result['usage_complete'] = result['unknown_usage'] == 0
    return result


def paired_bootstrap(rows, candidate, baseline, trials=10000):
    families = sorted({r['family'] for r in rows})
    clusters = {a: {f: summarize([r for r in rows if r['arm'] == a and r['family'] == f])
                    for f in families} for a in (candidate, baseline)}
    rng = random.Random(918207)
    savings, quality = [], []
    for _ in range(trials):
        sampled = rng.choices(families, k=len(families))
        sums = {a: {key: sum(clusters[a][f][key] for f in sampled)
                    for key in ('success', 'total', 'n')} for a in clusters}
        c, b = sums[candidate], sums[baseline]
        if c['success'] and b['success']:
            savings.append(100 * (1 - (c['total'] / c['success']) / (b['total'] / b['success'])))
        quality.append(100 * (c['success'] / c['n'] - b['success'] / b['n']))
    return {'family_clusters': len(families), 'bootstrap_draws': trials,
            'tokens_per_success_saving_percent_ci95': [percentile(savings, .025), percentile(savings, .975)],
            'success_rate_difference_pp_ci95': [percentile(quality, .025), percentile(quality, .975)],
            'interpretation': 'Exploratory paired family bootstrap; generated families and correlated variants are not independent customer workloads.'}


def build(run_dir, services, output):
    run_dir, services, output = Path(run_dir), Path(services), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((run_dir / 'manifest.json').read_text())
    rows = [json.loads(p.read_text()) for p in sorted((run_dir / 'runs').glob('*.json'))]
    source_integrity = {}
    for filename, expected in manifest.get('source_sha256', {}).items():
        p = Path(filename)
        source_integrity[filename] = p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == expected
    wire = defaultdict(list)
    for arm in manifest['arms']:
        for line in (services / arm / 'upstream.jsonl').read_text().splitlines():
            w = json.loads(line)
            wire[(arm, w['case'])].append(w)
    accounting = []
    for r in rows:
        attempts = wire[(r['arm'], r['id'])]
        # No wire record is unknown, not a presumed cache hit or zero cost.
        r['calls'] = len(attempts)
        r['unknown_usage'] = sum(w.get('usage') is None for w in attempts) + (not attempts)
        r['input'] = sum((w.get('usage') or {}).get('input_tokens', 0) for w in attempts)
        r['output'] = sum((w.get('usage') or {}).get('output_tokens', 0) for w in attempts)
        r['cached_input'] = sum((w.get('usage') or {}).get('input_tokens_details', {}).get('cached_tokens', 0) for w in attempts)
        accounting.append({k: r[k] for k in ['id', 'arm', 'family', 'success', 'valid', 'input', 'output', 'cached_input', 'calls', 'unknown_usage', 'retrievals', 'duration_s']})
        accounting[-1]['client_usage'] = r['provider_usage']
        accounting[-1]['wire_statuses'] = [w.get('status') for w in attempts]
    groups = {arm: summarize([r for r in rows if r['arm'] == arm]) for arm in manifest['arms']}
    families = {f: {arm: summarize([r for r in rows if r['arm'] == arm and r['family'] == f])
                    for arm in manifest['arms']} for f in manifest['families']}
    candidate = 'candidate'
    comparisons = {}
    for baseline in manifest['arms']:
        if baseline == candidate:
            continue
        c, b = groups[candidate], groups[baseline]
        comparisons[baseline] = {
            'total_tokens_saving_percent': 100 * (1 - c['total'] / b['total']),
            'tokens_per_success_saving_percent': 100 * (1 - c['tokens_per_success'] / b['tokens_per_success']),
            'quality_difference_pp': 100 * (c['success'] / c['n'] - b['success'] / b['n']),
            'p95_change_percent': 100 * (c['p95_s'] / b['p95_s'] - 1),
            **paired_bootstrap(rows, candidate, baseline)}
    result = {'run_dir': str(run_dir), 'observations': len(rows),
              'expected_observations': len(manifest['tasks']) * manifest['repeats'] * len(manifest['arms']),
              'source_integrity': source_integrity, 'arms': groups, 'families': families,
              'comparisons': comparisons, 'accounting': accounting,
              'limitations': ['Codex subscription token counters, not measured API invoices or dollars.',
                              'All output tokens include reasoning; reasoning is not added twice.',
                              'All failed answers and observed upstream attempts are charged to the numerator.',
                              'Synthetic fixtures, one model, ten families, same operator as candidate.',
                              'Native means unoptimized Headroom forwarding, not direct network baseline.',
                              'Fake upstream protocol checks are excluded from token/quality results.',
                              'Memory and traffic learning disabled; no claim of exhaustive proxy-feature coverage.']}
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = ['# Full HTTP proxy comparison', '',
             f"Recorded **{len(rows)}/{result['expected_observations']} outcomes**, using actual Headroom 0.37.0 HTTP servers and live Codex gpt-5.6-luna responses.", '',
             'The candidate is derived from Headroom and adds reversible tool-output transformations. Headroom subsequently applies its own compression. This is not an independent implementation or a wholly lossless request path.', '',
             '| Arm | Correct | Input | Output | Cached input | All tokens/correct | p50 s | p95 s | Upstream calls |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm, s in groups.items():
        lines.append(f"| {arm} | {s['success']}/{s['n']} | {s['input']:,} | {s['output']:,} | {s['cached_input']:,} | {s['tokens_per_success']:,.0f} | {s['p50_s']:.2f} | {s['p95_s']:.2f} | {s['calls']} |")
    lines += ['', 'All observed spend, including wrong answers and retrieval rounds, is included. Token counts are not dollar savings. With input price P, cached-input price C, and output price Q, compute `(input-cached)*P + cached*C + output*Q`; no dollar price is assumed.', '',
              '| Candidate compared with | Total token saving | Tokens/correct saving | Family bootstrap 95% interval | Accuracy change | p95 latency change |',
              '|---|---:|---:|---:|---:|---:|']
    for baseline, c in comparisons.items():
        lo, hi = c['tokens_per_success_saving_percent_ci95']
        lines.append(f"| {baseline} | {c['total_tokens_saving_percent']:.1f}% | {c['tokens_per_success_saving_percent']:.1f}% | {lo:.1f}% to {hi:.1f}% | {c['quality_difference_pp']:+.1f} pp | {c['p95_change_percent']:+.1f}% |")
    lines += ['', 'Positive token saving means fewer tokens; positive latency change means slower. Bootstrap intervals are exploratory and use ten generated family clusters, not 240 independent tasks.', '',
              '| Family | Native correct | Headroom cache correct | Headroom token correct | Candidate correct | Cache tokens/correct | Candidate tokens/correct |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for family, arms in families.items():
        scores = [f"{arms[a]['success']}/{arms[a]['n']}" for a in manifest['arms']]
        costs = [('—' if arms[a]['tokens_per_success'] is None else f"{arms[a]['tokens_per_success']:,.0f}") for a in ['headroom_cache', 'candidate']]
        lines.append('| ' + ' | '.join([family, *scores, *costs]) + ' |')
    lines += ['', f"Infrastructure-invalid outcomes: {sum(s['invalid'] for s in groups.values())}. Attempts/cases with missing usage: {sum(s['unknown_usage'] for s in groups.values())}. Frozen source files match: {all(source_integrity.values())}.", '',
              'Reproducibility: manifest.json freezes source hashes, task hashes, arm configuration and repetitions. Per-case records and separate outgoing-request logs allow usage reconciliation. Pilot variant 00 is excluded from the main run.', '',
              '## Limits', '', *['- ' + x for x in result['limitations']], '']
    (output / 'REPORT.md').write_text('\n'.join(lines))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', default='results/fullproxy-v2/main')
    p.add_argument('--services', default='results/fullproxy-v2/services')
    p.add_argument('--output', default='results/fullproxy-v2/report')
    a = p.parse_args()
    r = build(a.run, a.services, a.output)
    print(json.dumps({'observations': r['observations'], 'arms': r['arms'], 'comparisons': r['comparisons']}, indent=2))


if __name__ == '__main__':
    main()
