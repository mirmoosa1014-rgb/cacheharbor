# Decision model and why there is no neural network

CacheHarbor uses a measured reuse model and exhaustive bounded optimization. This is not a learned classifier or neural predictor. The input is a past-window stack-distance histogram, and the candidate decision space has just 31 feasible splits at the benchmark capacity. Adding ML here would obscure an exact, interpretable baseline without a demonstrated need.

The fixed split is selected from four candidates on training traces. The adaptive interval is selected from four candidates on disjoint validation seeds. These are parameter-selection steps, not a claim of trained AI. The saved config, candidate scores, family lists and exact seeds are in `results/benchmark.json`.

The objective is total misses, not fairness, power, wall-clock throughput or weighted speedup. No hardware measurements or performance counters are involved. No future references, workload family labels, or hidden working-set sizes enter the allocation function.

The main conceptual source is [Qureshi and Patt, Utility-Based Cache Partitioning, technical report (2006)](https://hps.ece.utexas.edu/pub/TR-HPS-2006-009.pdf). It motivates allocation by benefit rather than demand. This project is a small fully associative educational abstraction; it does not reproduce that paper's sampled hardware monitors, set-associative architecture or reported performance.
