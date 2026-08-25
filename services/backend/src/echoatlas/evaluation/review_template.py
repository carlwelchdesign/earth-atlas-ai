"""Self-contained, local-only HTML for candidate review."""

# ruff: noqa: E501

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from echoatlas.evaluation.review import ReviewPacket


def render_review_html(packet: ReviewPacket) -> str:
    payload = json.dumps(packet.model_dump(mode="json"), separators=(",", ":")).replace(
        "</", "<\\/"
    )
    return _TEMPLATE.replace("__PACKET_JSON__", payload)


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EchoAtlas local candidate review</title>
  <style>
    :root { color-scheme: dark; --bg:#061116; --panel:#0b1b21; --line:#29434b; --text:#eef8f7; --muted:#a9bcc0; --mint:#82e6d4; --amber:#ffc662; --danger:#ff9b8d; }
    * { box-sizing:border-box; }
    [hidden] { display:none !important; }
    body { margin:0; background:var(--bg); color:var(--text); font:15px/1.45 ui-sans-serif,system-ui,-apple-system,sans-serif; }
    button,input,select,textarea { font:inherit; }
    button,input,select,textarea { outline-offset:3px; }
    :focus-visible { outline:3px solid var(--mint); }
    header { padding:24px; border-bottom:1px solid var(--line); display:flex; gap:24px; justify-content:space-between; align-items:start; flex-wrap:wrap; }
    .eyebrow { color:var(--mint); text-transform:uppercase; letter-spacing:.14em; font-weight:800; font-size:12px; }
    h1,h2,h3,p { margin-top:0; }
    h1 { margin-bottom:6px; font-size:clamp(23px,3vw,34px); }
    .status { border:1px solid #356c65; color:var(--mint); border-radius:999px; padding:7px 11px; font-weight:800; }
    .boundary { margin:20px 24px; padding:16px 18px; border:1px solid #795b27; background:#291f10; border-radius:8px; }
    .boundary strong { color:var(--amber); }
    main { display:grid; grid-template-columns:minmax(240px,310px) minmax(0,1fr); gap:16px; padding:0 24px 28px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:10px; overflow:hidden; }
    .panel-heading { padding:16px; border-bottom:1px solid var(--line); }
    .queue { max-height:calc(100vh - 220px); overflow:auto; }
    .candidate { width:100%; border:0; border-bottom:1px solid var(--line); background:transparent; color:var(--text); padding:13px 16px; text-align:left; cursor:pointer; }
    .candidate:hover,.candidate[aria-current="true"] { background:#123039; }
    .candidate strong,.candidate small { display:block; }
    .candidate small { color:var(--muted); margin-top:4px; }
    .workspace { padding:18px; }
    .meta { color:var(--muted); }
    .views { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:16px 0; }
    figure { margin:0; min-width:0; }
    canvas { width:100%; aspect-ratio:1; display:block; background:#020608; border:1px solid var(--line); border-radius:6px; }
    figcaption { padding-top:7px; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.1em; font-weight:800; }
    .review-form { border-top:1px solid var(--line); padding-top:18px; }
    .reviewer { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px; }
    label { display:grid; gap:6px; font-weight:700; }
    input,select,textarea { width:100%; color:var(--text); background:#071318; border:1px solid #45616a; border-radius:6px; padding:10px; }
    textarea { min-height:90px; resize:vertical; }
    .classification { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:16px; }
    .primary,.secondary { border-radius:6px; padding:10px 14px; font-weight:800; cursor:pointer; }
    .primary { background:var(--mint); color:#031310; border:1px solid var(--mint); }
    .secondary { background:transparent; color:var(--text); border:1px solid #58717a; }
    .save-state { color:var(--mint); }
    .warnings { color:var(--muted); margin-bottom:0; }
    .warnings li + li { margin-top:5px; }
    footer { color:var(--muted); border-top:1px solid var(--line); padding:18px 24px 28px; font-size:13px; }
    @media (max-width:900px) { main { grid-template-columns:1fr; } .queue { max-height:280px; } .views { grid-template-columns:1fr; } }
    @media (max-width:560px) { header,main { padding-left:14px; padding-right:14px; } .boundary { margin-left:14px; margin-right:14px; } .reviewer,.classification { grid-template-columns:1fr; } }
    @media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; } }
  </style>
</head>
<body>
  <header>
    <div><div class="eyebrow">EchoAtlas · local review packet</div><h1>Bingham Canyon candidate review</h1><p class="meta" id="run-meta"></p></div>
    <div class="status">Local-only · pending human review</div>
  </header>
  <section class="boundary" role="note"><strong>Evidence boundary</strong><br><span id="boundary-copy"></span> A qualified SAR reviewer and independently drawn reference regions are still required before benchmark or accuracy claims.</section>
  <main>
    <aside class="panel" aria-label="Candidate queue"><div class="panel-heading"><div class="eyebrow">Review queue</div><h2 id="queue-title"></h2></div><div class="queue" id="queue"></div></aside>
    <section class="panel workspace" aria-labelledby="candidate-title">
      <div class="eyebrow">Synchronized evidence crops</div><h2 id="candidate-title" tabindex="-1">Select a candidate</h2><p class="meta" id="candidate-meta"></p>
      <div class="views">
        <figure><canvas id="before-canvas" width="720" height="720"></canvas><figcaption>Before</figcaption></figure>
        <figure><canvas id="after-canvas" width="720" height="720"></canvas><figcaption>After</figcaption></figure>
        <figure><canvas id="overlay-canvas" width="720" height="720"></canvas><figcaption>Candidate overlay</figcaption></figure>
      </div>
      <ul class="warnings" id="warnings"></ul>
      <form class="review-form" id="review-form">
        <div class="reviewer">
          <label>Reviewer name<input id="reviewer-name" autocomplete="name" required></label>
          <label>Reviewer role<input id="reviewer-role" placeholder="e.g. engineering review or SAR domain review" required></label>
        </div>
        <div class="classification">
          <label>Review decision<select id="decision" required><option value="">Pending</option><option value="supported-needs-independent-reference">Evidence supports follow-up; independent region required</option><option value="false-positive">False positive / artifact</option><option value="unresolved">Unresolved</option></select></label>
          <label id="failure-wrap" hidden>False-positive class<select id="failure-class"><option value="">Choose a class</option><option value="geometry">Geometry</option><option value="water-moisture">Water / moisture</option><option value="speckle">Speckle</option><option value="shadow-layover">Shadow / layover</option><option value="registration-artifact">Registration artifact</option><option value="other">Other</option></select></label>
        </div>
        <label style="margin-top:12px">Reviewer note<textarea id="note" maxlength="1000" placeholder="Describe the visible evidence and uncertainty. Do not infer cause, damage, identity, intent, or operational status."></textarea></label>
        <div class="actions"><button class="primary" type="submit">Save candidate review</button><button class="secondary" id="export" type="button">Export review JSON</button><span class="save-state" id="save-state" role="status" aria-live="polite"></span></div>
      </form>
    </section>
  </main>
  <footer><span id="footer-copy"></span><br>Source imagery remains local and is not embedded in this HTML or export.</footer>
  <script>
    const packet=__PACKET_JSON__;
    const storageKey=`echoatlas-review:${packet.packet_id}`;
    const state=(()=>{try{const stored=JSON.parse(localStorage.getItem(storageKey)||'{}');return {reviewer:stored?.reviewer||{},decisions:stored?.decisions||{}};}catch{return {reviewer:{},decisions:{}};}})();
    const images={}; let selected=null;
    for(const artifact of packet.artifacts){const image=new Image();image.src=artifact.source_url;images[artifact.role]=image;}
    const byId=id=>document.getElementById(id);
    byId('run-meta').textContent=`${packet.change_run_id} · ${packet.candidates.length} candidates · ${packet.source_license.provider} ${packet.source_license.spdx}`;
    byId('boundary-copy').textContent=packet.review_boundary;
    byId('queue-title').textContent=`${packet.candidates.length} machine candidates`;
    byId('footer-copy').textContent=`${packet.packet_id} · ${packet.processing_run_id} · ${packet.processing_aoi_id}`;
    byId('reviewer-name').value=state.reviewer.name||''; byId('reviewer-role').value=state.reviewer.role||'';
    function candidateIndex(candidate){return packet.candidates.indexOf(candidate)+1;}
    function shortId(candidate){return `C-${String(candidateIndex(candidate)).padStart(3,'0')}`;}
    function renderQueue(){const queue=byId('queue');queue.replaceChildren();for(const candidate of packet.candidates){const decision=state.decisions[candidate.candidate_id]?.decision||'pending';const button=document.createElement('button');const title=document.createElement('strong');const detail=document.createElement('small');button.type='button';button.className='candidate';button.setAttribute('aria-current',selected?.candidate_id===candidate.candidate_id?'true':'false');title.textContent=shortId(candidate);detail.textContent=`${candidate.pixel_count.toLocaleString()} px · score ${candidate.mean_change_score.toFixed(3)} · ${decision}`;button.replaceChildren(title,detail);button.onclick=()=>selectCandidate(candidate);queue.append(button);}}
    function selectCandidate(candidate,moveFocus=true){selected=candidate;renderQueue();byId('candidate-title').textContent=`${shortId(candidate)} · machine candidate`;byId('candidate-meta').textContent=`${candidate.candidate_id} · ${Math.round(candidate.area_square_meters).toLocaleString()} m² · p95 score ${candidate.p95_change_score.toFixed(3)}`;const warnings=byId('warnings');warnings.replaceChildren();for(const warning of candidate.warnings){const item=document.createElement('li');item.textContent=warning;warnings.append(item);}const saved=state.decisions[candidate.candidate_id]||{};byId('decision').value=saved.decision||'';byId('failure-class').value=saved.failure_class||'';byId('note').value=saved.note||'';syncFailure();drawCandidate(candidate);if(moveFocus)byId('candidate-title').focus();}
    function crop(candidate){const [minX,minY,maxX,maxY]=candidate.projected_bbox;const [gridMinX,,,gridMaxY]=packet.grid.bounds;const resolution=packet.grid.resolution;let x=(minX-gridMinX)/resolution;let y=(gridMaxY-maxY)/resolution;let width=(maxX-minX)/resolution;let height=(maxY-minY)/resolution;const padding=Math.max(48,Math.max(width,height)*.55);x-=padding;y-=padding;width+=padding*2;height+=padding*2;const side=Math.min(Math.max(width,height),packet.grid.width,packet.grid.height);x-=Math.max(0,(side-width)/2);y-=Math.max(0,(side-height)/2);x=Math.max(0,Math.min(x,packet.grid.width-side));y=Math.max(0,Math.min(y,packet.grid.height-side));return {x,y,side};}
    function drawCandidate(candidate){const box=crop(candidate);for(const [role,canvasId] of [['before','before-canvas'],['after','after-canvas'],['candidate-overlay','overlay-canvas']]){const canvas=byId(canvasId);const context=canvas.getContext('2d');context.fillStyle='#020608';context.fillRect(0,0,canvas.width,canvas.height);const image=images[role];const draw=()=>context.drawImage(image,box.x,box.y,box.side,box.side,0,0,canvas.width,canvas.height);const fail=()=>{context.fillStyle='#ff9b8d';context.font='700 24px system-ui';context.fillText('Image unavailable',28,56);byId('save-state').textContent='A review image could not be loaded. Regenerate the packet after checking local artifacts.';};if(image.complete){if(image.naturalWidth)draw();else fail();}else{image.addEventListener('load',draw,{once:true});image.addEventListener('error',fail,{once:true});}}}
    function syncFailure(){const isFailure=byId('decision').value==='false-positive';byId('failure-wrap').hidden=!isFailure;byId('failure-class').required=isFailure;if(!isFailure)byId('failure-class').value='';}
    byId('decision').addEventListener('change',syncFailure);
    byId('review-form').addEventListener('submit',event=>{event.preventDefault();if(!selected)return;state.reviewer={name:byId('reviewer-name').value.trim(),role:byId('reviewer-role').value.trim()};state.decisions[selected.candidate_id]={decision:byId('decision').value,failure_class:byId('failure-class').value||null,note:byId('note').value.trim(),saved_at:new Date().toISOString()};try{localStorage.setItem(storageKey,JSON.stringify(state));byId('save-state').textContent=`Saved ${shortId(selected)} locally.`;}catch{byId('save-state').textContent='Browser storage is unavailable. Export the review JSON to preserve this decision.';}renderQueue();});
    byId('export').addEventListener('click',()=>{state.reviewer={name:byId('reviewer-name').value.trim(),role:byId('reviewer-role').value.trim()};const exportData={review_export_version:'1.0.0',packet_id:packet.packet_id,change_run_id:packet.change_run_id,reviewer:state.reviewer,exported_at:new Date().toISOString(),decisions:packet.candidates.map(candidate=>({candidate_id:candidate.candidate_id,...(state.decisions[candidate.candidate_id]||{decision:'',failure_class:null,note:'',saved_at:null})})),boundary:'Candidate decisions are not independent reference regions or pipeline accuracy evidence.'};const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([JSON.stringify(exportData,null,2)+'\\n'],{type:'application/json'}));link.download=`${packet.packet_id}-decisions.json`;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);});
    renderQueue();if(packet.candidates.length)selectCandidate(packet.candidates[0],false);
  </script>
</body>
</html>
"""
