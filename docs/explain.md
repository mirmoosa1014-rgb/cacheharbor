# How to explain it

A cache is a small shelf holding recently used information. Two programs share the shelf. Giving each half can be wasteful: one program repeatedly reuses a small collection while another reads a stream of things it never uses again. CacheHarbor measures what was reused, gives space to the program likely to benefit, then checks whether that decision actually reduced misses.

## Reviewer questions

1. **What is a line?** One abstract address, not a measured number of bytes.
2. **What is LRU?** On overflow, evict the least recently accessed line.
3. **Can tenants share addresses?** Addresses are namespaced; they do not share data.
4. **Why profile separately?** Real quotas hide the benefit of larger allocations; the monitor estimates counterfactual miss curves.
5. **Can the policy see the future?** No. Its input is the completed preceding window only.
6. **Why not use AI?** The objective can be enumerated exactly in a tiny space; there is no demonstrated prediction task requiring ML here.
7. **Is the optimization globally optimal?** It is exact for the previous-window miss curves, not for future accesses or the whole run.
8. **Does reducing misses mean the CPU is faster?** Not necessarily. Timing, memory-level parallelism, coherence and hardware overhead are absent.
9. **When does it lose?** Shared LRU handles the held-out loop-cliff case better; adaptive needs observations and can misallocate during transitions.
10. **Who made it?** The user supplied portfolio goals and design direction. Codex chose this scoped idea, implemented it, tested it and prepared the evidence. No unsupported authorship claims are made.
