"""Split before selection; paired test traces never influence the policy config."""
import argparse, csv, json, statistics
from pathlib import Path
from .engine import trace, simulate, compare, POLICIES
ROOT = Path(__file__).resolve().parents[1]
TRAIN = ('hot_stream','balanced')
TEST = ('phase_swap','bursty','loop_cliff')

def mean(values): return statistics.mean(values)
def experiment(quick=False, output=None):
    output=Path(output) if output else ROOT/'results'; output.mkdir(parents=True,exist_ok=True)
    length=2048 if quick else 8192; n=2 if quick else 12
    training=[trace(s,f,length) for f in TRAIN for s in range(100,100+n)]
    fractions=[.25,.5,.625,.75]
    fixed_scores={str(v):mean(simulate(t,'fixed',fixed_fraction=v)['miss_rate'] for t in training) for v in fractions}
    fraction=min(fractions,key=lambda v:(fixed_scores[str(v)],abs(v-.5)))
    validation=[trace(s,f,length) for f in TRAIN for s in range(1000,1000+n)]
    intervals=[128,256,512,1024]
    interval_scores={str(v):mean(simulate(t,'adaptive',interval=v)['miss_rate'] for t in validation) for v in intervals}
    interval=min(intervals,key=lambda v:(interval_scores[str(v)],v))
    rows=[]; worst=None; examples={}
    for family in TEST:
        for seed in range(3000,3000+n):
            case=compare(seed,family,interval=interval,fixed_fraction=fraction,length=length)
            delta=case['results']['adaptive']['miss_rate']-min(case['results'][p]['miss_rate'] for p in ('shared','equal','fixed'))
            if worst is None or delta>worst[0]: worst=(delta,case)
            examples.setdefault(family,case)
            for policy,r in case['results'].items():
                rows.append(dict(family=family,seed=seed,policy=policy,miss_rate=r['miss_rate'],tenant_a=r['tenant_miss_rates'][0],tenant_b=r['tenant_miss_rates'][1],resize_evictions=r['resize_evictions']))
    summary={f:{p:mean(r['miss_rate'] for r in rows if r['family']==f and r['policy']==p) for p in POLICIES} for f in TEST}
    config=dict(capacity=32,interval=interval,fixed_fraction=fraction)
    data=dict(synthetic=True,quick=quick,length=length,seeds_per_family=n,config=config,training_families=TRAIN,test_families=TEST,training_seeds=list(range(100,100+n)),validation_seeds=list(range(1000,1000+n)),test_seeds=list(range(3000,3000+n)),fixed_training_scores=fixed_scores,interval_validation_scores=interval_scores,summary=summary,worst_adaptive_minus_best_baseline=worst[0])
    (output/'benchmark.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    (output/'counterexample.json').write_text(json.dumps(worst[1],separators=(',',':'),allow_nan=False)+'\n')
    (output/'demo.json').write_text(json.dumps(examples['phase_swap'],separators=(',',':'),allow_nan=False)+'\n')
    with (output/'paired.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(data,indent=2));return data
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true');parser.add_argument('--output',type=Path);args=parser.parse_args();experiment(args.quick,args.output)
