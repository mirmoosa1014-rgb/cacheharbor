"""Render only from saved paired experiments; no fabricated plot values."""
from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
b=json.loads((ROOT/'results/benchmark.json').read_text());demo=json.loads((ROOT/'results/demo.json').read_text());counter=json.loads((ROOT/'results/counterexample.json').read_text())
rows=list(csv.DictReader((ROOT/'results/paired.csv').open()))
colors=['#3D405B','#6E675F','#3D5A80','#E07A5F'];policies=['shared','equal','fixed','adaptive'];names=['Shared LRU','Equal','Fixed / trained','Adaptive']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.facecolor':'#F7F4EF','figure.facecolor':'#E6E1D8','text.color':'#2B2A28','axes.labelcolor':'#2B2A28'})
fig,axs=plt.subplots(2,2,figsize=(13,9),layout='constrained')
ax=axs[0,0]
for k,p in enumerate(policies):
 for j,f in enumerate(b['test_families']):
  vals=np.array([float(r['miss_rate'])*100 for r in rows if r['policy']==p and r['family']==f]);x=j+(k-1.5)*.18
  ax.bar(x,vals.mean(),.16,color=colors[k],label=names[k] if j==0 else None)
  ax.errorbar(x,vals.mean(),yerr=[[vals.mean()-vals.min()],[vals.max()-vals.mean()]],color='#2B2A28',capsize=2,lw=.8)
ax.set(xticks=range(3),xticklabels=['Phase swap','Bursty','Loop cliff'],ylabel='Misses / 100 references',title='A  ·  Held-out family comparison');ax.legend(fontsize=8,ncols=2);ax.set_ylim(0,100)
ax=axs[0,1]
for k,p in enumerate(policies):
 h=demo['results'][p]['history'];ax.plot([w['end'] for w in h],[sum(w['misses'])/sum(w['accesses'])*100 for w in h],color=colors[k],lw=1.4,label=names[k])
ax.set(xlabel='References processed',ylabel='Window miss rate (%)',title='B  ·  Phase-swap replay / seed 3000',ylim=(0,100));ax.grid(alpha=.15)
ax=axs[1,0];h=demo['results']['adaptive']['history'];x=[w['start'] for w in h];a=[w['quota'][0] for w in h]
ax.fill_between(x,a,step='post',color='#E07A5F',alpha=.7,label='A');ax.fill_between(x,a,32,step='post',color='#81B29A',alpha=.7,label='B')
ax.step(x,a,where='post',color='#3D405B',lw=1);ax.set(xlabel='References processed',ylabel='Allocated lines (32 total)',title='C  ·  Past-window allocation responds after a change',ylim=(0,32));ax.legend(ncols=2,loc='upper right')
ax=axs[1,1]
for k,p in enumerate(policies):
 r=counter['results'][p];rates=np.array(r['tenant_miss_rates'])*100
 ax.scatter(rates[0],rates[1],s=80,color=colors[k]);ax.annotate(names[k],rates,xytext=[(10,10),(-38,10),(10,-18),(10,27)][k],textcoords='offset points',fontsize=9)
ax.set(xlabel='Tenant A miss rate (%)',ylabel='Tenant B miss rate (%)',title=f"D  ·  Failure case / {counter['family']} / seed {counter['seed']}",xlim=(-3,105),ylim=(-3,105));ax.grid(alpha=.15)
fig.suptitle('CACHEHARBOR  /  Equal space is not equal utility',fontsize=22,fontweight='bold')
fig.supxlabel('Synthetic, fully associative read-only traces · 12 paired seeds per unseen family · bars: mean, whiskers: min–max · no CPU speedup claim',fontsize=10)
fig.savefig(ROOT/'docs/images/evaluation.png',dpi=160);plt.close(fig)
