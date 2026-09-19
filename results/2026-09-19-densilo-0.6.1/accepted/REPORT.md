# Independent Densilo full-proxy comparison

This candidate owns its HTTP/SSE/WebSocket request path and reversible compression. Candidate and unoptimized control processes run in an isolated environment with Headroom absent; the runner asserts this at startup. Headroom runs only in separate competitor processes. Previous extension results are excluded.

**360/360 outcomes**, 20 fixtures in 10 previously seen synthetic families, manifest-specified repetitions, one model (Codex gpt-5.6-luna). This is author-operated engineering evidence, not an independent customer holdout.

| Arm | Correct | Input | Output | Cached input | All tokens/correct | p50 s | p95 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| native | 60/60 | 307,668 | 3,503 | 210,688 | 5,186 | 2.87 | 6.69 |
| headroom_cache | 49/60 | 141,797 | 5,116 | 80,640 | 2,998 | 3.94 | 11.41 |
| headroom_token | 50/60 | 143,161 | 5,299 | 71,424 | 2,969 | 3.70 | 11.07 |
| headroom_lossless | 56/60 | 277,708 | 3,717 | 212,736 | 5,025 | 2.71 | 7.04 |
| candidate | 60/60 | 123,586 | 4,590 | 49,408 | 2,136 | 3.04 | 9.67 |
| previous | 59/60 | 141,864 | 3,615 | 69,120 | 2,466 | 2.82 | 5.61 |

All failed-answer spend, all observed upstream attempts and additional model/tool rounds count. Output includes reasoning; cached input is a subset of input. Provider counters are not actual dollar bills. Concurrent arms each use one client. Server startup is excluded; first-request initialization is included. No controlled cold/warm or production-load inference is justified.

| Candidate vs | Total token saving | Tokens/correct saving | Family bootstrap 95% interval | Accuracy change | p95 change |
|---|---:|---:|---:|---:|---:|
| native | 58.8% | 58.8% | 43.1% to 69.9% | +0.0 pp | +44.6% |
| headroom_cache | 12.8% | 28.7% | -0.2% to 57.7% | +18.3 pp | -15.3% |
| headroom_token | 13.7% | 28.1% | -0.3% to 56.2% | +16.7 pp | -12.6% |
| headroom_lossless | 54.5% | 57.5% | 40.3% to 68.3% | +6.7 pp | +37.3% |
| previous | 11.9% | 13.4% | -0.2% to 31.1% | +1.7 pp | +72.5% |

Positive savings mean fewer tokens; positive latency change means slower. Bootstrap clusters are workload families; repetitions and generated variants are not independent customer workloads.

| Family | native | headroom_cache | headroom_token | headroom_lossless | candidate | previous |
|---|---:|---:|---:|---:|---:|---:|
| code_repair | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| code_review | 6/6 | 1/6 | 2/6 | 6/6 | 6/6 | 6/6 |
| log_diagnosis | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| log_exact_count | 6/6 | 0/6 | 0/6 | 2/6 | 6/6 | 6/6 |
| long_conversation | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| research_conflicts | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| search_evidence | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| session_freshness | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| structured_aggregation | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 5/6 |
| structured_lookup | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

Infrastructure-invalid outcomes: 0. Missing-usage cases/attempts: 0. Source hashes match: True.

HTTP/WebSocket contract results are separate fake-provider evidence and do not contribute to measured savings. Real Anthropic/OpenAI API-key quality, persistent memory, adaptive learning, advanced provider-specific endpoints, native mobile integration, production load, and priced net savings remain unproven.
