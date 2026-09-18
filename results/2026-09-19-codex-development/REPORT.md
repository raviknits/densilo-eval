# Independent Densilo full-proxy comparison

This candidate owns its HTTP/SSE/WebSocket request path and reversible compression. Candidate and unoptimized control processes run in an isolated environment with Headroom absent; the runner asserts this at startup. Headroom runs only in separate competitor processes. Previous extension results are excluded.

**100/100 outcomes**, 20 newly seeded fixtures in ten previously seen synthetic families, manifest-specified repetitions, one model (Codex gpt-5.6-luna). This is author-operated engineering evidence, not an independent customer holdout.

| Arm | Correct | Input | Output | Cached input | All tokens/correct | p50 s | p95 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| native | 19/20 | 102,564 | 1,163 | 75,008 | 5,459 | 3.39 | 6.61 |
| headroom_cache | 16/20 | 51,183 | 1,861 | 22,272 | 3,315 | 4.84 | 14.10 |
| headroom_token | 16/20 | 47,703 | 1,717 | 22,272 | 3,089 | 3.90 | 11.50 |
| headroom_lossless | 18/20 | 92,202 | 1,062 | 73,216 | 5,181 | 2.65 | 5.82 |
| candidate | 20/20 | 47,288 | 1,144 | 23,040 | 2,422 | 2.51 | 4.65 |

All failed-answer spend, all observed upstream attempts and additional model/tool rounds count. Output includes reasoning; cached input is a subset of input. Provider counters are not actual dollar bills. Five concurrent arms each use one client. Server startup is excluded; first-request initialization is included. No controlled cold/warm or production-load inference is justified.

| Candidate vs | Total token saving | Tokens/correct saving | Family bootstrap 95% interval | Accuracy change | p95 change |
|---|---:|---:|---:|---:|---:|
| native | 53.3% | 55.6% | 36.8% to 68.4% | +5.0 pp | -29.8% |
| headroom_cache | 8.7% | 27.0% | -0.8% to 53.0% | +20.0 pp | -67.0% |
| headroom_token | 2.0% | 21.6% | -3.3% to 48.3% | +20.0 pp | -59.6% |
| headroom_lossless | 48.1% | 53.3% | 32.7% to 66.4% | +10.0 pp | -20.1% |

Positive savings mean fewer tokens; positive latency change means slower. Bootstrap clusters are the ten families; observations are not 200 independent tasks.

| Family | native | headroom_cache | headroom_token | headroom_lossless | candidate |
|---|---:|---:|---:|---:|---:|
| code_repair | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| code_review | 2/2 | 1/2 | 1/2 | 2/2 | 2/2 |
| log_diagnosis | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| log_exact_count | 2/2 | 0/2 | 0/2 | 0/2 | 2/2 |
| long_conversation | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| research_conflicts | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| search_evidence | 1/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| session_freshness | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| structured_aggregation | 2/2 | 1/2 | 1/2 | 2/2 | 2/2 |
| structured_lookup | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |

Infrastructure-invalid outcomes: 0. Missing-usage cases/attempts: 0. Source hashes match: True.

HTTP/WebSocket contract results are separate fake-provider evidence and do not contribute to measured savings. Real Anthropic/OpenAI API-key quality, persistent memory, adaptive learning, advanced provider-specific endpoints, native mobile integration, production load, and priced net savings remain unproven.
