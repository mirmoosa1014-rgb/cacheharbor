# Architecture

`engine.py` contains the synthetic trace generator, real LRU caches, independent recency monitors, exact partition enumeration, and paired policy replay. `experiment.py` selects parameters before touching held-out families. `server.py` serves a small loopback-only API and plain browser app. The runtime uses only Python's standard library and browser-native JavaScript/SVG; there is no build or network dependency for the app.

A reference is `(tenant, line_address)`. Tenant namespaces are disjoint. Every access updates a fully associative read-only LRU. A miss inserts the line and evicts the oldest line if necessary. The shared baseline has one 32-line cache. Partitioned policies have two caches whose quotas sum to 32 and are always at least one. Resizing preserves recent lines, evicts excess lines, and never preloads missing lines.

The monitor keeps at most C recent distinct lines for each tenant. Recency distance d means d distinct lines were used more recently. A cache of capacity c misses iff d ≥ c; unseen or older-than-C lines are in bucket C. Window histograms reset; stacks do not. For a candidate A quota a, predicted misses are `curve_A[a] + curve_B[C-a]`. Enumerating a=1..C−1 is exact for this small decision space. Stable ties prefer the previous split, then smaller A.

At window k, adaptive decisions use only histograms completed in window k−1. The monitor is unaffected by the chosen real partition. Profiles are counterfactual LRU estimates, not exact predictions of the next window or the post-resize warm state. The experiment tests prefix invariance and verifies the profiler against an independently written LRU oracle. All policies see identical interleaved references, and cold-start misses are scored.

Requests are bounded to 512 bytes, capacity 4–64 lines, seed 0–100000 and 8192 references. A semaphore admits one simulation at a time. Incomplete bodies time out after five seconds. The app has no upload or shell command endpoints. Plots and controls use actual replay output. Export stays disabled while a request is pending or after a failure.
