# Densilo public proxy evaluation

Reproducible, author-operated development tests for complete context-optimization proxies: **30 generated fixtures across 10 families**, graders, bounded recovery tools, a five-arm runner and a separate release gate. This repository contains evaluation code, not the Densilo product compressor, and makes no universal superiority claim.

The families include structured aggregation, exact log counting, diagnosis, code review/repair, research conflicts, search evidence, history and resource updates. `-00` fixtures are pilot variants; the default run evaluates the other 20. A new seed in the same families is not an independent holdout.

## Reproduce

Use Python 3.11+. Install `requirements.txt` into a benchmark environment. Separately install the candidate Densilo wheel into one environment without Headroom, and pinned Headroom 0.37.0 into another. Obtain the candidate wheel from the experiment's release owner; it is not silently downloaded. The native control uses the same Densilo proxy with optimization disabled.

Start one server per arm with the corresponding environment's Python:

```sh
python -m densilo_eval.serve --arm candidate --port 8850 --evidence runs/services/candidate
python -m densilo_eval.serve --arm native --port 8851 --evidence runs/services/native
python -m densilo_eval.serve --arm headroom_cache --port 8852 --evidence runs/services/headroom_cache
python -m densilo_eval.serve --arm headroom_token --port 8853 --evidence runs/services/headroom_token
python -m densilo_eval.serve --arm headroom_lossless --port 8854 --evidence runs/services/headroom_lossless
```

Then run the paired fixtures:

```sh
python -m densilo_eval.run --ports '{"native":8851,"candidate":8850,"headroom_cache":8852,"headroom_token":8853,"headroom_lossless":8854}' --auth api --model YOUR_PINNED_MODEL --output runs/experiment --repeats 2
```

API mode reads `OPENAI_API_KEY` locally. `--auth codex` explicitly uses the existing local Codex login for experimental subscription tests; those results do not establish API dollar savings. Never commit credentials, customer prompts or `runs/`. Five arms run concurrently with one client each. Cold/warm cache comparisons require a separate prespecified session experiment.

The runner grades every phase and includes recovery/repair calls. Observers capture attempts independently of client-visible usage. Code grading uses platform sandbox controls and fails closed when isolation is unavailable. Test fixtures with `python -m unittest discover -s tests -v`.

## Evidence limits

Report raw tokens, cached input, output/reasoning, task success, failed attempts, recovery and latency separately. Provider counters are not invoices. Price ratios are not dollar savings. A release claim requires deployment/gateway fees, non-token charges and customer workloads too.

`python -m densilo_eval.gate --help` exposes the cost/quality gate. Qualifying manifests must be sealed independent holdouts. Required bounds include at least 15% lower net cost per successful task, positive clustered cost confidence, quality noninferiority within one percentage point and no observed critical failures. These development fixtures cannot qualify.

Identity, billing, memory, image quality, physical devices, native apps, operations and paid pilots require separate acceptance. Passing this suite does not certify them.

## Provenance

Harness and generated fixtures: MIT. `manifest.json` pins fixture bytes; `headroom-baseline.json` records the competitor release/source. Headroom runs as a separately installed competitor, never inside the candidate. Publish grader corrections, failure cases and changed manifests for review. No independent customer benchmark or paid pilot has yet been established by this repository.


## Published development result

[19 September 2026 frozen full-proxy comparison](results/2026-09-19-codex-development/REPORT.md): Densilo 20/20 correct; Headroom cache 16/20, token 16/20, lossless 18/20. Densilo used 8.7% fewer total tokens than cache mode and 2.0% fewer than token mode. The token-per-correct-task confidence intervals against cache/token modes include zero. **Consistent superiority, independent customer quality and paid net savings remain unestablished.** The native control scored 19/20; model stochasticity is visible. All 100 observations include upstream attempt accounting and matching source hashes.
