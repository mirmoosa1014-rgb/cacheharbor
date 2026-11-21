const $=id=>document.getElementById(id), colors=['#E07A5F','#81B29A'], names={shared:'Shared LRU',equal:'Equal split',fixed:'Fixed / trained',adaptive:'Adaptive'};
let data=null,timer=null;
const pct=x=>(100*x).toFixed(1)+'%';
const svg=(body,w,h,label)=>`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${label}">${body}</svg>`;
const text=(x,y,t,size=11)=>`<text x="${x}" y="${y}" font-size="${size}" fill="#2B2A28">${t}</text>`;
function stop(){clearInterval(timer);timer=null;$('play').textContent='Play windows';}
function inspect(){if(!data)return;const policy=$('policy').value,r=data.results[policy],i=Number($('window').value),w=r.history[i];$('window-number').value=i+1;
 const quota=w.quota||w.occupancy,n=data.capacity;let blocks='';
 for(let j=0;j<n;j++){const tenant=j<quota[0]?0:1,col=j%8,row=Math.floor(j/8),x=400+(col-row)*37,y=36+(col+row)*15,c=colors[tenant];
 blocks+=`<g class="block" style="animation-delay:${Math.min(j,12)*.08}s"><ellipse cx="${x}" cy="${y+44}" rx="25" ry="9" fill="#6E675F" opacity=".12"/><path d="M${x},${y} l30,15 -30,15 -30,-15z" fill="${tenant===0?'#F0A48F':'#81B29A'}"/><path d="M${x-30},${y+15} l30,15 0,27 -30,-15z" fill="${c}"/><path d="M${x},${y+30} l30,-15 0,27 -30,15z" fill="${tenant===0?'#C45B42':'#3D405B'}"/><title>Tenant ${tenant===0?'A':'B'}: line ${j+1}</title></g>`;}
 const left=400-(Math.ceil(n/8)-1)*37-45,right=400+7*37+45,bottom=36+(7+Math.ceil(n/8)-1)*15+65;
 $('floor').innerHTML=svg(blocks,800,320,'Cache allocation: '+quota[0]+' lines A, '+quota[1]+' lines B').replace('0 0 800 320',`${left} 0 ${right-left} ${bottom}`);
 $('allocation').textContent=`${names[policy]} · A ${quota[0]} / B ${quota[1]} lines${w.quota?' allocated':' resident (no quotas)'}`;
 $('epoch').textContent=`References ${w.start+1}–${w.end} · misses A ${w.misses[0]}/${w.accesses[0]}, B ${w.misses[1]}/${w.accesses[1]} · resident at window end: ${w.occupancy.join(' / ')}`;
 const curves=w.decision_curves;
 if(!curves){$('curves').innerHTML='<p>No earlier window exists. The adaptive policy starts with an equal split.</p>';$('decision').textContent='Cold-start misses are included.';}
 else{const max=Math.max(1,...curves.flat()),width=460,height=170;let body='';
 [0,1].forEach(t=>{const points=curves[t].slice(1,n).map((v,j)=>`${30+j/(n-2)*400},${140-v/max*110}`).join(' ');body+=`<polyline points="${points}" fill="none" stroke="${colors[t]}" stroke-width="3"/>`;});
 body+=text(30,163,'1 line')+text(350,163,`${n-1} lines`)+text(30,15,`Previous-window misses · max ${max}`);
 $('curves').innerHTML=svg(body,width,height,'Miss curves from prior accesses for tenants A and B');
 $('decision').textContent=policy==='adaptive'?`Chosen split minimizes A[a] + B[${n}−a]; ties stay nearest the last split. These curves describe the previous window, not this one.`:'Curves shown for comparison; this baseline does not use them.';
 }
 $('fairness').textContent=`${names[policy]} · whole-run miss rates: A ${pct(r.tenant_miss_rates[0])}, B ${pct(r.tenant_miss_rates[1])}. ${r.resize_evictions} lines evicted by resizing.`;
}
function render(){stop();$('window').max=data.results.adaptive.history.length-1;$('window').value=0;$('window').disabled=false;$('play').disabled=false;$('download').disabled=false;
 $('scores').innerHTML=Object.entries(data.results).map(([p,r])=>`<div class="bar-row"><span>${names[p]}</span><div class="bar-track"><div class="bar-fill" style="width:${100*r.miss_rate}%"></div></div><b>${pct(r.miss_rate)}</b></div>`).join('');
 let body='';const hues=['#3D405B','#6E675F','#3D5A80','#E07A5F'];
 Object.entries(data.results).forEach(([p,r],k)=>{const points=r.history.map((w,j)=>`${45+j/(r.history.length-1)*1000},${180-150*(w.misses[0]+w.misses[1])/(w.accesses[0]+w.accesses[1])}`).join(' ');body+=`<polyline points="${points}" fill="none" stroke="${hues[k]}" stroke-width="2"/>`+`<line x1="${45+k*245}" y1="217" x2="${65+k*245}" y2="217" stroke="${hues[k]}" stroke-width="3"/>`+text(73+k*245,220,names[p]);});
 body+=text(5,30,'100%')+text(12,180,'0%')+text(45,200,'First window')+text(930,200,'Last window');$('timeline').innerHTML=svg(body,1100,235,'Window miss-rate comparison for four policies');inspect();
}
$('controls').addEventListener('submit',async e=>{e.preventDefault();stop();$('download').disabled=true;$('play').disabled=true;$('status').textContent='Replaying the same accesses through four cache policies…';document.querySelectorAll('#controls input,#controls select,#run').forEach(x=>x.disabled=true);
 try{const response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seed:Number($('seed').value),family:$('family').value,capacity:Number($('capacity').value)})});const result=await response.json();if(!response.ok)throw Error(result.error);data=result;render();$('status').textContent=`Complete · ${data.length.toLocaleString()} identical references per policy · seed ${data.seed} · ${data.family}`;}
 catch(e){$('status').textContent='Run failed: '+e.message;}
 finally{document.querySelectorAll('#controls input,#controls select,#run').forEach(x=>x.disabled=false);}
});
$('window').addEventListener('input',()=>{stop();inspect();});$('policy').addEventListener('change',()=>{stop();inspect();});
$('play').addEventListener('click',()=>{if(timer){stop();return;}$('play').textContent='Pause';timer=setInterval(()=>{if(Number($('window').value)>=Number($('window').max)){stop();return;}$('window').value=Number($('window').value)+1;inspect();},800);});
$('download').addEventListener('click',()=>{if(!data||$('download').disabled)return;const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`cacheharbor-${data.family}-${data.seed}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
fetch('/api/meta').then(r=>{if(!r.ok)throw Error('metadata unavailable');return r.json();}).then(m=>{$('benchmark').textContent=`Saved benchmark: ${m.seeds_per_family} held-out seeds × 3 unseen families, ${m.length.toLocaleString()} references per replay. Validation-selected window: ${m.config.interval} references. Fixed split: ${100*m.config.fixed_fraction}% to A. Capacity changes in this demo are exploratory; tuning used 32 lines.`;}).catch(()=>{$('benchmark').textContent='Saved benchmark metadata unavailable.';});
$('controls').requestSubmit();
