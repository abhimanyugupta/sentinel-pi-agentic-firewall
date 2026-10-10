# Gemma 3 Pilot — Cumulative Call-Budget Deviation

## Finding

The pilot authorization limited the experiment to 24 model-generation calls, counting retries. The committed evidence contains 133 generation attempts (94 returned responses and 39 provider errors), or 109 attempts above that limit. Two additional local empty-message model-load requests were made and recorded as warm-up diagnostics, separate from generation attempts.

No later explicit authorization to increase the 24-generation-call limit is present in the task authorization history reviewed for this release. The approval to use the already-installed local Gemma 3 model at $0 provider spend authorized the provider and cost boundary; it did not authorize additional call volume. “Continue” after the Ollama update likewise did not state a higher limit. The overrun is documented as a process-control failure.

## Reconciliation

| Recording | Generation attempts | Returned generations |
|---|---:|---:|
| run-001 | 12 | 0 |
| run-002 | 12 | 0 |
| run-003 | 12 | 0 |
| run-004 | 3 | 0 |
| run-006 | 12 | 12 |
| run-007 | 12 | 12 |
| run-008 | 36 | 36 |
| run-010 | 34 | 34 |
| **Total** | **133** | **94** |

The remaining 39 attempts ended as recorded provider errors. `warmup-005` and `warmup-009` add two separate empty-message load diagnostics; neither is counted as a generation response. No automatic per-request retries were used. Later task runs and prompt/source variants still contributed to the cumulative overrun.

## Why it happened

The pilot had per-run request and wall-clock limits, plus a user-facing local-provider approval flag. It lacked persistent cross-run accounting and a separate approval step for increasing the experiment-wide cap. The operator could start new runs after earlier attempts, including from later task sessions. The check therefore bounded individual runs but not total use.

## Safeguard now in place

- `BUDGET_POLICY.json` keeps the original 24 generation-attempt cap and sets warm-ups to zero unless separately approved.
- `BUDGET_STATE.json` imports the observed 133 attempts and two warm-up requests; both default allowances are exhausted.
- `budget.py` reconciles committed run evidence with durable reservation records, uses a cross-process lock, and persists a reservation before each model request. Provider errors count.
- `BUDGET_APPROVALS.json` starts empty. Raising a limit requires the interactive approval command, an explicit confirmation phrase, and an authorization reference. The provider/cost approval flag does not override this gate.
- `LocalOllama.generate()` and `prepare()` reserve immediately before their respective `/api/chat` request. The CLI checks capacity before initializing a run. Offline tests prove exhaustion prevents the model request and that history persists across guard instances.

Under the present recorded use, no further generation or warm-up request can pass the guard. The regression tests and release packaging do not invoke Ollama. This safeguard is a software process control and does not prevent a user from deliberately editing/deleting local files or bypassing the adapter; keep the budget state and approvals in reviewed version control.

## Interpretation

The final paired run remains 34/34 returned generations. That describes the final run only. Across the full development history, only 94/133 attempts returned a generation. Neither figure is a statistically reliable model-performance estimate; cases were reused during development and provider failures are part of the disclosed history. The failed attempts do not establish whether the runtime did partial work before a timeout.
