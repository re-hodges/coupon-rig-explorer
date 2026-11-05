"""Assemble the self-contained coupon explorer page (band-mounted rig, v3).

    python build_page_v3.py

Reads grid_v3.json, the four markdown documents and the sensitivity figures, and
emits explorer_v2/index.html -- one file, no build step, no server, no network,
no dependencies.

SIX TABS: parameter explorer, RBC in 3D, sensitivity and SHAP, model details,
glossary, data sources.
"""
from __future__ import annotations
import os, sys, json, base64, glob, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mdlite

OUT = ROOT
os.makedirs(OUT, exist_ok=True)

MATNAME = {"PE": "HDPE", "STL": "bare steel", "GRA": "graphene-coated steel",
           "FAB": "non-woven fabric"}
HARVEST_DAYS = [5, 7, 10]


def load_grid():
    g = json.load(open(os.path.join(HERE, "grid_v3.json")))
    series, meta = {}, {}
    for a in g:
        k = a["key"]
        series[k] = {"t": a["t"], "Xp": a["Xp"], "Xn": a["Xn"], "Xh": a["Xh"],
                     "Lf": a["Lf"], "JA": a["JA"]}
        meta[k] = {c: a[c] for c in
                   ("material","photoperiod","timer_h","delivered_h","rpm","n_shear",
                    "shelter","load","f_wet","period_s","submerged_s","emergent_s",
                    "tau_Pa","tau_free_Pa","I0","k_det","laminar_ok","Re","o2_um")}
        meta[k]["harvest_mg"] = a["harvest_mg"]
    return series, meta


def axis_tokens(meta, idx):
    """Exact key tokens for one axis, read back OUT of the keys themselves.

    Reformatting a float here (0.5 -> '0.5' vs '0.50') would silently break every
    lookup, so the option values are the strings the keys actually contain.
    """
    seen = {}
    for k in meta:
        t = k.split("|")[idx]
        seen[t] = float(t) if t.replace(".", "").replace("-", "").isdigit() else t
    return [t for t, _ in sorted(seen.items(), key=lambda kv: kv[1])]


def b64img(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return None
    return base64.b64encode(open(p, "rb").read()).decode()


CSS = """
:root{--bg:#14171a;--panel:#1b1f23;--panel2:#20252a;--ink:#e6e8ea;--mut:#949ca6;
--line:#2d343a;--acc:#5fb3e0;--warn:#e8755c;--warnbg:#2e1d19;
--PE:#5fb3e0;--STL:#b9c0c8;--GRA:#c08cf0;--FAB:#4fc9a0;
--p:#4fc3a1;--n:#5a9fe0;--h:#e8835a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{padding:18px 26px 0}
h1{font-size:19px;margin:0 0 2px;font-weight:600}
.sub{color:var(--mut);font-size:12.5px;margin-bottom:14px}
nav{display:flex;gap:2px;border-bottom:1px solid var(--line);padding:0 26px}
nav button{background:none;border:0;border-bottom:2px solid transparent;padding:9px 15px;
 font:inherit;font-size:13.5px;color:var(--mut);cursor:pointer}
nav button:hover{color:var(--ink)}
nav button.on{color:var(--acc);border-bottom-color:var(--acc);font-weight:600}
main{padding:20px 26px 60px;max-width:1180px}
.wrap{display:grid;grid-template-columns:238px minmax(0,1fr) 252px;gap:22px;
 align-items:start}
/* summary cards now ride in a right-hand rail rather than a band above the charts,
   so the charts get the full height of the viewport. Below 1250px the rail drops
   under the charts and the cards flow horizontally again. */
.side{grid-column:3}
@media(max-width:1250px){.wrap{grid-template-columns:238px minmax(0,1fr)}
 .side{grid-column:1/-1}
 .side .cards{grid-template-columns:repeat(auto-fit,minmax(132px,1fr))}}
.ctl{border:1px solid var(--line);border-radius:7px;padding:14px;background:var(--panel)}
.ctl label{display:block;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;
 color:var(--mut);margin:13px 0 4px}
.ctl label:first-child{margin-top:0}
.ctl select{width:100%;padding:5px;border:1px solid var(--line);border-radius:4px;
 background:var(--panel2);color:var(--ink);font:inherit;font-size:13px}
.val{float:right;color:var(--ink);font-weight:600;text-transform:none;letter-spacing:0}
.cards{display:grid;grid-template-columns:1fr;gap:9px;margin-bottom:0}
.card{border:1px solid var(--line);border-radius:6px;padding:9px 11px;background:var(--panel)}
.card .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
.card .v{font-size:17px;font-weight:600;margin-top:2px}
.card .u{font-size:11px;color:var(--mut)}
.card.bad{border-color:var(--warn);background:var(--warnbg)}
.card.bad .v{color:var(--warn)}
.chart{border:1px solid var(--line);border-radius:7px;background:var(--panel);
 padding:11px 13px;margin-bottom:13px}
.chart h3{margin:0 0 1px;font-size:13.5px;font-weight:600}
.chart .cap{color:var(--mut);font-size:11.5px;margin-bottom:7px}
canvas{width:100%;display:block}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:13px}
.doc{max-width:860px}
.doc h1{font-size:21px;margin:4px 0 10px}
.doc h2{font-size:16px;margin:26px 0 8px;padding-bottom:5px;border-bottom:1px solid var(--line)}
.doc h3{font-size:14px;margin:18px 0 6px}
.doc table{border-collapse:collapse;width:100%;margin:11px 0;font-size:12.5px}
.doc th,.doc td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
.doc th{background:var(--panel2);font-weight:600}
.doc td{background:var(--panel)}
.doc code{background:var(--panel2);padding:1px 4px;border-radius:3px;font-size:12px;color:#cfe6f5}
.doc pre{background:var(--panel2);padding:11px;border-radius:6px;overflow-x:auto}
.doc pre code{background:none;padding:0}
.doc blockquote{margin:12px 0;padding:9px 13px;border-left:3px solid var(--warn);
 background:var(--warnbg);color:#f0c4b8}
.doc a{color:var(--acc)}
.tt{position:relative;border:1px solid var(--line);border-radius:7px;background:var(--panel);padding:12px}
.tt img{width:100%;display:block;cursor:grab;border-radius:4px}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:12.5px;color:var(--mut)}
.sw{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.dash{display:inline-block;width:18px;border-top:2px dashed currentColor;margin-right:5px;vertical-align:3px}
.solid{display:inline-block;width:18px;border-top:2px solid currentColor;margin-right:5px;vertical-align:3px}
.note{font-size:12.5px;color:var(--mut);margin-top:9px}
.calc{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
.calc summary{cursor:pointer;color:var(--acc);font-size:12.5px;font-weight:600;list-style:revert}
.calc p{font-size:12.5px;color:var(--mut);margin:8px 0}
.calc strong{color:var(--ink)}
.calc pre{background:var(--panel2);padding:9px 11px;border-radius:5px;overflow-x:auto;
 font-size:11.5px;line-height:1.5;margin:8px 0}
.calc code{color:#cfe6f5}
.ph{display:inline-block;background:#3a3016;border:1px solid #6b5a22;color:#e8d08a;
 border-radius:3px;padding:0 5px;font-size:11px;font-weight:600}
"""


# CSS additions for the sensitivity tab
CSS += """
.figbox{border:1px solid var(--line);border-radius:7px;background:var(--panel);
 padding:13px 15px;margin:16px 0}
.figbox h3{margin:0 0 2px;font-size:14px;font-weight:600}
.figbox .cap{color:var(--mut);font-size:12px;margin-bottom:9px;max-width:780px}
.figbox img{width:100%;display:block;border-radius:5px;background:#0c0f12}
.figrow{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:900px){.figrow{grid-template-columns:1fr}}
.slider{width:100%;accent-color:var(--acc)}
.lede{max-width:820px;color:var(--mut);font-size:13px}
/* The 3D scene escapes the 860px prose column: the canvas sizes itself from its
   parent's clientWidth, so a wider container IS a bigger render. Sliders sit above
   the graphic, the click readout rides in a right-hand rail. */
.scenewrap{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:18px;
 align-items:start;max-width:1400px;margin:16px 0}
.scenewrap .sldrow{margin-top:0;margin-bottom:11px}
.scenewrap .rd{margin-top:0}
.scenside .note{margin-top:10px}
@media(max-width:1100px){.scenewrap{grid-template-columns:minmax(0,1fr)}}
/* variable key at the foot of the Sensitivity tab: wider than .doc and denser,
   because it carries seven columns including a free-text source for each input */
.keywrap{max-width:1180px}
.keywrap table{border-collapse:collapse;width:100%;margin:11px 0;font-size:11.5px}
.keywrap th,.keywrap td{border:1px solid var(--line);padding:4px 7px;text-align:left;
 vertical-align:top}
.keywrap th{background:var(--panel2);font-weight:600;position:sticky;top:0}
.keywrap td{background:var(--panel)}
.keywrap code{background:var(--panel2);padding:1px 4px;border-radius:3px;font-size:11px;
 color:#cfe6f5}
.keywrap .srccell{color:var(--mut);font-size:11px;max-width:340px}
.keywrap .rolecell{color:var(--mut);font-size:11px;display:inline-block;margin-top:3px}
.lede strong{color:var(--ink)}
.sldrow{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:12px}
.sldrow label{display:block;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;
 color:var(--mut)}
.rd{border:1px solid var(--line);border-radius:7px;background:var(--panel);
 padding:12px 14px;margin-top:12px;min-height:74px}
.rdhint{color:var(--mut);font-size:12.5px}
.rdhead{font-size:12.5px;color:var(--mut);margin-bottom:9px}
.rdhead strong{color:var(--ink)}
.rdtag{background:#3a3016;border:1px solid #6b5a22;color:#e8d08a;border-radius:3px;
 padding:0 5px;font-size:11px;font-weight:600;margin-left:4px}
.rdbar{display:flex;height:7px;border-radius:4px;overflow:hidden;margin-bottom:11px;
 background:var(--panel2)}
.rdbar span{display:block;height:100%}
.rdgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:9px}
.rdgrid>div{border:1px solid var(--line);border-radius:5px;padding:7px 9px;background:var(--panel2)}
.rdgrid .k{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;
 color:var(--mut)}
.rdgrid .v{display:block;font-size:16px;font-weight:600;margin-top:2px}
.rdgrid .u{display:block;font-size:10.5px;color:var(--mut)}
"""

JS = r"""
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const MCOL={PE:'#5fb3e0',STL:'#b9c0c8',GRA:'#c08cf0',FAB:'#4fc9a0'};
const GCOL={Xp:'#4fc3a1',Xn:'#5a9fe0',Xh:'#e8835a'};
const GNAME={Xp:'phototrophs',Xn:'nitrifiers',Xh:'heterotrophs'};
const MORDER=['FAB','PE','STL','GRA'];
const HARVEST=[5,7,10];

/* Which arms are selected. "all" materials and "both" photoperiods fan out here,
   so every chart draws the same arm list and the legend stays truthful.
   Key order follows build_grid_v3: material|photoperiod|rpm|n_shear|shelter|load */
function key(m,p){return [m,p,$('#rpm').value,$('#nsh').value,$('#shel').value,$('#load').value].join('|');}
function arms(){
  const mv=$('#mat').value, pv=$('#phot').value;
  const ms = mv==='__all' ? MORDER.filter(m=>MATS.includes(m)) : [mv];
  const ps = pv==='__both' ? ['summer','winter'] : [pv];
  const out=[];
  for(const m of ms) for(const p of ps){const k=key(m,p); if(SERIES[k]) out.push({k,m,p});}
  return out;
}
const multiM=()=>$('#mat').value==='__all';
const multiP=()=>$('#phot').value==='__both';
/* Arms the Y AXIS is scaled over: the selected materials against BOTH photoperiods,
   always. Scaling to the selected arms only meant the identical winter curve was drawn
   about 10% shorter once summer was added, because summer raised the axis maximum —
   the data never changed, the axis did. Rotation, shear, shelter and load still
   rescale, which is correct: those change the physics on display. */
function axisArms(){
  const mv=$('#mat').value;
  const ms = mv==='__all' ? MORDER.filter(m=>MATS.includes(m)) : [mv];
  const out=[];
  for(const m of ms) for(const p of ['summer','winter']){
    const k=key(m,p); if(SERIES[k]) out.push({k:k,m:m,p:p});
  }
  return out.length?out:arms();
}
/* The photoperiod is named in every key, not only when both are shown. A single
   photoperiod view otherwise gave no on-chart indication of WHICH one, which is easy
   to misread given that winter can yield the higher flux. Winter is dashed always. */
function photoKey(){
  const pv=$('#phot').value;
  if(pv==='__both') return [{c:'#949ca6',t:'summer 15.50 h'},{c:'#949ca6',t:'winter 8.87 h',d:1}];
  return pv==='winter' ? [{c:'#949ca6',t:'winter solstice, 8.87 h timer',d:1}]
                       : [{c:'#949ca6',t:'summer solstice, 15.50 h timer'}];
}

const DPR=Math.max(1,window.devicePixelRatio||1);
function fit(c,h){const w=c.parentNode.clientWidth-26;c.width=w*DPR;c.height=h*DPR;
  c.style.height=h+'px';const x=c.getContext('2d');x.setTransform(DPR,0,0,DPR,0,0);return [x,w,h];}
function axes(x,w,h,xm,ym,xl,yl){
  const L=54,R=12,T=10,B=30;x.clearRect(0,0,w,h);
  x.strokeStyle='#3a4248';x.lineWidth=1;x.beginPath();
  x.moveTo(L,T);x.lineTo(L,h-B);x.lineTo(w-R,h-B);x.stroke();
  x.fillStyle='#949ca6';x.font='11px system-ui';
  for(let i=0;i<=4;i++){const v=ym*i/4,y=h-B-(h-B-T)*i/4;
    x.textAlign='right';x.fillText(fmt(v),L-6,y+3);
    if(i){x.strokeStyle='#252b30';x.beginPath();x.moveTo(L,y);x.lineTo(w-R,y);x.stroke();}}
  for(let i=0;i<=6;i++){const v=xm*i/6,px=L+(w-R-L)*i/6;
    x.textAlign='center';x.fillText(Math.round(v),px,h-B+14);}
  x.textAlign='center';x.fillText(xl,(L+w-R)/2,h-4);
  x.save();x.translate(14,(T+h-B)/2);x.rotate(-Math.PI/2);x.fillText(yl,0,0);x.restore();
  return {L,R,T,B};}
/* Harvest markers. Three coupons come off on each of days 5, 7 and 10, so those are
   the only days the model can ever be checked against -- worth seeing on every axis. */
function harvestMarks(x,g,w,h,xm){
  x.save();x.strokeStyle='rgba(232,208,138,.40)';x.lineWidth=1;x.setLineDash([3,3]);
  x.fillStyle='#e8d08a';x.font='10px system-ui';x.textAlign='center';
  for(const d of HARVEST){const px=g.L+(w-g.R-g.L)*d/xm;
    x.beginPath();x.moveTo(px,g.T);x.lineTo(px,h-g.B);x.stroke();
    x.fillText('d'+d,px,g.T+9);}
  x.restore();}
function fmt(v){if(v===0)return'0';const a=Math.abs(v);
  if(a>=100)return v.toFixed(0);if(a>=10)return v.toFixed(1);
  if(a>=1)return v.toFixed(2);return v.toPrecision(2);}
function line(x,g,w,h,t,y,ym,col,wd,dash){
  const{L,R,T,B}=g;x.save();x.strokeStyle=col;x.lineWidth=wd||1.8;
  if(dash)x.setLineDash([5,3]);
  x.beginPath();const xm=t[t.length-1];
  for(let i=0;i<t.length;i++){const px=L+(w-R-L)*t[i]/xm,
    py=h-B-(h-B-T)*Math.max(0,Math.min(y[i]/ym,1));i?x.lineTo(px,py):x.moveTo(px,py);}
  x.stroke();x.restore();}
function keyline(el,items){
  el.innerHTML=items.map(i=>`<span style="color:${i.c}">`+
    (i.d?'<span class="dash"></span>':'<span class="solid"></span>')+
    `</span><span style="color:#949ca6">${i.t}</span>`).join('&nbsp;&nbsp; ');}

function draw(){
  const A=arms();
  if(!A.length){$('#cards').innerHTML='<div class="card bad"><div class="k">no data</div>'+
    '<div class="v">—</div><div class="u">that combination was not run</div></div>';return;}
  const T=SERIES[A[0].k].t, perGuild = !multiM();
  const AX=axisArms();

  /* 1. biomass by guild (single material) or total per material (all materials) */
  let [x,w,h]=fit($('#cX'),212), ym=0, keys=[];
  if(perGuild){ for(const a of AX) for(const g of ['Xp','Xn','Xh']) ym=Math.max(ym,...SERIES[a.k][g]); }
  else { for(const a of AX){const s=SERIES[a.k];
      for(let i=0;i<T.length;i++) ym=Math.max(ym,s.Xp[i]+s.Xn[i]+s.Xh[i]);} }
  ym=ym*1.15||1;
  let g=axes(x,w,h,60,ym,'day','X  (g DW m\u207B\u00B2)');
  harvestMarks(x,g,w,h,60);
  for(const a of A){const s=SERIES[a.k], d=(a.p==='winter');
    if(perGuild){ for(const gl of ['Xh','Xn','Xp']) line(x,g,w,h,T,s[gl],ym,GCOL[gl],1.9,d); }
    else { const tot=T.map((_,i)=>s.Xp[i]+s.Xn[i]+s.Xh[i]);
           line(x,g,w,h,T,tot,ym,MCOL[a.m],1.9,d); }}
  keys = perGuild ? ['Xh','Xn','Xp'].map(gl=>({c:GCOL[gl],t:GNAME[gl]}))
                  : A.filter(a=>a.p===A[0].p).map(a=>({c:MCOL[a.m],t:MATNAME[a.m]}));
  keyline($('#kX'),keys.concat(photoKey()));
  $('#hX').textContent = perGuild ? 'Biomass by guild' : 'Total biomass by material';
  $('#capX').textContent = perGuild
    ? 'Per exposed coupon area A_exp = 12.90 cm², one face net of its magnet.'
    : 'Guilds are summed: with four materials overlaid, per-guild lines would be unreadable.';

  /* 2. film thickness */
  [x,w,h]=fit($('#cLf'),212); ym=0;
  for(const a of AX) ym=Math.max(ym,...SERIES[a.k].Lf);
  ym=Math.max(ym*1.15,0.45);
  g=axes(x,w,h,60,ym,'day','L_f  (mm)');
  const y1=h-g.B-(h-g.B-g.T)*Math.min(0.151/ym,1), y2=h-g.B-(h-g.B-g.T)*Math.min(0.412/ym,1);
  x.fillStyle='rgba(95,179,224,.13)';x.fillRect(g.L,y2,w-g.R-g.L,y1-y2);
  x.fillStyle='#949ca6';x.font='10.5px system-ui';x.textAlign='left';
  x.fillText('151–412 µm reported on RBC media',g.L+6,y2-4);
  harvestMarks(x,g,w,h,60);
  for(const a of A) line(x,g,w,h,T,SERIES[a.k].Lf,ym,
                         multiM()?MCOL[a.m]:'#5fb3e0',1.9,a.p==='winter');
  keyline($('#kLf'), (multiM()? A.filter(a=>a.p===A[0].p).map(a=>({c:MCOL[a.m],t:MATNAME[a.m]}))
                              : [{c:'#5fb3e0',t:MATNAME[A[0].m]}]).concat(photoKey()));

  /* 3. areal removal flux */
  [x,w,h]=fit($('#cJA'),238); ym=0;
  for(const a of AX) ym=Math.max(ym,...SERIES[a.k].JA);
  ym=ym*1.15||1;
  g=axes(x,w,h,60,ym,'day','J_A  (g N m\u207B\u00B2 d\u207B\u00B9)');
  harvestMarks(x,g,w,h,60);
  for(const a of A) line(x,g,w,h,T,SERIES[a.k].JA,ym,
                         multiM()?MCOL[a.m]:'#5fb3e0',2.2,a.p==='winter');
  let kj = multiM()? A.filter(a=>a.p===A[0].p).map(a=>({c:MCOL[a.m],t:MATNAME[a.m]}))
                   : [{c:'#5fb3e0',t:MATNAME[A[0].m]}];
  keyline($('#kJA'),kj.concat(photoKey()));

  /* cards. Geometry-derived values are identical across materials; anything that
     varies over the selection is shown as a range so nothing is silently hidden. */
  const M=A.map(a=>META[a.k]), m0=M[0];
  const rng=(f,dp,u)=>{const v=M.map(f),lo=Math.min(...v),hi=Math.max(...v);
    return lo===hi?lo.toFixed(dp)+u:lo.toFixed(dp)+'–'+hi.toFixed(dp)+u;};
  const allLam=M.every(z=>z.laminar_ok), minH=Math.min(...M.map(z=>z.harvest_mg.d5));
  const c=[
   ['wet fraction',m0.f_wet.toFixed(4),'of each revolution, at the band',''],
   ['cycle',m0.period_s.toFixed(0)+' s',
     m0.submerged_s.toFixed(1)+' s wet / '+m0.emergent_s.toFixed(1)+' s dry',''],
   ['light delivered',rng(z=>z.delivered_h,2,' h'),
     'of '+rng(z=>z.timer_h,2,' h')+' on the timer',''],
   ['O\u2082 per pass',m0.o2_um.toFixed(0)+' \u00B5m','\u221A(2Dt) over the emergent dwell',''],
   ['shear felt',m0.tau_Pa.toFixed(4)+' Pa',
     'of '+m0.tau_free_Pa.toFixed(4)+' Pa free-stream'+(allLam?'':' \u2014 OUT OF RANGE'),
     allLam?'':' bad'],
   ['k_det',m0.k_det.toFixed(4)+' /d','shear-modified, n='+m0.n_shear,''],
   ['harvest, day 5',rng(z=>z.harvest_mg.d5,1,' mg'),'3 coupons, A_exp only',
     minH>=1.0?'':' bad']];
  $('#cards').innerHTML=c.map(r=>`<div class="card${r[3]}"><div class="k">${r[0]}</div>`+
    `<div class="v">${r[1]}</div><div class="u">${r[2]}</div></div>`).join('');
}
window.addEventListener('DOMContentLoaded',()=>{
  $$('nav button').forEach(b=>b.onclick=()=>{
    $$('nav button').forEach(z=>z.classList.remove('on'));b.classList.add('on');
    $$('section').forEach(s=>s.style.display='none');
    $('#'+b.dataset.tab).style.display='';
    if(b.dataset.tab==='t1')draw();
    if(b.dataset.tab==='t2'){if(window.SCENE_DRAW)window.SCENE_DRAW();}});
  $$('#t1 select').forEach(e=>e.oninput=()=>{
    $$('.val').forEach(v=>{const s=$('#'+v.dataset.for);if(s)v.textContent=s.selectedOptions[0].dataset.short||s.value;});
    draw();});
  $$('.val').forEach(v=>{const s=$('#'+v.dataset.for);
    if(s)v.textContent=s.selectedOptions[0].dataset.short||s.value;});
  draw();window.addEventListener('resize',draw);});
"""


def sens_tab():
    """Sensitivity tab. EVERY index on this tab is computed on the differential
    equations themselves; see SENSITIVITY.md for the methods and their cost."""
    import csv

    def figure(name, title, cap, extra=""):
        b = b64img(name)
        if not b:
            return ('<div class="figbox"><h3>%s</h3><p class="note">%s not built yet.'
                    '</p></div>' % (title, name))
        return ('<div class="figbox"><h3>%s</h3><div class="cap">%s</div>'
                '<img alt="%s" src="data:image/png;base64,%s">%s</div>'
                % (title, cap, title, b, extra))

    # ---- the variable key, built from sa_evidence.csv -------------------------
    BADGE = {"4": "#1E7A4C", "3": "#2B5D7D", "2": "#8A6D1F", "1": "#8A5A1F", "0": "#C8102E"}

    def key_table():
        fp = os.path.join(HERE, "sa_evidence.csv")
        if not os.path.exists(fp):
            return '<p class="note">sa_evidence.csv not built yet.</p>'
        rows = list(csv.DictReader(open(fp, encoding="utf-8")))
        out = ['<table class="keytbl"><tr><th>input</th><th>units</th>'
               '<th>what it is, and how it enters the model</th>'
               '<th>nominal</th><th>swept over</th><th>evidence</th><th>source</th></tr>']
        for r in rows:
            try:
                rng = "%.4g &ndash; %.4g" % (float(r["range_lo"]), float(r["range_hi"]))
            except (ValueError, TypeError):
                rng = r.get("sampling", "")
            nom = r.get("nominal", "")
            try:
                nom = "%.4g" % float(nom)
            except (ValueError, TypeError):
                pass
            col = BADGE.get(r.get("evidence_score", ""), "#6B7280")
            role = r.get("role_in_model", "")
            what = r["definition"] + (
                '<br><span class="rolecell"><strong>In the model:</strong> %s.</span>' % role
                if role else "")
            out.append(
                '<tr><td><strong>%s</strong><br><code>%s</code></td><td>%s</td>'
                '<td>%s</td><td>%s</td>'
                '<td>%s</td><td><span style="color:%s;font-weight:600">%s</span></td>'
                '<td class="srccell">%s</td></tr>'
                % (r.get("display_name", r["parameter"]), r["parameter"], r["units"],
                   what, nom, rng, col, r["evidence_tier"], r["source"]))
        return "".join(out) + "</table>"

    # ---- headline numbers read from the analyses themselves -------------------
    def meta_val(fn, col, where=None):
        fp = os.path.join(HERE, fn)
        if not os.path.exists(fp):
            return None
        for r in csv.DictReader(open(fp, encoding="utf-8")):
            if where is None or all(r.get(k) == v for k, v in where.items()):
                return r.get(col)
        return None

    r2_flux = meta_val("sa_givendata_meta.csv", "R2_SRRC", {"target": "JA_d60"})
    r2_lin = meta_val("sa_givendata_meta.csv", "R2_SRC", {"target": "JA_d60"})
    st_top = meta_val("sa_sobol_ode.csv", "ST")
    st_name = meta_val("sa_sobol_ode.csv", "parameter")
    r2s = ("monotone R&sup2; %.2f against linear R&sup2; %.2f"
           % (float(r2_flux), float(r2_lin))) if r2_flux else ""

    hdr = """
<h1>Sensitivity &amp; SHAP</h1>
<p class="lede"><strong>Everything on this tab is computed on the differential equations.</strong>
There is no surrogate anywhere in it, and no machine learning anywhere in the model.
Shapley values are obtained by <strong>complete enumeration of every coalition</strong> on the
model itself, so they are exact and additivity holds by construction rather than by test.</p>
<p class="lede"><strong>Read the ranking as a measurement priority, not a physics claim.</strong>
An input's influence is measured over the range it was swept, and the widest ranges belong to
the inputs nobody has measured. So this answers &ldquo;what would be most worth measuring&rdquo;
&mdash; which is the question the coupon campaign exists to answer. The evidence axis below makes
that explicit. Note also that these runs are at <strong>15&nbsp;&deg;C</strong>, so the Arrhenius
coefficients are live inputs here, unlike the isothermal-20&nbsp;&deg;C ensemble where both were
inert.</p>

<h2>What would be worth measuring</h2>
"""
    f_diag = figure("fig_sa_evidence_impact.png",
        "Measurement priority \u2014 Morris influence against strength of evidence",
        "Impact is Morris &mu;* on the day-60 flux, taken on the ODE. Evidence is the tier "
        "each value carries in the Data sources tab, scored 0&ndash;4. The red band is weak "
        "evidence. <strong>K<sub>comp</sub>, k<sub>det</sub>, &phi;<sub>shear</sub> and "
        "k<sub>att</sub> sit in the measure-first corner</strong>; K<sub>P,p</sub>, "
        "S<sub>O</sub>, K<sub>I</sub> and D<sub>O2</sub> are low-impact and can be left "
        "unmeasured, which is just as useful for planning the campaign.")

    f_shap = figure("fig_sa_shapley_exact.png",
        "Per-arm attribution \u2014 exact Shapley values by complete coalition enumeration",
        "Each arm's eight highest-&mu;* inputs are toggled through all 2<sup>8</sup> = 256 "
        "coalitions, so the Shapley value is exact rather than sampled. Panel b is the exact "
        "counterpart of a SHAP beeswarm: one dot per arm. Horizontal position is that input's "
        "signed Shapley contribution in g&nbsp;N&nbsp;m<sup>-2</sup>&nbsp;d<sup>-1</sup>; "
        "colour is a different quantity \u2014 the value the input was SET to in that arm, as "
        "a position within the range it was swept over. Panel c aggregates to the three domain groups, which is also "
        "exact because grouped Shapley needs only 2<sup>3</sup> coalitions. Attributions are "
        "relative to the nominal baseline defined in SENSITIVITY.md.")

    f_sob = figure("fig_sa_sobol_ode.png",
        "Variance decomposition \u2014 Sobol' first-order and total indices on the ODE",
        "Saltelli design over the 19 continuous inputs plus material, evaluated on the model "
        "itself rather than on a surrogate. Bars are first-order S<sub>1</sub> and total "
        "S<sub>T</sub>; error bars are SALib's bootstrap confidence intervals. The gap "
        "between them is the part of an input's influence that acts only through "
        "interactions with others.")

    f_water = figure("fig_sa_waterfall.png",
        "Mechanism accounting \u2014 exact multiplicative decomposition of one prediction",
        "The rate is a product, so in logarithms it is a sum, and a sum decomposes with no "
        "residual at all (max relative residual 3.5&times;10<sup>-16</sup> over 12 arms). "
        "This is the complete account of a single prediction that a SHAP waterfall "
        "approximates. It attributes to <em>mechanisms</em> rather than to parameters, so it "
        "complements the Shapley panel rather than repeating it.")

    f_targ = figure("fig_sa_targets_givendata.png",
        "Per-response attribution \u2014 share of explained variance, squared rank regression",
        "Share of each response's explained variance, from squared standardised rank "
        "regression coefficients &mdash; a legitimate variance partition because the inputs "
        "are sampled independently. The R&sup2; under each column is how much of that "
        "response the partition covers.")

    f_agree = figure("fig_sa_givendata.png",
        "Cross-method agreement \u2014 regression, moment-independent and variance-based rankings",
        "All six are computed on the 4,096 existing ODE runs, so none of them cost a new "
        "simulation and none involve a surrogate. They agree on K<sub>comp</sub>. The one "
        "real disagreement is &theta;<sub>h</sub>, large by the distribution-based measures and "
        "near zero by the monotone ones. The Sobol' run settles that one: "
        "S<sub>T</sub>&nbsp;=&nbsp;0.003, so the &delta;/PAWN signal was estimator noise, not "
        "a real effect. Note also that &delta; and PAWN carry a positive noise floor at this "
        "sample size (about 0.25 once normalised), so every row below <em>divot shelter</em> "
        "sits on that floor and those rows are <strong>not</strong> ranked against one "
        "another. The linear fit R&sup2; of 0.63 is below the 0.7 convention, which is why "
        "the SRC column alone should not be used for ranking; the monotone fit at 0.83 is.")

    f_mor = figure("fig_sa_morris.png", "Screening \u2014 Morris elementary effects on the ODE",
        "20 trajectories over the 19 continuous inputs, material fixed at HDPE, response = "
        "removal flux. Screening only: it ranks by &mu;* and flags non-linearity or "
        "interaction through &sigma;.")
    f_fact = figure("fig_sa_factorial_targets.png",
        "Design-factor variance \u2014 exact total Sobol' indices from the 864-arm factorial",
        "Total Sobol' indices from the 864-arm factorial &mdash; exact, and never needed a "
        "surrogate, because the grid is a complete orthogonal design. These are the six "
        "things the team actually sets.")

    findings = """
<h2>What the analyses say</h2>
<p class="lede"><strong>1. K<sub>comp</sub> rules the flux, and it has no source.</strong>
It is rank 1 on the day-60 flux by every model-truth measure &mdash; Morris &mu;* = 0.934,
exact Shapley mean |&phi;| = 0.119 g&nbsp;N&nbsp;m<sup>-2</sup>&nbsp;d<sup>-1</sup>, and Sobol'
S<sub>T</sub> = 0.476 &plusmn; 0.123 on the equations themselves, with SRC, SRRC, PRCC,
Borgonovo &delta;, PAWN and RBD-FAST agreeing. It is also the only input whose S<sub>T</sub>
interval separates from the next input's at 95&nbsp;%. Nobody has measured heterotroph suppression of nitrifiers on this system. Influence
and evidence are close to inversely ordered here, and that is the main limit on what the model
can claim quantitatively.</p>
<p class="lede"><strong>2. The model is monotone but not linear.</strong> For the flux, a linear
description captures R&sup2;&nbsp;=&nbsp;__R2LIN__ of the model's own variance while a monotone one
captures R&sup2;&nbsp;=&nbsp;__R2MON__. Rank-based rankings are therefore trustworthy; raw linear
coefficients are not. Neither number says anything about agreement with measurement &mdash;
<strong>no coupon flux has ever been measured, and nothing in this model has been fitted to
one.</strong></p>
<p class="lede"><strong>3. Crowding is the throttle; oxygen is not.</strong> The exact
decomposition shows heterotroph crowding removing 61&ndash;86&nbsp;% of the flux across arms,
while the oxygen effectiveness factor is <strong>exactly 1.00 in every arm</strong>. The film
never gets thick enough for oxygen to limit, which is why photoperiod moves biomass and not
flux: phototrophs take film capacity and return nothing the nitrifiers can use.</p>
<p class="lede"><strong>4. Material leads every response except two.</strong> It takes the
largest share of total biofilm, phototrophs and nitrifiers; heterotrophs are ruled by feed
substrate and the flux by K<sub>comp</sub>. Averaging the guilds into &ldquo;biofilm&rdquo;
hides all of this, which is the case for reporting them separately.</p>

<h2>Key to every variable in these analyses</h2>
<p class="lede">Figures on this tab label inputs by what they <em>are</em>, with the model's
own symbol underneath in parentheses, so nothing has to be decoded from memory. This key gives
the full entry for each: what it means, how it enters the equations, the value the model uses,
the range the sensitivity analyses swept it over, and <strong>where the number came from</strong>. The evidence column is
the tier from the Data sources tab; <span style="color:#C8102E;font-weight:600">no source</span>
means nobody has measured it. Full grading scheme in SENSITIVITY.md.</p>
"""
    findings = (findings
                .replace("__R2LIN__", ("%.2f" % float(r2_lin)) if r2_lin else "&mdash;")
                .replace("__R2MON__", ("%.2f" % float(r2_flux)) if r2_flux else "&mdash;"))

    return (hdr + f_diag + f_shap + f_water + "<h2>Ranking the inputs</h2>"
            + f_sob + f_agree + f_targ
            + "<h2>Screening and the design factors</h2>" + f_mor + f_fact
            + findings + '<div class="keywrap">' + key_table() + "</div>")


def build():
    series, meta = load_grid()
    model_html = mdlite.render(open(os.path.join(ROOT, "MODEL.md"), encoding="utf-8").read())
    gloss_html = mdlite.render(open(os.path.join(ROOT, "GLOSSARY.md"), encoding="utf-8").read())
    src_html   = mdlite.render(open(os.path.join(ROOT, "DATA_SOURCES.md"), encoding="utf-8").read())
    scene_js   = open(os.path.join(HERE, "_scene_js_v3.txt"), encoding="utf-8").read()

    mats = sorted({m["material"] for m in meta.values()})
    rpms = axis_tokens(meta, 2)
    nshs = axis_tokens(meta, 3)
    shel = axis_tokens(meta, 4)

    # Built OUTSIDE the page f-string on purpose: inline, the inner f-strings' braces
    # were escaped twice and every numeric option rendered the literal text "{v}".
    def opts(vs, label, short):
        return "".join('<option value="%s" data-short="%s">%s</option>'
                       % (v, short(v), label(v)) for v in vs)
    opt_mat = "".join('<option value="%s">%s</option>' % (v, MATNAME.get(v, v)) for v in mats)
    opt_rpm = opts(rpms, lambda v: "%g rpm" % float(v), lambda v: "%g rpm" % float(v))
    opt_nsh = opts(nshs, lambda v: ("n = %g  (no shear effect)" if float(v) == 0 else "n = %g") % float(v),
                   lambda v: "n = %g" % float(v))
    SHEL_LAB = {"1.0": "1.0 — flush with the band", "0.5": "0.5 — half sheltered",
                "0.3": "0.3 — deeply recessed"}
    opt_shel = opts(shel, lambda v: SHEL_LAB.get(v, v), lambda v: "\u03c6 = %g" % float(v))

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Coupon explorer — Apple Springs RBC</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head><body>
<header><h1>Coupon explorer — coupons on the Apple Springs RBC</h1>
<div class="sub">Four materials, nine coupons per divot, in divots on the two steel bands of the
first-stage wheel. Photoperiod is set by which end of the shaft a divot sits at. Open system:
the bulk is imposed by the plant. Rig geometry is <span class="ph">PLACEHOLDER</span> pending
field measurement.</div></header>
<nav>
 <button class="on" data-tab="t1">Parameter explorer</button>
 <button data-tab="t2">RBC in 3D</button>
 <button data-tab="t3">Sensitivity &amp; SHAP</button>
 <button data-tab="t4">Model details</button>
 <button data-tab="t5">Glossary</button>
 <button data-tab="t6">Data sources</button></nav>
<main>
<section id="t1"><div class="wrap"><div class="ctl">
 <label>material</label><select id="mat">
   <option value="__all">show all four</option>
   {opt_mat}</select>
 <label>photoperiod</label><select id="phot">
   <option value="__both">show both</option>
   <option value="summer" selected>summer solstice — 15.50 h</option>
   <option value="winter">winter solstice — 8.87 h</option></select>
 <label>rotation <span class="val" data-for="rpm"></span></label>
 <select id="rpm">{opt_rpm}</select>
 <label>shear exponent <span class="val" data-for="nsh"></span></label>
 <select id="nsh">{opt_nsh}</select>
 <label>divot shelter <span class="val" data-for="shel"></span></label>
 <select id="shel">{opt_shel}</select>
 <label>bulk load</label><select id="load">
   <option value="low">BOD₅ 72 mg/L</option><option value="high">BOD₅ 120 mg/L</option></select>
 <div class="note"><strong>Mount radius is not a control.</strong> The bands fix the
 coupons at r/R = 0.95, so f_wet = 0.4469 for every arm.</div>
 <div class="note"><strong>Shear exponent</strong> <em>n</em> sets how strongly detachment
 responds to shear: <code>k_det = k_det,base · (τ/τ_ref)^n</code>. It is sampled rather than
 fixed because the literature disagrees — <em>n</em> = 0 is the position that shear has no
 effect on detachment, while Rittmann (1982) gives 0.58.</div>
 <div class="note"><strong>Divot shelter</strong> φ scales the shear a recessed coupon feels:
 <code>τ_local = φ · τ_free</code>. <span class="ph">NO SOURCE</span> — nothing measures it, so
 it is swept rather than fixed. It only bites when <em>n</em> &gt; 0.</div>
 <div class="note">Photoperiods are <strong>timer</strong> hours. What the coupon receives is
 less, because submerged means dark — see the delivered-light card.</div>
 <div class="note">With both photoperiods shown, <strong>summer is solid and winter dashed</strong>.</div>
</div><div>
  <div class="chart"><h3 id="hX">Biomass by guild</h3>
   <div class="cap" id="capX">Per exposed coupon area A_exp = 12.90 cm².</div>
   <canvas id="cX"></canvas><div class="legend" id="kX"></div></div>
  <div class="chart"><h3>Film thickness</h3>
   <div class="cap">Shaded band: 151–412 µm, the two film thicknesses reported on real RBC
   media by Hassard et al. (2014) — the thicknesses at which biofilm cohesive strength measured
   7.7 and 6.1 N m⁻². Two data points, not a distribution.</div>
   <canvas id="cLf"></canvas><div class="legend" id="kLf"></div></div>
 <div class="chart"><h3>Areal removal flux</h3>
  <div class="cap">Ammonia-nitrogen removed per m² of exposed coupon per day — what the coupons
  actually measure, and the quantity the plant join consumes through J_V = a_eff · J_A.
  Dashed gold lines mark the three harvests.</div>
  <canvas id="cJA"></canvas><div class="legend" id="kJA"></div>
  <details class="calc"><summary>How this is calculated</summary>
   <p>Nitrification is carried in a <strong>measured areal form</strong> rather than a
   volumetric Monod rate. For each irradiance bin the rate is a reference flux scaled by seven
   multiplicative terms, each between 0 and 1 except the biomass ratio:</p>
   <pre><code>r_N = rN_ref · (X_n / Xn_ref)        nitrifier biomass, linear
          · S_NH / (K_N,n + S_NH)      ammonia Monod
          · θ_n^(T − 20)               temperature
          · K_comp / (K_comp + X_h)    heterotroph crowding
          · f_wet                      share of each revolution submerged
          · S_O / (K_O,A + S_O)        oxygen at the film surface
          · (1 − X_tot / X_cap)        remaining space in the film</code></pre>
   <p>That rate is then cut by an <strong>oxygen effectiveness factor</strong>, because a thick
   film is anoxic below a certain depth. The penetration depth comes from an analytic zero-order
   solution rather than a PDE:</p>
   <pre><code>δ    = √(2 · D_O2 · S_O / R_v)      R_v = volumetric O₂ demand
η_O2 = min(1, δ / L_f)             = 1 while the film is thinner than δ</code></pre>
   <p>Finally the bins are combined by <strong>area weight</strong>, since a flat coupon is
   partly lit and partly shaded:</p>
   <pre><code>J_A = Σ_b  w_b · r_N,b · η_O2,b</code></pre>
   <p>Three things worth noting when reading the curve. <strong>J_A is per unit of colonized,
   non-occluded area</strong> — the colonized and occluded fractions are applied later, in the
   plant join, so applying them here too would discount twice. <strong>The denominator is the
   exposed coupon area</strong> A_exp = 12.90 cm², one face net of its 19.05 mm magnet; every
   value on this axis is tied to that number, and it is 2.22× smaller than the both-faces
   figure used before the magnet mounting was described. And <strong>f_wet enters directly</strong>,
   so the duty cycle moves this curve even with the shear exponent set to zero.</p>
  </details></div>
</div>
<aside class="side"><div class="cards" id="cards"></div></aside>
</div></section>

<section id="t2" style="display:none"><div class="doc">
<h1>The rig, in 3D</h1>
<p><strong>Drag to orbit, slide to turn the wheel or change the day, and click any coupon to
read its predicted state.</strong> Coupon brightness tracks predicted biomass on the selected
day, scaled against the brightest divot on that same day — so what you see is relative growth,
and the readout below carries the numbers. The lamps follow the photoperiod control on the first
tab, and the readout follows the rotation, shear, shelter and load controls as well.</p>
<p> Two rotating steel <strong>end plates 6 ft
apart</strong> carry the wafer pack between them. Two steel <strong>bands</strong> run axially
from plate to plate at <strong>0° and 180°</strong>, at r/R = 0.95. Each band carries four
<strong>divots</strong>, and each divot holds nine coupons of one material in magnet sandwiches.</p>
<p><strong>Photoperiod is axial.</strong> Six lamps sit in existing round holes in the cover,
three at each end, so a divot's photoperiod is decided by which end of the shaft it sits at —
not by which face of a disc it is on, as in the earlier design. The two bands at 0° and 180° are
<strong>replicates, not treatments</strong>: angular position on a turning wheel is a phase, not
a location, so both sample the same duty cycle.</p>
</div>
<div class="scenewrap">
 <div>
  <div class="sldrow">
   <div><label>wheel angle
     <span class="val" id="scphaselab" style="float:right;color:#e6e8ea;font-weight:600">54°</span></label>
     <input type="range" class="slider" id="scphase" min="0" max="359" value="54"></div>
   <div><label>experiment day
     <span class="val" id="scdaylab" style="float:right;color:#e6e8ea;font-weight:600">day 60</span></label>
     <input type="range" class="slider" id="scday" min="0" max="60" value="60"></div>
  </div>
  <div class="tt"><canvas id="scene"></canvas></div>
 </div>
 <aside class="scenside"><div class="rd" id="cpinfo"></div>
  <div class="note">Click any coupon in the scene to fill this panel. It follows the rotation,
  shear, shelter and load controls on the first tab, not just photoperiod.</div></aside>
</div>
<div class="doc">
<div class="legend">
 <span><span class="sw" style="background:#4fc9a0"></span>fabric</span>
 <span><span class="sw" style="background:#5fb3e0"></span>HDPE</span>
 <span><span class="sw" style="background:#b9c0c8"></span>bare steel</span>
 <span><span class="sw" style="background:#c08cf0"></span>graphene-coated steel</span>
 <span><span class="sw" style="background:#d69e46"></span>summer-end lamps</span>
 <span><span class="sw" style="background:#5c90d6"></span>winter-end lamps</span>
 <span><span class="sw" style="background:#1a5c56"></span>liquor at 0.1577 R below the shaft</span></div>
<p class="note">Live canvas render by a painter's-algorithm routine in plain JavaScript — no
WebGL and no library, so the page stays one self-contained file. The lamps follow the
<strong>photoperiod control</strong> on the first tab: switch to one solstice and the other end
goes dark. Two legibility departures from the real hardware, both deliberate: the
<strong>end plates are drawn translucent</strong> (they are solid steel, but opaque they hide the
wafer pack and every divot behind them), and the <strong>coupon blocks are drawn 1.8× oversize</strong>
— at true scale a 39.7 mm coupon is 0.04 of the disc radius and invisible. The tank shell is
not drawn: four large quads cannot be depth-sorted against
the wheel without a z-buffer. Dimensions are <span class="ph">PLACEHOLDER</span> except the 6 ft
shaft span: disc diameter 2.0 m, band at r/R = 0.95. The waterline is at the geometrically
correct depth for 40 % areal submergence.</p>
</div></section>

<section id="t3" style="display:none"><div>{sens_tab()}</div></section>
<section id="t4" style="display:none"><div class="doc">{model_html}</div></section>
<section id="t5" style="display:none"><div class="doc">{gloss_html}</div></section>
<section id="t6" style="display:none"><div class="doc">{src_html}</div></section>
</main>
<script>
const SERIES={json.dumps(series, separators=(',',':'))};
const META={json.dumps(meta, separators=(',',':'))};
const MATNAME={json.dumps(MATNAME)};
const MATS={json.dumps(mats)};
</script>
<script>
"""
    # The explorer JS and the scene JS are concatenated, NOT interpolated into the
    # f-string: both are full of braces and escaping them twice is how the v2 build
    # printed literal "{v}" into every dropdown.

    html += JS + "\n" + scene_js + "\n</script></body></html>"

    p = os.path.join(OUT, "index.html")
    open(p, "w", encoding="utf-8").write(html)
    b = open(p, "rb").read()
    print(f"wrote {p}")
    print(f"  {len(b)/1e6:.2f} MB   sha256 {hashlib.sha256(b).hexdigest()[:16]}")
    print(f"  {len(series)} arms, 6 tabs, live canvas scene")
    return p


if __name__ == "__main__":
    build()
