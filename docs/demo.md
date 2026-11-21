# A 90-second walkthrough

1. Start `python3 -m cacheharbor.server`, then open http://127.0.0.1:8767. The phase-swap example loads automatically.
2. Clay blocks represent tenant A's allocated cache lines; sage blocks represent B's. Move the window slider beyond the first window to reveal the previous window's miss curves.
3. Switch to Shared LRU. The blocks now show occupied lines at the end of the window, not quotas. Read the caption before comparing them.
4. Compare whole-run miss bars and each tenant's rate. Play the window sequence or scrub it with the keyboard. There is no automatic animation playback; reduced motion disables block entrances.
5. Select Loop-size cliff, run, and see Shared LRU outperform the adaptive partitioner. Equal partitions can miss almost every access from a tenant whose loop is just larger than its quota.
6. Export the replay. It contains the exact seed, parameters, miss counts, resident counts and prior-window evidence. No private data is used.

Changing cache capacity is an exploratory intervention. The saved interval and fixed fraction were tuned at 32 lines; results at other capacities are not part of the committed benchmark.
