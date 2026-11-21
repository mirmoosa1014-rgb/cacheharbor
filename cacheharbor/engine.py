"""Fully associative, read-only LRU abstraction. One address is one cache line."""
from collections import OrderedDict
import random

FAMILIES = ('hot_stream', 'balanced', 'phase_swap', 'bursty', 'loop_cliff')
POLICIES = ('shared', 'equal', 'fixed', 'adaptive')

def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer from {low} to {high}')
    return value

class LRU:
    def __init__(self, capacity):
        self.capacity = integer(capacity, 1, 64, 'capacity')
        self.lines = OrderedDict()
    def resize(self, capacity):
        self.capacity = integer(capacity, 1, 64, 'capacity')
        evicted = 0
        while len(self.lines) > capacity:
            self.lines.popitem(last=False); evicted += 1
        return evicted
    def access(self, key):
        hit = key in self.lines
        if hit: self.lines.move_to_end(key)
        else:
            self.lines[key] = None
            if len(self.lines) > self.capacity: self.lines.popitem(last=False)
        return hit

class Monitor:
    """Bounded recency stack; histogram gives exact LRU miss counts for 1..C-1."""
    def __init__(self, capacity):
        self.capacity = capacity; self.stack = []; self.hist = [0] * (capacity+1)
    def observe(self, address):
        try: distance = self.stack.index(address)
        except ValueError: distance = self.capacity
        self.hist[distance] += 1
        if distance < self.capacity: self.stack.pop(distance)
        self.stack.insert(0, address)
        del self.stack[self.capacity:]
    def curve(self):
        return [sum(self.hist[c:]) for c in range(self.capacity+1)]
    def clear_window(self):
        self.hist = [0] * (self.capacity+1)  # Preserve recency across windows.

def allocate(curves, capacity, previous):
    """Exact enumeration, minimum one line per tenant; stable ties limit churn."""
    return min(range(1, capacity), key=lambda a: (curves[0][a]+curves[1][capacity-a], abs(a-previous), a))

def trace(seed=3001, family='phase_swap', length=8192):
    integer(seed, 0, 100000, 'seed'); integer(length, 512, 32768, 'length')
    if family not in FAMILIES: raise ValueError('unknown workload family')
    rng = random.Random(seed); output = []; counters = [0, 0]
    for i in range(length):
        tenant = int(rng.random() >= (.75 if family == 'bursty' and (i//512)%2 else .5))
        j = counters[tenant]; counters[tenant] += 1
        if family == 'hot_stream': address = rng.randrange(20) if tenant == 0 else 100000+j
        elif family == 'balanced': address = rng.randrange(12 if tenant == 0 else 14)
        elif family == 'phase_swap':
            hot = (i//1024)%2
            address = rng.randrange(20) if tenant == hot else 100000+j
        elif family == 'bursty':
            address = rng.randrange(24) if (i//768+tenant)%3 else 100000+j
        else: address = j % (17 if tenant == 0 else 13)
        output.append((tenant, address))
    return output

def simulate(accesses, policy='adaptive', capacity=32, interval=256, fixed_fraction=.5):
    integer(capacity, 4, 64, 'capacity'); integer(interval, 32, 2048, 'interval')
    if policy not in POLICIES: raise ValueError('unknown policy')
    if type(fixed_fraction) not in (int, float) or not 0 < fixed_fraction < 1: raise ValueError('fixed fraction must lie between zero and one')
    if not isinstance(accesses, (list, tuple)) or not 1 <= len(accesses) <= 32768: raise ValueError('1–32768 accesses required')
    for entry in accesses:
        if not isinstance(entry, (tuple, list)) or len(entry) != 2 or type(entry[0]) is not int or entry[0] not in (0,1) or type(entry[1]) is not int or entry[1] < 0:
            raise ValueError('accesses must be (tenant 0/1, nonnegative integer line)')
    allocation = max(1, min(capacity-1, round(capacity*fixed_fraction))) if policy == 'fixed' else capacity//2
    caches = [LRU(allocation), LRU(capacity-allocation)]; shared = LRU(capacity)
    monitors = [Monitor(capacity), Monitor(capacity)]
    total = [0,0]; misses = [0,0]; histories = []; evictions = 0; previous_curves = None
    for start in range(0, len(accesses), interval):
        if policy == 'adaptive' and previous_curves is not None:
            allocation = allocate(previous_curves, capacity, allocation)
            evictions += caches[0].resize(allocation)+caches[1].resize(capacity-allocation)
        counts = [0,0]; failures = [0,0]
        for tenant, address in accesses[start:start+interval]:
            hit = shared.access((tenant,address)) if policy == 'shared' else caches[tenant].access(address)
            total[tenant] += 1; counts[tenant] += 1
            if not hit: misses[tenant] += 1; failures[tenant] += 1
            monitors[tenant].observe(address)
        occupancy = [sum(k[0] == t for k in shared.lines) for t in (0,1)] if policy == 'shared' else [len(c.lines) for c in caches]
        histories.append(dict(start=start, end=min(start+interval,len(accesses)), quota=None if policy=='shared' else [allocation,capacity-allocation], occupancy=occupancy, accesses=counts, misses=failures, decision_curves=previous_curves))
        previous_curves = [m.curve() for m in monitors]
        for m in monitors: m.clear_window()
    return dict(policy=policy, capacity=capacity, interval=interval, accesses=total, misses=misses,
                miss_rate=sum(misses)/sum(total), tenant_miss_rates=[m/n if n else None for m,n in zip(misses,total)],
                resize_evictions=evictions, history=histories)

def compare(seed=3001, family='phase_swap', capacity=32, interval=256, fixed_fraction=.75, length=8192):
    accesses = trace(seed, family, length)
    return dict(seed=seed, family=family, synthetic=True, length=length, capacity=capacity,
                results={p:simulate(accesses,p,capacity,interval,fixed_fraction) for p in POLICIES})
