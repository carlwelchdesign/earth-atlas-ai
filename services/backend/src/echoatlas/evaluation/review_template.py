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
    #reference-canvas { cursor:crosshair; touch-action:none; }
    figcaption { padding-top:7px; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.1em; font-weight:800; }
    .review-form { border-top:1px solid var(--line); padding-top:18px; }
    .reference { margin:18px 0; padding:16px; border:1px solid #45616a; border-radius:8px; background:#08171c; }
    .reference-grid { display:grid; grid-template-columns:minmax(240px,1fr) minmax(240px,1fr); gap:16px; align-items:start; }
    .reference-copy { color:var(--muted); }
    .reference-copy strong { color:var(--amber); }
    .reference-status { color:var(--mint); min-height:1.45em; margin:10px 0 0; }
    .coordinate-help { color:var(--muted); font-size:13px; font-weight:400; }
    .danger { background:transparent; color:var(--danger); border:1px solid #98574f; }
    .confirm-clear { margin-top:12px; padding:12px; border:1px solid #98574f; border-radius:6px; }
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
    @media (max-width:900px) { main { grid-template-columns:1fr; } .queue { max-height:280px; } .views,.reference-grid { grid-template-columns:1fr; } }
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
        <section class="reference" aria-labelledby="reference-title">
          <div class="eyebrow">Candidate-directed labeling aid</div>
          <h3 id="reference-title">Provisional reference region</h3>
          <p class="reference-copy"><strong>Not independent ground truth.</strong> Draw only what you can support from the clean after image. Because this view was opened from a machine candidate, the result requires separate qualified review and adjudication before evaluation use.</p>
          <div class="reference-grid">
            <figure><canvas id="reference-canvas" width="720" height="720" aria-label="After image for provisional polygon drawing. Click or tap to add boundary points."></canvas><figcaption>After image only · no candidate overlay</figcaption></figure>
            <div>
              <label>Projected polygon coordinates
                <textarea id="reference-coordinates" spellcheck="false" placeholder="One x,y coordinate per line" aria-describedby="coordinate-help"></textarea>
                <span class="coordinate-help" id="coordinate-help">Enter at least three points in <span id="reference-crs"></span>, or add points on the image. Close the polygon to export complete geometry.</span>
              </label>
              <div class="actions">
                <button class="secondary" id="apply-coordinates" type="button">Apply coordinates</button>
                <button class="secondary" id="undo-point" type="button">Undo point</button>
                <button class="secondary" id="close-polygon" type="button">Close polygon</button>
                <button class="primary danger" id="request-clear" type="button">Clear region</button>
              </div>
              <div class="confirm-clear" id="confirm-clear" hidden role="group" aria-label="Confirm clearing provisional reference region">
                <strong>Clear this provisional region?</strong>
                <div class="actions"><button class="primary danger" id="confirm-clear-region" type="button">Yes, clear region</button><button class="secondary" id="cancel-clear" type="button">Cancel</button></div>
              </div>
              <p class="reference-status" id="reference-status" role="status" aria-live="polite"></p>
            </div>
          </div>
        </section>
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
    const state=(()=>{try{const stored=JSON.parse(localStorage.getItem(storageKey)||'{}');return {reviewer:stored?.reviewer||{},decisions:stored?.decisions||{},reference_regions:stored?.reference_regions||{}};}catch{return {reviewer:{},decisions:{},reference_regions:{}};}})();
    const images={}; let selected=null;
    for(const artifact of packet.artifacts){const image=new Image();image.src=artifact.source_url;images[artifact.role]=image;}
    const byId=id=>document.getElementById(id);
    byId('run-meta').textContent=`${packet.change_run_id} · ${packet.candidates.length} candidates · ${packet.source_license.provider} ${packet.source_license.spdx}`;
    byId('boundary-copy').textContent=packet.review_boundary;
    byId('queue-title').textContent=`${packet.candidates.length} machine candidates`;
    byId('footer-copy').textContent=`${packet.packet_id} · ${packet.processing_run_id} · ${packet.processing_aoi_id}`;
    byId('reference-crs').textContent=packet.grid.crs;
    byId('reviewer-name').value=state.reviewer.name||''; byId('reviewer-role').value=state.reviewer.role||'';
    function candidateIndex(candidate){return packet.candidates.indexOf(candidate)+1;}
    function shortId(candidate){return `C-${String(candidateIndex(candidate)).padStart(3,'0')}`;}
    function renderQueue(){const queue=byId('queue');queue.replaceChildren();for(const candidate of packet.candidates){const decision=state.decisions[candidate.candidate_id]?.decision||'pending';const button=document.createElement('button');const title=document.createElement('strong');const detail=document.createElement('small');button.type='button';button.className='candidate';button.setAttribute('aria-current',selected?.candidate_id===candidate.candidate_id?'true':'false');title.textContent=shortId(candidate);detail.textContent=`${candidate.pixel_count.toLocaleString()} px · score ${candidate.mean_change_score.toFixed(3)} · ${decision}`;button.replaceChildren(title,detail);button.onclick=()=>selectCandidate(candidate);queue.append(button);}}
    function selectCandidate(candidate,moveFocus=true){selected=candidate;byId('confirm-clear').hidden=true;renderQueue();byId('candidate-title').textContent=`${shortId(candidate)} · machine candidate`;byId('candidate-meta').textContent=`${candidate.candidate_id} · ${Math.round(candidate.area_square_meters).toLocaleString()} m² · p95 score ${candidate.p95_change_score.toFixed(3)}`;const warnings=byId('warnings');warnings.replaceChildren();for(const warning of candidate.warnings){const item=document.createElement('li');item.textContent=warning;warnings.append(item);}const saved=state.decisions[candidate.candidate_id]||{};byId('decision').value=saved.decision||'';byId('failure-class').value=saved.failure_class||'';byId('note').value=saved.note||'';syncFailure();syncReferenceText();drawCandidate(candidate);if(moveFocus)byId('candidate-title').focus();}
    function crop(candidate){const [minX,minY,maxX,maxY]=candidate.projected_bbox;const [gridMinX,,,gridMaxY]=packet.grid.bounds;const resolution=packet.grid.resolution;let x=(minX-gridMinX)/resolution;let y=(gridMaxY-maxY)/resolution;let width=(maxX-minX)/resolution;let height=(maxY-minY)/resolution;const padding=Math.max(48,Math.max(width,height)*.55);x-=padding;y-=padding;width+=padding*2;height+=padding*2;const side=Math.min(Math.max(width,height),packet.grid.width,packet.grid.height);x-=Math.max(0,(side-width)/2);y-=Math.max(0,(side-height)/2);x=Math.max(0,Math.min(x,packet.grid.width-side));y=Math.max(0,Math.min(y,packet.grid.height-side));return {x,y,side};}
    function drawImageCrop(role,canvasId,box,afterDraw=()=>{}){const canvas=byId(canvasId);const context=canvas.getContext('2d');context.fillStyle='#020608';context.fillRect(0,0,canvas.width,canvas.height);const image=images[role];const draw=()=>{context.drawImage(image,box.x,box.y,box.side,box.side,0,0,canvas.width,canvas.height);afterDraw(context,canvas,box);};const fail=()=>{context.fillStyle='#ff9b8d';context.font='700 24px system-ui';context.fillText('Image unavailable',28,56);byId('save-state').textContent='A review image could not be loaded. Regenerate the packet after checking local artifacts.';};if(image.complete){if(image.naturalWidth)draw();else fail();}else{image.addEventListener('load',draw,{once:true});image.addEventListener('error',fail,{once:true});}}
    function drawCandidate(candidate){const box=crop(candidate);for(const [role,canvasId] of [['before','before-canvas'],['after','after-canvas'],['candidate-overlay','overlay-canvas']])drawImageCrop(role,canvasId,box);drawReference();}
    function currentRegion(create=false){if(!selected)return null;let region=state.reference_regions[selected.candidate_id];if(!region&&create){region={points:[],closed:false,updated_at:null};state.reference_regions[selected.candidate_id]=region;}return region||{points:[],closed:false,updated_at:null};}
    function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state));return true;}catch{return false;}}
    function projectedToPixel([x,y]){const [gridMinX,,,gridMaxY]=packet.grid.bounds;return [(x-gridMinX)/packet.grid.resolution,(gridMaxY-y)/packet.grid.resolution];}
    function pixelToProjected([x,y]){const [gridMinX,,,gridMaxY]=packet.grid.bounds;return [gridMinX+x*packet.grid.resolution,gridMaxY-y*packet.grid.resolution];}
    function drawReference(){if(!selected)return;const box=crop(selected);drawImageCrop('after','reference-canvas',box,(context,canvas)=>{const region=currentRegion();const points=region.points.map(projectedToPixel).map(([x,y])=>[(x-box.x)/box.side*canvas.width,(y-box.y)/box.side*canvas.height]);if(!points.length)return;context.strokeStyle='#ffc662';context.fillStyle='rgba(255,198,98,.18)';context.lineWidth=5;context.lineJoin='round';context.beginPath();context.moveTo(...points[0]);for(const point of points.slice(1))context.lineTo(...point);if(region.closed){context.closePath();context.fill();}context.stroke();context.fillStyle='#eef8f7';for(const [x,y] of points){context.beginPath();context.arc(x,y,7,0,Math.PI*2);context.fill();context.stroke();}});updateReferenceStatus();}
    function syncReferenceText(){const region=currentRegion();byId('reference-coordinates').value=region.points.map(([x,y])=>`${x.toFixed(2)}, ${y.toFixed(2)}`).join('\\n');drawReference();}
    function updateReferenceStatus(message=''){const region=currentRegion();const status=message||(region.closed?`Closed provisional polygon · ${region.points.length} points · requires adjudication.`:region.points.length?`Draft polygon · ${region.points.length} points · not export-ready.`:'No provisional region drawn.');byId('reference-status').textContent=status;byId('close-polygon').disabled=region.closed;byId('undo-point').disabled=!region.points.length;byId('request-clear').disabled=!region.points.length;}
    function saveRegion(region,message){region.updated_at=new Date().toISOString();state.reference_regions[selected.candidate_id]=region;if(!persist())message+=' Browser storage is unavailable; export before leaving.';syncReferenceText();updateReferenceStatus(message);}
    byId('reference-canvas').addEventListener('pointerdown',event=>{if(!selected)return;const region=currentRegion(true);if(region.closed){updateReferenceStatus('Polygon is closed. Undo a point or clear the region before editing.');return;}const canvas=byId('reference-canvas');const rect=canvas.getBoundingClientRect();const box=crop(selected);const sourceX=box.x+(event.clientX-rect.left)/rect.width*box.side;const sourceY=box.y+(event.clientY-rect.top)/rect.height*box.side;region.points.push(pixelToProjected([sourceX,sourceY]));saveRegion(region,`Added point ${region.points.length}.`);});
    byId('apply-coordinates').addEventListener('click',()=>{if(!selected)return;const lines=byId('reference-coordinates').value.split(/\\r?\\n/).map(line=>line.trim()).filter(Boolean);const points=[];for(const [index,line] of lines.entries()){const parts=line.split(',').map(value=>Number(value.trim()));if(parts.length!==2||parts.some(value=>!Number.isFinite(value))){updateReferenceStatus(`Line ${index+1} must contain one numeric x,y coordinate.`);return;}const [x,y]=parts;const [minX,minY,maxX,maxY]=packet.grid.bounds;if(x<minX||x>maxX||y<minY||y>maxY){updateReferenceStatus(`Line ${index+1} falls outside the ${packet.grid.crs} image bounds.`);return;}points.push([x,y]);}const region=currentRegion(true);region.points=points;region.closed=false;saveRegion(region,points.length?'Coordinates applied as an open draft.':'Coordinate draft cleared.');});
    byId('undo-point').addEventListener('click',()=>{const region=currentRegion(true);if(!region.points.length)return;region.closed=false;region.points.pop();saveRegion(region,'Removed the last point; polygon is open.');});
    function polygonArea(points){let twiceArea=0;for(let index=0;index<points.length;index++){const [x1,y1]=points[index];const [x2,y2]=points[(index+1)%points.length];twiceArea+=x1*y2-x2*y1;}return Math.abs(twiceArea)/2;}
    byId('close-polygon').addEventListener('click',()=>{const region=currentRegion(true);const distinctPoints=new Set(region.points.map(([x,y])=>`${x},${y}`));if(region.points.length<3||distinctPoints.size<3){updateReferenceStatus('Add at least three distinct points before closing the polygon.');return;}if(polygonArea(region.points)<.5){updateReferenceStatus('The polygon has no measurable area. Adjust its points before closing.');return;}region.closed=true;saveRegion(region,'Closed provisional polygon. It still requires qualified adjudication.');});
    byId('request-clear').addEventListener('click',()=>{byId('confirm-clear').hidden=false;byId('cancel-clear').focus();});
    byId('cancel-clear').addEventListener('click',()=>{byId('confirm-clear').hidden=true;byId('request-clear').focus();});
    byId('confirm-clear-region').addEventListener('click',()=>{delete state.reference_regions[selected.candidate_id];persist();byId('confirm-clear').hidden=true;syncReferenceText();byId('reference-coordinates').focus();updateReferenceStatus('Provisional region cleared.');});
    function syncFailure(){const isFailure=byId('decision').value==='false-positive';byId('failure-wrap').hidden=!isFailure;byId('failure-class').required=isFailure;if(!isFailure)byId('failure-class').value='';}
    byId('decision').addEventListener('change',syncFailure);
    byId('review-form').addEventListener('submit',event=>{event.preventDefault();if(!selected)return;state.reviewer={name:byId('reviewer-name').value.trim(),role:byId('reviewer-role').value.trim()};state.decisions[selected.candidate_id]={decision:byId('decision').value,failure_class:byId('failure-class').value||null,note:byId('note').value.trim(),saved_at:new Date().toISOString()};if(persist())byId('save-state').textContent=`Saved ${shortId(selected)} locally.`;else byId('save-state').textContent='Browser storage is unavailable. Export the review JSON to preserve this decision.';renderQueue();});
    function serializeRegion(candidate){const region=state.reference_regions[candidate.candidate_id];if(!region?.points?.length)return null;const closed=region.closed&&region.points.length>=3&&polygonArea(region.points)>=.5;const ring=closed?[...region.points,region.points[0]]:null;return {region_id:`${packet.packet_id}:${candidate.candidate_id}:provisional-1`,candidate_context_id:candidate.candidate_id,geometry_crs:packet.grid.crs,geometry:closed?{type:'Polygon',coordinates:[ring]}:null,projected_points:region.points,pixel_points:region.points.map(projectedToPixel).map(([x,y])=>[Number(x.toFixed(3)),Number(y.toFixed(3))]),review_status:closed?'provisional-candidate-directed':'draft-incomplete',closed,updated_at:region.updated_at||null,boundary:'Candidate-directed provisional geometry; independent qualified review and adjudication required.'};}
    byId('export').addEventListener('click',()=>{state.reviewer={name:byId('reviewer-name').value.trim(),role:byId('reviewer-role').value.trim()};if(!state.reviewer.name||!state.reviewer.role){byId('save-state').textContent='Add reviewer name and role before exporting audit evidence.';(state.reviewer.name?byId('reviewer-role'):byId('reviewer-name')).focus();return;}persist();const referenceRegions=packet.candidates.map(serializeRegion).filter(Boolean);const exportData={review_export_version:'1.1.0',packet_id:packet.packet_id,change_run_id:packet.change_run_id,reviewer:state.reviewer,exported_at:new Date().toISOString(),decisions:packet.candidates.map(candidate=>({candidate_id:candidate.candidate_id,...(state.decisions[candidate.candidate_id]||{decision:'',failure_class:null,note:'',saved_at:null})})),reference_regions:referenceRegions,boundary:'Candidate decisions are not independent reference regions or pipeline accuracy evidence. Candidate-directed provisional regions are not independent adjudicated reference regions.'};const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([JSON.stringify(exportData,null,2)+'\\n'],{type:'application/json'}));link.download=`${packet.packet_id}-review.json`;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);});
    renderQueue();if(packet.candidates.length)selectCandidate(packet.candidates[0],false);
  </script>
</body>
</html>
"""
