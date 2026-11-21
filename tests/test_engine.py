import itertools, random, unittest
from cacheharbor.engine import LRU, Monitor, allocate, trace, simulate, compare
from cacheharbor.experiment import TRAIN, TEST

class EngineTests(unittest.TestCase):
    def test_lru_hand_trace(self):
        c=LRU(2)
        self.assertEqual([c.access(x) for x in [1,2,1,3,2]],[False,False,True,False,False])
        self.assertEqual(list(c.lines),[3,2])
    def test_resize_evicts_oldest(self):
        c=LRU(3)
        for x in [1,2,3,1]:c.access(x)
        self.assertEqual(c.resize(1),2);self.assertEqual(list(c.lines),[1])
        c.resize(4);self.assertTrue(c.access(1))
    def test_monitor_matches_independent_lru_oracle(self):
        # Independent list-based LRU with recency carried over window resets.
        rng=random.Random(11);monitor=Monitor(8);caches={c:[] for c in range(1,8)};misses={c:0 for c in caches}
        for i in range(600):
            x=rng.randrange(12);monitor.observe(x)
            for c,cache in caches.items():
                if x in cache:cache.remove(x)
                else:misses[c]+=1
                cache.append(x)
                if len(cache)>c:cache.pop(0)
            if (i+1)%100==0:
                curve=monitor.curve()
                for c in caches:self.assertEqual(curve[c],misses[c])
                monitor.clear_window();misses={c:0 for c in caches}
    def test_exhaustive_allocation_and_stable_tie(self):
        curves=[[10,8,4,3,1,0],[10,9,7,2,1,0]]
        a=allocate(curves,5,2)
        self.assertEqual(curves[0][a]+curves[1][5-a],min(curves[0][i]+curves[1][5-i] for i in range(1,5)))
        self.assertEqual(allocate([[0]*9]*2,8,3),3)
    def test_causal_prefix_and_first_window(self):
        t=trace(41,'phase_swap',1024);r=simulate(t,interval=128)
        changed=t[:512]+[(0,99999)]*512;s=simulate(changed,interval=128)
        self.assertEqual(r['history'][:4],s['history'][:4])
        self.assertEqual(r['history'][4]['quota'],s['history'][4]['quota'])
        self.assertEqual(r['history'][0]['quota'],[16,16])
        self.assertIsNone(r['history'][0]['decision_curves'])
    def test_capacity_and_accounting_all_policies(self):
        case=compare(length=1024)
        for r in case['results'].values():
            self.assertEqual(sum(r['accesses']),1024)
            self.assertEqual(sum(sum(w['misses']) for w in r['history']),sum(r['misses']))
            for w in r['history']:
                self.assertLessEqual(sum(w['occupancy']),32)
                if w['quota']:
                    self.assertEqual(sum(w['quota']),32)
                    self.assertTrue(all(1<=q<32 for q in w['quota']))
                    self.assertTrue(all(n<=q for n,q in zip(w['occupancy'],w['quota'])))
    def test_namespaces_and_partial_window(self):
        r=simulate([(0,1),(1,1),(0,1),(1,1)],'shared')
        self.assertEqual(r['misses'],[1,1]);self.assertEqual(r['history'][-1]['end'],4)
    def test_replay_and_split(self):
        self.assertEqual(trace(9),trace(9));self.assertNotEqual(trace(9),trace(10))
        self.assertFalse(set(TRAIN)&set(TEST))
    def test_invalid_arguments(self):
        for value in [True,1.5,-1,100001]:
            with self.subTest(seed=value),self.assertRaises(ValueError):trace(value)
        for kw in [dict(capacity=True),dict(interval=0),dict(policy='oracle'),dict(fixed_fraction=float('nan'))]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):simulate([(0,1)],**kw)
        for entries in [[],[(True,1)],[(0,-1)],[(2,1)],[(0,1.5)],['x']]:
            with self.subTest(entries=entries),self.assertRaises(ValueError):simulate(entries)
    def test_monotonic_curves(self):
        m=Monitor(32)
        for _,a in trace(length=512):m.observe(a)
        c=m.curve();self.assertTrue(all(a>=b for a,b in zip(c,c[1:])))

if __name__=='__main__':unittest.main()
