#!/usr/bin/env python3
"""Merge <out>/sessions.json + <out>/decisions.json into a single
self-contained recap HTML (data embedded inline, interactive client-side).

decisions.json is optional: { "<session-id>": {"summary": str, "decisions": [str]} }

Usage: render_html.py --out ~/.claude/recaps
"""
import argparse, json, os
from datetime import datetime

PALETTE = [
    "#6ee7b7", "#fca5a5", "#93c5fd", "#fcd34d", "#c4b5fd",
    "#f9a8d4", "#5eead4", "#fdba74", "#a3e635", "#67e8f9",
    "#f0abfc", "#bef264",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="~/.claude/recaps")
    args = ap.parse_args()
    out = os.path.expanduser(args.out)

    data = json.load(open(os.path.join(out, "sessions.json")))
    decisions = {}
    dp = os.path.join(out, "decisions.json")
    if os.path.exists(dp):
        decisions = json.load(open(dp))

    sess = data["sessions"]
    for s in sess:
        d = decisions.get(s["id"])
        s["summary"] = d.get("summary") if d else None
        s["decisions"] = d.get("decisions", []) if d else []

    projects = sorted({s["project"] for s in sess})
    proj_color = {p: PALETTE[i % len(PALETTE)] for i, p in enumerate(projects)}

    stats = {
        "sessions": len(sess),
        "prs": sum(len(s["prs"]) for s in sess),
        "commits": sum(s["commits"] for s in sess),
        "projects": len(projects),
        "files": sum(s["file_count"] for s in sess),
        "minutes": sum(s["duration_min"] for s in sess),
    }

    payload = {
        "generated": data["generated"], "days": data["days"],
        "sessions": sess, "projectColors": proj_color, "stats": stats,
    }
    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))

    stamp = datetime.now().astimezone().strftime("%Y-%m-%d")
    path = os.path.join(out, f"recap-{stamp}.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"wrote {path} ({len(html) // 1024} KB)")
    print(path)  # last line = path, for the caller to open


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude · Session Recap</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0a0b0f; --bg2:#0e1016; --panel:#13161f; --panel2:#171b26;
  --line:#232838; --line2:#2d3346;
  --ink:#e8eaf0; --ink-dim:#9aa3b8; --ink-faint:#646d85;
  --amber:#f5b942; --amber-soft:#f5b94222;
  --green:#5ad6a0; --green-soft:#5ad6a01a;
  --rail:#2a3145;
  --shadow:0 18px 50px -18px rgba(0,0,0,.8);
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
  background:var(--bg); color:var(--ink);
  font-family:'IBM Plex Sans',system-ui,sans-serif;
  line-height:1.5; -webkit-font-smoothing:antialiased;
  background-image:
    radial-gradient(900px 500px at 78% -8%, #1a2030 0%, transparent 60%),
    radial-gradient(700px 480px at 8% 4%, #18161f 0%, transparent 55%);
  background-attachment:fixed;
}
body::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:9999;
  opacity:.035; mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px 120px}
header{padding:64px 0 28px;position:relative}
.eyebrow{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.32em;
  text-transform:uppercase;color:var(--amber);opacity:.9}
h1{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;
  font-size:clamp(38px,6vw,68px);line-height:.98;letter-spacing:-.02em;margin:10px 0 6px}
h1 .accent{color:var(--ink-faint)}
.range{font-family:'JetBrains Mono',monospace;color:var(--ink-dim);font-size:13.5px}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}
.stat{background:linear-gradient(180deg,var(--panel),var(--bg2));
  border:1px solid var(--line);border-radius:14px;padding:14px 18px;min-width:104px;position:relative;overflow:hidden}
.stat .n{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:30px;line-height:1}
.stat .l{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--ink-faint);margin-top:7px}
.stat.pr .n{color:var(--green)} .stat.amber .n{color:var(--amber)}
.controls{position:sticky;top:0;z-index:50;margin-top:30px;padding:16px 0 14px;
  background:linear-gradient(180deg,var(--bg) 60%,transparent);backdrop-filter:blur(4px)}
.searchrow{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.search{flex:1;min-width:220px;display:flex;align-items:center;gap:9px;
  background:var(--panel);border:1px solid var(--line2);border-radius:11px;padding:10px 14px}
.search input{flex:1;background:none;border:none;outline:none;color:var(--ink);
  font-family:'IBM Plex Sans';font-size:14.5px}
.search input::placeholder{color:var(--ink-faint)}
.search svg{flex:none;opacity:.5}
.toggle{display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;
  background:var(--panel);border:1px solid var(--line2);border-radius:11px;padding:10px 14px;
  font-size:13px;color:var(--ink-dim);white-space:nowrap}
.toggle .box{width:16px;height:16px;border-radius:5px;border:1.5px solid var(--line2);
  display:grid;place-items:center;transition:.15s}
.toggle.on{color:var(--ink);border-color:var(--green)}
.toggle.on .box{background:var(--green);border-color:var(--green)}
.toggle.on .box::after{content:"✓";font-size:11px;color:#06281c;font-weight:700}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}
.chip{font-family:'JetBrains Mono',monospace;font-size:11.5px;letter-spacing:.02em;
  border:1px solid var(--line2);background:var(--panel);color:var(--ink-dim);
  padding:6px 11px 6px 9px;border-radius:999px;cursor:pointer;display:flex;align-items:center;gap:7px;transition:.15s}
.chip:hover{color:var(--ink)}
.chip .dot{width:8px;height:8px;border-radius:50%}
.chip .ct{opacity:.5}
.chip.off{opacity:.32;filter:saturate(.4)}
.chip.solo{border-color:var(--ink);color:var(--ink);box-shadow:0 0 0 1px var(--ink) inset}
#timeline{margin-top:18px;position:relative}
.rail{position:absolute;left:9px;top:6px;bottom:0;width:2px;
  background:linear-gradient(180deg,transparent,var(--rail) 4%,var(--rail) 96%,transparent)}
.day{position:relative;padding:30px 0 4px 0}
.dayhead{position:sticky;top:118px;z-index:20;display:flex;align-items:baseline;gap:14px;padding-left:38px;margin-bottom:12px}
.dayhead::before{content:"";position:absolute;left:2px;top:3px;width:16px;height:16px;border-radius:50%;
  background:var(--amber);box-shadow:0 0 0 5px var(--bg),0 0 16px var(--amber);}
.dnum{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:24px;letter-spacing:-.01em}
.dmeta{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--ink-faint)}
.dmeta b{color:var(--amber);font-weight:500}
.card{position:relative;margin:0 0 12px 38px;background:linear-gradient(165deg,var(--panel),var(--bg2));
  border:1px solid var(--line);border-radius:15px;padding:16px 18px;cursor:pointer;
  transition:transform .18s cubic-bezier(.2,.7,.3,1),border-color .18s,box-shadow .18s;
  opacity:0;transform:translateY(14px)}
.card.in{opacity:1;transform:none}
.card:hover{border-color:var(--line2);transform:translateY(-2px);box-shadow:var(--shadow)}
.card::before{content:"";position:absolute;left:-34px;top:22px;width:11px;height:11px;border-radius:50%;
  background:var(--bg2);border:2px solid var(--rail);transition:.18s}
.card:hover::before{border-color:var(--ink-dim)}
.card.haspr::before{border-color:var(--green);background:var(--green);box-shadow:0 0 12px var(--green-soft)}
.connector{position:absolute;left:-23px;top:27px;width:23px;height:2px;background:var(--rail)}
.crow{display:flex;align-items:flex-start;gap:12px}
.ctime{font-family:'JetBrains Mono',monospace;font-size:12.5px;color:var(--ink-dim);flex:none;padding-top:2px;width:52px}
.cmain{flex:1;min-width:0}
.ctitle{font-family:'Bricolage Grotesque',sans-serif;font-weight:600;font-size:17.5px;letter-spacing:-.01em;line-height:1.25}
.csum{color:var(--ink-dim);font-size:13.5px;margin-top:5px}
.cmeta{display:flex;flex-wrap:wrap;gap:7px;margin-top:11px;align-items:center}
.tag{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.02em;border-radius:7px;padding:3px 8px;
  display:inline-flex;align-items:center;gap:5px;border:1px solid var(--line2);color:var(--ink-dim);white-space:nowrap}
.tag .dot{width:7px;height:7px;border-radius:50%}
.tag.branch{color:var(--ink-faint)}
.tag.pr{border-color:#2f6b50;color:var(--green);background:var(--green-soft);text-decoration:none}
.tag.pr:hover{border-color:var(--green)}
.tag.commit{color:#d9b46a;border-color:#4a3f22;background:#f5b9420f}
.tag.files{color:#9fb4e8;border-color:#2c3858}
.detail{max-height:0;overflow:hidden;transition:max-height .3s ease}
.card.open .detail{max-height:1200px}
.detail-inner{padding-top:14px;margin-top:14px;border-top:1px dashed var(--line2)}
.dec-h{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:8px}
.dec{list-style:none;display:flex;flex-direction:column;gap:7px;margin-bottom:14px}
.dec li{position:relative;padding-left:18px;font-size:13.5px;color:var(--ink)}
.dec li::before{content:"";position:absolute;left:2px;top:8px;width:6px;height:6px;border-radius:1px;background:var(--amber);transform:rotate(45deg)}
.ask{background:#0c0e14;border:1px solid var(--line);border-radius:10px;padding:11px 13px;font-size:13px;color:var(--ink-dim)}
.ask .q{color:var(--ink-faint);font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.16em;text-transform:uppercase;display:block;margin-bottom:6px}
.prlist{display:flex;flex-wrap:wrap;gap:7px;margin-top:11px}
.resume{display:flex;align-items:center;gap:8px;margin-top:12px;font-family:'JetBrains Mono',monospace;font-size:11.5px}
.resume code{background:#0c0e14;border:1px solid var(--line2);border-radius:7px;padding:5px 9px;color:var(--ink-dim)}
.resume button{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;
  background:none;border:1px solid var(--line2);color:var(--ink-faint);border-radius:7px;padding:5px 9px;cursor:pointer;transition:.15s}
.resume button:hover{border-color:var(--amber);color:var(--amber)}
.caret{flex:none;color:var(--ink-faint);transition:.2s;margin-top:3px}
.card.open .caret{transform:rotate(90deg);color:var(--ink-dim)}
.empty{text-align:center;color:var(--ink-faint);padding:60px 0;font-family:'JetBrains Mono',monospace;font-size:13px}
footer{margin-top:50px;text-align:center;font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--ink-faint);letter-spacing:.04em}
footer .amber{color:var(--amber)}
@media(max-width:560px){.ctime{width:auto}.crow{flex-wrap:wrap}.dayhead{top:108px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">Session Flight Recorder</div>
    <h1>Session <span class="accent">Recap</span></h1>
    <div class="range" id="range"></div>
    <div class="stats" id="stats"></div>
  </header>
  <div class="controls">
    <div class="searchrow">
      <label class="search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input id="q" type="text" placeholder="Search titles, decisions, branches…" autocomplete="off">
      </label>
      <div class="toggle" id="prtoggle"><span class="box"></span>PRs / commits only</div>
    </div>
    <div class="chips" id="chips"></div>
  </div>
  <div id="timeline"><div class="rail"></div></div>
  <footer></footer>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const S = DATA.sessions, PC = DATA.projectColors;
const state = { q:"", prOnly:false, projects:new Set(Object.keys(PC)), soloMode:false };
const fmtDur = m => m>=60 ? `${Math.floor(m/60)}h ${m%60}m` : `${m}m`;
const esc = s => (s||"").replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const D = iso => new Date(iso);
const dayKey = iso => { const d=D(iso); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); };
const fmtTime = iso => D(iso).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
const fmtDayNum = iso => D(iso).toLocaleDateString([], {weekday:'long', month:'short', day:'numeric'});
const relDay = iso => { const t=new Date(); t.setHours(0,0,0,0); const d=D(iso); d.setHours(0,0,0,0);
  const diff=Math.round((t-d)/864e5); return diff===0?'Today':diff===1?'Yesterday':`${diff} days ago`; };

(function(){
  const st=DATA.stats, first=S[S.length-1]?.start, last=S[0]?.start;
  document.getElementById('range').textContent =
    S.length ? `${fmtDayNum(first)} → ${fmtDayNum(last)}  ·  last ${DATA.days} days` : `last ${DATA.days} days`;
  const tiles=[['sessions','sessions',''],['prs','PRs opened','pr'],['commits','commits','amber'],
    ['files','files touched',''],['projects','projects','']];
  document.getElementById('stats').innerHTML = tiles.map(([k,l,c])=>
    `<div class="stat ${c}"><div class="n">${st[k]}</div><div class="l">${l}</div></div>`).join('')
    + `<div class="stat amber"><div class="n">${Math.round(st.minutes/60)}h</div><div class="l">active time</div></div>`;
})();

const projCounts = {};
S.forEach(s=>projCounts[s.project]=(projCounts[s.project]||0)+1);
const chipsEl=document.getElementById('chips');
Object.keys(PC).sort((a,b)=>projCounts[b]-projCounts[a]).forEach(p=>{
  const c=document.createElement('div'); c.className='chip'; c.dataset.p=p;
  c.innerHTML=`<span class="dot" style="background:${PC[p]}"></span>${esc(p)} <span class="ct">${projCounts[p]}</span>`;
  c.onclick=(e)=>{
    if(e.shiftKey||state.soloMode){
      if(state.projects.size===1 && state.projects.has(p)){ state.projects=new Set(Object.keys(PC)); state.soloMode=false; }
      else { state.projects=new Set([p]); state.soloMode=true; }
    } else {
      if(state.projects.has(p)) state.projects.delete(p); else state.projects.add(p);
      if(state.projects.size===0) state.projects=new Set(Object.keys(PC));
    }
    render();
  };
  chipsEl.appendChild(c);
});
document.getElementById('q').addEventListener('input',e=>{state.q=e.target.value.toLowerCase();render();});
document.getElementById('prtoggle').addEventListener('click',function(){
  state.prOnly=!state.prOnly; this.classList.toggle('on',state.prOnly); render();
});

function matches(s){
  if(!state.projects.has(s.project)) return false;
  if(state.prOnly && !(s.prs.length||s.commits)) return false;
  if(state.q){
    const hay=[s.title,s.summary,s.branch,s.project,s.first_prompt,...(s.decisions||[])].join(' ').toLowerCase();
    if(!hay.includes(state.q)) return false;
  }
  return true;
}
function copyResume(btn,id){
  navigator.clipboard.writeText('claude --resume '+id).then(()=>{
    const o=btn.textContent; btn.textContent='copied'; setTimeout(()=>btn.textContent=o,1200);
  });
}
function card(s){
  const col=PC[s.project];
  const prs=s.prs.map(p=>`<a class="tag pr" href="${p.url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">🔀 ${esc(p.repo.split('/')[1]||p.repo)} #${p.num}</a>`).join('');
  const meta=[`<span class="tag"><span class="dot" style="background:${col}"></span>${esc(s.project)}</span>`];
  if(s.branch) meta.push(`<span class="tag branch">⎇ ${esc(s.branch)}</span>`);
  if(s.commits) meta.push(`<span class="tag commit">✓ ${s.commits} commit${s.commits>1?'s':''}</span>`);
  if(s.file_count) meta.push(`<span class="tag files">📝 ${s.file_count} file${s.file_count>1?'s':''}</span>`);
  meta.push(`<span class="tag">⏱ ${fmtDur(s.duration_min)}</span>`);
  meta.push(`<span class="tag">${s.prompt_count} turn${s.prompt_count>1?'s':''}</span>`);
  const dec=(s.decisions&&s.decisions.length)
    ? `<div class="dec-h">Key decisions</div><ul class="dec">${s.decisions.map(d=>`<li>${esc(d)}</li>`).join('')}</ul>` : '';
  const ask=s.first_prompt ? `<div class="ask"><span class="q">Opening ask</span>${esc(s.first_prompt)}</div>` : '';
  const prlist=s.prs.length? `<div class="prlist">${prs}</div>`:'';
  const resume=`<div class="resume"><code>claude --resume ${esc(s.id)}</code><button onclick="event.stopPropagation();copyResume(this,'${esc(s.id)}')">copy</button></div>`;
  const el=document.createElement('div');
  el.className='card'+(s.prs.length?' haspr':'');
  el.innerHTML=`
    <div class="connector"></div>
    <div class="crow">
      <div class="ctime">${fmtTime(s.start)}</div>
      <div class="cmain">
        <div class="ctitle">${esc(s.title)}</div>
        ${s.summary?`<div class="csum">${esc(s.summary)}</div>`:''}
        <div class="cmeta">${meta.join('')}</div>
      </div>
      <svg class="caret" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
    </div>
    <div class="detail"><div class="detail-inner">${dec}${ask}${prlist}${resume}</div></div>`;
  el.onclick=()=>el.classList.toggle('open');
  return el;
}
function render(){
  document.querySelectorAll('.chip').forEach(c=>{
    const on=state.projects.has(c.dataset.p);
    c.classList.toggle('off',!on);
    c.classList.toggle('solo',state.soloMode&&on);
  });
  const tl=document.getElementById('timeline');
  tl.querySelectorAll('.day,.empty').forEach(n=>n.remove());
  const list=S.filter(matches);
  if(!list.length){ const e=document.createElement('div'); e.className='empty'; e.textContent='// no sessions match these filters'; tl.appendChild(e); footer(0); return; }
  const byDay={};
  list.forEach(s=>{(byDay[dayKey(s.start)] ||= []).push(s);});
  Object.keys(byDay).sort().reverse().forEach(k=>{
    const day=byDay[k], sec=document.createElement('div'); sec.className='day';
    const prs=day.reduce((a,s)=>a+s.prs.length,0), cm=day.reduce((a,s)=>a+s.commits,0);
    sec.innerHTML=`<div class="dayhead"><span class="dnum">${fmtDayNum(day[0].start)}</span>
      <span class="dmeta">${relDay(day[0].start)} · <b>${day.length}</b> session${day.length>1?'s':''}${prs?` · <b>${prs}</b> PR`:''}${cm?` · ${cm} commit${cm>1?'s':''}`:''}</span></div>`;
    day.forEach(s=>sec.appendChild(card(s)));
    tl.appendChild(sec);
  });
  footer(list.length);
  [...tl.querySelectorAll('.card')].forEach((c,i)=>setTimeout(()=>c.classList.add('in'), Math.min(i*22,500)));
}
function footer(n){
  const g=new Date(DATA.generated).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
  document.querySelector('footer').innerHTML=`showing <span class="amber">${n}</span> of ${S.length} sessions · generated ${g} · <span class="amber">tip:</span> shift-click a project to solo it · expand a card to copy its resume command`;
}
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
