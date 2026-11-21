# Evaluation

Full experiment: 12 seeds per family, 8192 references per replay, 32 cache lines, four policies. Training and validation each use hot_stream and balanced, with seeds 100–111 and 1000–1011 respectively. Evaluation uses unseen phase_swap, bursty and loop_cliff families with seeds 3000–3011. Families are intentionally small synthetic archetypes, not representative CPU traces.

Four fixed fractions are scored on 24 training traces, then four adaptive intervals on 24 validation traces. The selected fraction is 0.625 and the interval is 128 global references. The held-out evaluation consists of 36 paired traces × four policies = 144 policy replays. Including selection, the full run performs 336 policy replays. No test-family result changes the config.

| Held-out family | Shared LRU | Equal | Fixed | Adaptive |
|---|---:|---:|---:|---:|
| phase_swap | 69.20% | 60.93% | 61.13% | 53.95% |
| bursty | 57.73% | 56.97% | 55.02% | 48.59% |
| loop_cliff | 0.37% | 49.88% | 50.49% | 0.94% |

Values are mean miss rates. [paired.csv](../results/paired.csv) contains seed-level rows and per-tenant rates. Figure error bars are min–max across 12 seeds, not confidence intervals. [benchmark.json](../results/benchmark.json) records selection scores and seed lists. All traces are generated locally using Python's seeded standard-library RNG.

## Counterexample

The saved [counterexample](../results/counterexample.json) maximizes adaptive minus the best of the three baselines over the held-out seeds. It is loop_cliff seed 3002: adaptive 1.111% versus shared 0.366% misses. This was selected after evaluation to illustrate a failure, never to retune. Adaptive does better than equal on every tested seed, but it is not universally the best policy.

## Scope and limitations

No timing, IPC, miss penalty, energy, prefetching, writes, coherence, inclusion, associativity conflicts or memory-level parallelism is modeled. Profiling work is simulated for all policies for comparable output and is not charged against a hardware budget. Resize evictions are counted, but their CPU cost is not modeled. Minimum one line per tenant is enforced; fairness is not optimized. Decisions can lag changing locality and benefit one tenant at the other's expense. Synthetic improvements do not establish silicon performance.

Quick mode uses two seeds per split and 2048 references, selects its own parameters, and writes to a separate directory in the documented command; it is a smoke check, not the source of the published numbers.
