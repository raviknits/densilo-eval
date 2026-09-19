# Independent Densilo full-proxy comparison

This candidate owns its HTTP/SSE/WebSocket request path and reversible compression. Candidate and unoptimized control processes run in an isolated environment with Headroom absent; the runner asserts this at startup. Headroom runs only in separate competitor processes. Previous extension results are excluded.

**96/96 outcomes**, 8 fixtures in 4 previously seen synthetic families, manifest-specified repetitions, one model (Codex gpt-5.6-luna). This is author-operated engineering evidence, not an independent customer holdout.

| Arm | Correct | Input | Output | Cached input | All tokens/correct | p50 s | p95 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate | 24/24 | 42,786 | 1,760 | 0 | 1,856 | 4.06 | 7.01 |
| previous | 24/24 | 64,893 | 1,431 | 18,176 | 2,764 | 3.78 | 5.25 |
| headroom_token | 24/24 | 55,980 | 1,577 | 9,216 | 2,398 | 3.58 | 4.53 |
| headroom_cache | 24/24 | 55,980 | 1,587 | 13,824 | 2,399 | 4.08 | 7.94 |

All failed-answer spend, all observed upstream attempts and additional model/tool rounds count. Output includes reasoning; cached input is a subset of input. Provider counters are not actual dollar bills. Concurrent arms each use one client. Server startup is excluded; first-request initialization is included. No controlled cold/warm or production-load inference is justified.

| Candidate vs | Total token saving | Tokens/correct saving | Family bootstrap 95% interval | Accuracy change | p95 change |
|---|---:|---:|---:|---:|---:|
| previous | 32.8% | 32.8% | 17.1% to 58.6% | +0.0 pp | +33.4% |
| headroom_token | 22.6% | 22.6% | 5.1% to 56.5% | +0.0 pp | +54.7% |
| headroom_cache | 22.6% | 22.6% | 4.9% to 56.4% | +0.0 pp | -11.7% |

Positive savings mean fewer tokens; positive latency change means slower. Bootstrap clusters are workload families; repetitions and generated variants are not independent customer workloads.

| Family | candidate | previous | headroom_token | headroom_cache |
|---|---:|---:|---:|---:|
| code_repair | 6/6 | 6/6 | 6/6 | 6/6 |
| research_conflicts | 6/6 | 6/6 | 6/6 | 6/6 |
| session_freshness | 6/6 | 6/6 | 6/6 | 6/6 |
| structured_lookup | 6/6 | 6/6 | 6/6 | 6/6 |

Infrastructure-invalid outcomes: 0. Missing-usage cases/attempts: 0. Source hashes match: True.

HTTP/WebSocket contract results are separate fake-provider evidence and do not contribute to measured savings. Real Anthropic/OpenAI API-key quality, persistent memory, adaptive learning, advanced provider-specific endpoints, native mobile integration, production load, and priced net savings remain unproven.
