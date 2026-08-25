"""Self-contained HTML for candidate-hidden reference labeling."""

# ruff: noqa: E501

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from echoatlas.evaluation.review import LabelingPacket


def render_labeling_html(packet: LabelingPacket) -> str:
    payload = json.dumps(packet.model_dump(mode="json"), separators=(",", ":")).replace(
        "</", "<\\/"
    )
    return _TEMPLATE.replace("__PACKET_JSON__", payload)


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EchoAtlas candidate-hidden labeling</title>
  <style>
    :root { color-scheme:dark; --bg:#061116; --panel:#0b1b21; --line:#29434b; --text:#eef8f7; --muted:#a9bcc0; --mint:#82e6d4; --amber:#ffc662; --danger:#ff9b8d; }
    * { box-sizing:border-box; }
    [hidden] { display:none !important; }
    body { margin:0; background:var(--bg); color:var(--text); font:15px/1.45 ui-sans-serif,system-ui,-apple-system,sans-serif; }
    button,input,select,textarea { font:inherit; outline-offset:3px; }
    :focus-visible { outline:3px solid var(--mint); }
    header { padding:24px; border-bottom:1px solid var(--line); display:flex; gap:24px; justify-content:space-between; align-items:start; flex-wrap:wrap; }
    h1,h2,h3,p { margin-top:0; }
    h1 { margin-bottom:6px; font-size:clamp(23px,3vw,34px); }
    .eyebrow { color:var(--mint); text-transform:uppercase; letter-spacing:.14em; font-weight:800; font-size:12px; }
    .meta,.help { color:var(--muted); }
    .status { border:1px solid #356c65; color:var(--mint); border-radius:999px; padding:7px 11px; font-weight:800; }
    .boundary { margin:20px 24px; padding:16px 18px; border:1px solid #795b27; background:#291f10; border-radius:8px; }
    .boundary strong { color:var(--amber); }
    main { display:grid; grid-template-columns:minmax(230px,290px) minmax(0,1fr); gap:16px; padding:0 24px 28px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:10px; overflow:hidden; }
    .panel-heading { padding:16px; border-bottom:1px solid var(--line); }
    .queue { max-height:calc(100vh - 220px); overflow:auto; }
    .tile { width:100%; border:0; border-bottom:1px solid var(--line); background:transparent; color:var(--text); padding:12px 16px; text-align:left; cursor:pointer; }
    .tile:hover,.tile[aria-current="true"] { background:#123039; }
    .tile strong,.tile small { display:block; }
    .tile small { color:var(--muted); margin-top:4px; }
    .workspace { padding:18px; }
    .views { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:16px 0; }
    figure { margin:0; min-width:0; }
    canvas { width:100%; aspect-ratio:1; display:block; background:#020608; border:1px solid var(--line); border-radius:6px; }
    #label-canvas { cursor:crosshair; touch-action:none; }
    figcaption { padding-top:7px; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.1em; font-weight:800; }
    .labeling-tools { display:grid; grid-template-columns:minmax(240px,1fr) minmax(240px,1fr); gap:16px; padding:16px; border:1px solid #45616a; border-radius:8px; background:#08171c; }
    label { display:grid; gap:6px; font-weight:700; }
    input,select,textarea { width:100%; color:var(--text); background:#071318; border:1px solid #45616a; border-radius:6px; padding:10px; }
    textarea { min-height:92px; resize:vertical; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }
    .primary,.secondary,.danger { border-radius:6px; padding:10px 14px; font-weight:800; cursor:pointer; }
    .primary { background:var(--mint); color:#031310; border:1px solid var(--mint); }
    .secondary { background:transparent; color:var(--text); border:1px solid #58717a; }
    .danger { background:transparent; color:var(--danger); border:1px solid #98574f; }
    button:disabled { opacity:.45; cursor:not-allowed; }
    .live-status { color:var(--mint); min-height:1.45em; margin:10px 0 0; }
    .regions { list-style:none; padding:0; margin:10px 0 0; }
    .regions li { border-top:1px solid var(--line); padding:10px 0; }
    .regions li:first-child { border-top:0; }
    .regions .actions { margin-top:6px; }
    .review-form { margin-top:18px; border-top:1px solid var(--line); padding-top:18px; }
    .reviewer,.classification { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; }
    footer { color:var(--muted); border-top:1px solid var(--line); padding:18px 24px 28px; font-size:13px; }
    @media (max-width:1000px) { main { grid-template-columns:1fr; } .queue { max-height:250px; } .views,.labeling-tools { grid-template-columns:1fr; } }
    @media (max-width:560px) { header,main { padding-left:14px; padding-right:14px; } .boundary { margin-left:14px; margin-right:14px; } .reviewer,.classification { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <header>
    <div><div class="eyebrow">EchoAtlas · local labeling packet</div><h1>Candidate-hidden reference labeling</h1><p class="meta" id="run-meta"></p></div>
    <div class="status">Local-only · candidates hidden</div>
  </header>
  <section class="boundary" role="note"><strong>Evidence boundary</strong><br><span id="boundary-copy"></span> This packet cannot verify reviewer qualifications or establish accuracy by itself.</section>
  <main>
    <aside class="panel" aria-label="Labeling tile queue"><div class="panel-heading"><div class="eyebrow">Coverage queue</div><h2 id="queue-title"></h2></div><div class="queue" id="queue"></div></aside>
    <section class="panel workspace" aria-labelledby="tile-title">
      <div class="eyebrow">Before/after comparison</div><h2 id="tile-title" tabindex="-1">Select a tile</h2><p class="meta" id="tile-meta"></p>
      <div class="views">
        <figure><canvas id="before-canvas" width="720" height="720"></canvas><figcaption>Before · no overlay</figcaption></figure>
        <figure><canvas id="after-canvas" width="720" height="720"></canvas><figcaption>After · no overlay</figcaption></figure>
        <figure><canvas id="label-canvas" width="720" height="720" aria-label="After image labeling surface. Click or tap to add boundary points."></canvas><figcaption>Reference drawing · candidates hidden</figcaption></figure>
      </div>
      <section class="labeling-tools" aria-labelledby="draw-title">
        <div><h3 id="draw-title">Draw a provisional region</h3><p class="help">Add points on the after image or enter projected coordinates. Closed regions remain provisional until qualified adjudication.</p><label>Projected coordinates<textarea id="coordinates" spellcheck="false" placeholder="One x,y coordinate per line" aria-describedby="coordinate-help"></textarea><span class="help" id="coordinate-help">Coordinates use <span id="crs"></span> and must fall inside the selected tile.</span></label><div class="actions"><button class="secondary" id="apply-coordinates" type="button">Apply coordinates</button><button class="secondary" id="undo" type="button">Undo point</button><button class="primary" id="close-region" type="button">Close and save region</button><button class="danger" id="request-clear-draft" type="button">Clear draft</button></div><div id="confirm-clear-draft" hidden role="group" aria-label="Confirm clearing open draft"><strong>Clear this open draft?</strong><div class="actions"><button class="danger" id="confirm-clear-draft-button" type="button">Yes, clear draft</button><button class="secondary" id="cancel-clear-draft" type="button">Cancel</button></div></div><p class="live-status" id="draw-status" role="status" aria-live="polite"></p></div>
        <div><h3>Saved regions in this tile</h3><p class="help">Removal requires an explicit confirmation. Overlapping tiles may show the same feature; adjudication must deduplicate it later.</p><ul class="regions" id="regions"></ul></div>
      </section>
      <form class="review-form" id="review-form">
        <div class="reviewer"><label>Reviewer name<input id="reviewer-name" autocomplete="name" required></label><label>Reviewer role or qualification<input id="reviewer-role" placeholder="e.g. SAR domain reviewer" required></label></div>
        <div class="classification"><label>Tile review status<select id="tile-decision" required><option value="">Pending</option><option value="regions-drawn">One or more provisional regions drawn</option><option value="reviewed-no-reference-region">Reviewed; no supportable region identified</option><option value="unresolved">Unresolved</option></select></label><label>Tile note<textarea id="tile-note" maxlength="1000" placeholder="Record visible evidence, ambiguity, and quality limitations without inferring cause, damage, identity, intent, or operational status."></textarea></label></div>
        <div class="actions"><button class="primary" type="submit">Save tile review</button><button class="secondary" id="export" type="button">Export labeling JSON</button><span class="live-status" id="save-status" role="status" aria-live="polite"></span></div>
      </form>
    </section>
  </main>
  <footer><span id="footer-copy"></span><br>Source imagery remains local and is not embedded in this HTML or export. Machine-candidate geometry, scores, and identifiers are not packet inputs.</footer>
  <script>
    const packet=__PACKET_JSON__;
    const storageKey=`echoatlas-labeling:${packet.packet_id}`;
    const state=(()=>{try{const stored=JSON.parse(localStorage.getItem(storageKey)||'{}');return {reviewer:stored?.reviewer||{},tile_reviews:stored?.tile_reviews||{},regions:Array.isArray(stored?.regions)?stored.regions:[],drafts:stored?.drafts||{}};}catch{return {reviewer:{},tile_reviews:{},regions:[],drafts:{}};}})();
    const tileById=new Map(packet.tiles.map(tile=>[tile.tile_id,tile]));
    const allowedDecisions=new Set(['regions-drawn','reviewed-no-reference-region','unresolved']);
    function safePoints(value,tile,{minimum=0}={}){if(!Array.isArray(value)||value.length<minimum)return null;const points=[];for(const point of value){if(!Array.isArray(point)||point.length!==2||point.some(coordinate=>!Number.isFinite(coordinate)))return null;if(!pointInsideTile(tile,point))return null;points.push([point[0],point[1]]);}return points;}
    function pointInsideTile(tile,point){const [tileX,tileY,width,height]=tile.source_box;const [x,y]=projectedToPixel(point);return x>=tileX&&x<=tileX+width&&y>=tileY&&y<=tileY+height;}
    function normalizeStoredState(){state.reviewer={name:typeof state.reviewer?.name==='string'?state.reviewer.name:'',role:typeof state.reviewer?.role==='string'?state.reviewer.role:''};const reviews={};if(state.tile_reviews&&typeof state.tile_reviews==='object'&&!Array.isArray(state.tile_reviews)){for(const [tileId,review] of Object.entries(state.tile_reviews)){if(!tileById.has(tileId)||!review||typeof review!=='object'||!allowedDecisions.has(review.decision))continue;reviews[tileId]={decision:review.decision,note:typeof review.note==='string'?review.note.slice(0,1000):'',saved_at:typeof review.saved_at==='string'?review.saved_at:null};}}state.tile_reviews=reviews;const regionIds=new Set();state.regions=state.regions.flatMap(region=>{const tile=tileById.get(region?.tile_id);const points=tile?safePoints(region?.points,tile,{minimum:3}):null;if(!tile||!points||polygonArea(points)<.5||typeof region.region_id!=='string'||regionIds.has(region.region_id))return [];regionIds.add(region.region_id);return [{region_id:region.region_id,tile_id:tile.tile_id,points,created_at:typeof region.created_at==='string'?region.created_at:null,review_status:'provisional-candidate-hidden'}];});const drafts={};if(state.drafts&&typeof state.drafts==='object'&&!Array.isArray(state.drafts)){for(const [tileId,draft] of Object.entries(state.drafts)){const tile=tileById.get(tileId);const points=tile?safePoints(draft?.points,tile):null;if(tile&&points)drafts[tileId]={points,updated_at:typeof draft?.updated_at==='string'?draft.updated_at:null};}}state.drafts=drafts;}
    normalizeStoredState();
    const images={};let selected=null;let pendingRemoval=null;
    for(const artifact of packet.artifacts){const image=new Image();image.src=artifact.source_url;images[artifact.role]=image;}
    const byId=id=>document.getElementById(id);
    byId('run-meta').textContent=`${packet.processing_run_id} · ${packet.tiles.length} deterministic coverage tiles · ${packet.source_license.provider} ${packet.source_license.spdx}`;
    byId('boundary-copy').textContent=packet.labeling_boundary;
    byId('queue-title').textContent=`${packet.tiles.length} coverage tiles`;
    byId('footer-copy').textContent=`${packet.packet_id} · ${packet.processing_aoi_id}`;
    byId('crs').textContent=packet.grid.crs;
    byId('reviewer-name').value=state.reviewer.name||'';byId('reviewer-role').value=state.reviewer.role||'';
    function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state));return true;}catch{return false;}}
    function regionsForTile(tile){return state.regions.filter(region=>region.tile_id===tile.tile_id);}
    function draftForTile(tile,create=false){let draft=state.drafts[tile.tile_id];if(!draft&&create){draft={points:[],updated_at:null};state.drafts[tile.tile_id]=draft;}return draft||{points:[],updated_at:null};}
    function renderQueue(){const queue=byId('queue');queue.replaceChildren();for(const tile of packet.tiles){const button=document.createElement('button');const title=document.createElement('strong');const detail=document.createElement('small');const decision=state.tile_reviews[tile.tile_id]?.decision||'pending';button.type='button';button.className='tile';button.setAttribute('aria-current',selected?.tile_id===tile.tile_id?'true':'false');title.textContent=`${tile.tile_id} · row ${tile.row}, column ${tile.column}`;detail.textContent=`${regionsForTile(tile).length} regions · ${decision}`;button.replaceChildren(title,detail);button.onclick=()=>selectTile(tile);queue.append(button);}}
    function selectTile(tile,moveFocus=true){selected=tile;pendingRemoval=null;byId('confirm-clear-draft').hidden=true;renderQueue();byId('tile-title').textContent=`${tile.tile_id} · coverage tile`;const [x,y,width,height]=tile.source_box;byId('tile-meta').textContent=`row ${tile.row}, column ${tile.column} · source pixels ${x},${y} · ${width}×${height}`;const review=state.tile_reviews[tile.tile_id]||{};byId('tile-decision').value=review.decision||'';byId('tile-note').value=review.note||'';syncDraftText();renderRegions();drawTile();if(moveFocus)byId('tile-title').focus();}
    function drawCrop(role,canvasId,afterDraw=()=>{}){const [x,y,width,height]=selected.source_box;const canvas=byId(canvasId);const context=canvas.getContext('2d');context.fillStyle='#020608';context.fillRect(0,0,canvas.width,canvas.height);const image=images[role];const draw=()=>{context.drawImage(image,x,y,width,height,0,0,canvas.width,canvas.height);afterDraw(context,canvas);};const fail=()=>{context.fillStyle='#ff9b8d';context.font='700 24px system-ui';context.fillText('Image unavailable',28,56);byId('save-status').textContent='A source image could not be loaded. Regenerate the packet after checking local artifacts.';};if(image.complete){if(image.naturalWidth)draw();else fail();}else{image.addEventListener('load',draw,{once:true});image.addEventListener('error',fail,{once:true});}}
    function projectedToPixel([x,y]){const [minX,,,maxY]=packet.grid.bounds;return [(x-minX)/packet.grid.resolution,(maxY-y)/packet.grid.resolution];}
    function pixelToProjected([x,y]){const [minX,,,maxY]=packet.grid.bounds;return [minX+x*packet.grid.resolution,maxY-y*packet.grid.resolution];}
    function canvasPoints(points,canvas){const [tileX,tileY,width,height]=selected.source_box;return points.map(projectedToPixel).map(([x,y])=>[(x-tileX)/width*canvas.width,(y-tileY)/height*canvas.height]);}
    function drawPolygon(context,points,{closed,color,fill}){if(!points.length)return;context.strokeStyle=color;context.fillStyle=fill;context.lineWidth=5;context.lineJoin='round';context.beginPath();context.moveTo(...points[0]);for(const point of points.slice(1))context.lineTo(...point);if(closed){context.closePath();context.fill();}context.stroke();context.fillStyle='#eef8f7';for(const [x,y] of points){context.beginPath();context.arc(x,y,6,0,Math.PI*2);context.fill();context.stroke();}}
    function drawTile(){if(!selected)return;drawCrop('before','before-canvas');drawCrop('after','after-canvas');drawCrop('after','label-canvas',(context,canvas)=>{for(const region of regionsForTile(selected))drawPolygon(context,canvasPoints(region.points,canvas),{closed:true,color:'#82e6d4',fill:'rgba(130,230,212,.16)'});drawPolygon(context,canvasPoints(draftForTile(selected).points,canvas),{closed:false,color:'#ffc662',fill:'transparent'});});updateDrawStatus();}
    function syncDraftText(){byId('coordinates').value=draftForTile(selected).points.map(([x,y])=>`${x.toFixed(2)}, ${y.toFixed(2)}`).join('\\n');}
    function updateDrawStatus(message=''){const count=draftForTile(selected).points.length;byId('draw-status').textContent=message||(count?`Open draft · ${count} points.`:'No open draft.');byId('undo').disabled=!count;byId('request-clear-draft').disabled=!count;}
    function saveDraft(draft,message){draft.updated_at=new Date().toISOString();state.drafts[selected.tile_id]=draft;if(!persist())message+=' Browser storage is unavailable; export before leaving.';syncDraftText();drawTile();updateDrawStatus(message);}
    byId('label-canvas').addEventListener('pointerdown',event=>{if(!selected)return;const canvas=byId('label-canvas');const rect=canvas.getBoundingClientRect();const [tileX,tileY,width,height]=selected.source_box;const sourceX=tileX+(event.clientX-rect.left)/rect.width*width;const sourceY=tileY+(event.clientY-rect.top)/rect.height*height;const draft=draftForTile(selected,true);draft.points.push(pixelToProjected([sourceX,sourceY]));saveDraft(draft,`Added point ${draft.points.length}.`);});
    byId('apply-coordinates').addEventListener('click',()=>{const lines=byId('coordinates').value.split(/\\r?\\n/).map(line=>line.trim()).filter(Boolean);const points=[];const [tileX,tileY,width,height]=selected.source_box;for(const [index,line] of lines.entries()){const values=line.split(',').map(value=>Number(value.trim()));if(values.length!==2||values.some(value=>!Number.isFinite(value))){updateDrawStatus(`Line ${index+1} must contain one numeric x,y coordinate.`);return;}const pixel=projectedToPixel(values);if(pixel[0]<tileX||pixel[0]>tileX+width||pixel[1]<tileY||pixel[1]>tileY+height){updateDrawStatus(`Line ${index+1} falls outside ${selected.tile_id}.`);return;}points.push(values);}const draft=draftForTile(selected,true);draft.points=points;saveDraft(draft,points.length?'Coordinates applied to the open draft.':'Draft cleared.');});
    byId('undo').addEventListener('click',()=>{const draft=draftForTile(selected,true);draft.points.pop();saveDraft(draft,'Removed the last point.');});
    byId('request-clear-draft').addEventListener('click',()=>{byId('confirm-clear-draft').hidden=false;byId('cancel-clear-draft').focus();});
    byId('cancel-clear-draft').addEventListener('click',()=>{byId('confirm-clear-draft').hidden=true;byId('request-clear-draft').focus();});
    byId('confirm-clear-draft-button').addEventListener('click',()=>{delete state.drafts[selected.tile_id];persist();byId('confirm-clear-draft').hidden=true;syncDraftText();drawTile();byId('coordinates').focus();updateDrawStatus('Draft cleared.');});
    function polygonArea(points){let twiceArea=0;for(let index=0;index<points.length;index++){const [x1,y1]=points[index];const [x2,y2]=points[(index+1)%points.length];twiceArea+=x1*y2-x2*y1;}return Math.abs(twiceArea)/2;}
    function nextRegionId(){let sequence=regionsForTile(selected).length+1;let id;do{id=`${selected.tile_id}-R-${String(sequence++).padStart(2,'0')}`;}while(state.regions.some(region=>region.region_id===id));return id;}
    byId('close-region').addEventListener('click',()=>{const draft=draftForTile(selected,true);const distinct=new Set(draft.points.map(([x,y])=>`${x},${y}`));if(draft.points.length<3||distinct.size<3){updateDrawStatus('Add at least three distinct points before closing the region.');return;}if(polygonArea(draft.points)<.5){updateDrawStatus('The region has no measurable area. Adjust its points before closing.');return;}state.regions.push({region_id:nextRegionId(),tile_id:selected.tile_id,points:draft.points,created_at:new Date().toISOString(),review_status:'provisional-candidate-hidden'});delete state.drafts[selected.tile_id];if(!byId('tile-decision').value)byId('tile-decision').value='regions-drawn';persist();syncDraftText();renderRegions();renderQueue();drawTile();updateDrawStatus('Region saved locally. Qualified adjudication is still required.');});
    function renderRegions(){const list=byId('regions');list.replaceChildren();const regions=regionsForTile(selected);if(!regions.length){const item=document.createElement('li');item.textContent='No saved regions in this tile.';list.append(item);return;}for(const region of regions){const item=document.createElement('li');const title=document.createElement('strong');title.textContent=`${region.region_id} · ${region.points.length} points`;item.append(title);const actions=document.createElement('div');actions.className='actions';if(pendingRemoval===region.region_id){const warning=document.createElement('span');warning.textContent='Remove this saved region?';const confirm=document.createElement('button');confirm.type='button';confirm.className='danger';confirm.textContent='Yes, remove';confirm.onclick=()=>{state.regions=state.regions.filter(item=>item.region_id!==region.region_id);pendingRemoval=null;persist();renderRegions();renderQueue();drawTile();};const cancel=document.createElement('button');cancel.type='button';cancel.className='secondary';cancel.textContent='Cancel';cancel.onclick=()=>{pendingRemoval=null;renderRegions();};actions.append(warning,confirm,cancel);}else{const remove=document.createElement('button');remove.type='button';remove.className='danger';remove.textContent='Remove region';remove.onclick=()=>{pendingRemoval=region.region_id;renderRegions();};actions.append(remove);}item.append(actions);list.append(item);}}
    function decisionConflict(tile,decision){const regionCount=regionsForTile(tile).length;if(decision==='regions-drawn'&&!regionCount)return 'is marked regions drawn but has no saved region';if(decision==='reviewed-no-reference-region'&&regionCount)return 'is marked no region but has saved regions';return null;}
    byId('review-form').addEventListener('submit',event=>{event.preventDefault();const decision=byId('tile-decision').value;const conflict=decisionConflict(selected,decision);if(conflict){byId('save-status').textContent=`${selected.tile_id} ${conflict}. Resolve the contradiction before saving.`;byId('tile-decision').focus();return;}state.reviewer={name:byId('reviewer-name').value.trim(),role:byId('reviewer-role').value.trim()};state.tile_reviews[selected.tile_id]={decision,note:byId('tile-note').value.trim(),saved_at:new Date().toISOString()};if(persist())byId('save-status').textContent=`Saved ${selected.tile_id} locally.`;else byId('save-status').textContent='Browser storage is unavailable. Export before leaving.';renderQueue();});
    function serializeRegion(region){const ring=[...region.points,region.points[0]];return {...region,geometry_crs:packet.grid.crs,geometry:{type:'Polygon',coordinates:[ring]},projected_points:region.points,pixel_points:region.points.map(projectedToPixel).map(([x,y])=>[Number(x.toFixed(3)),Number(y.toFixed(3))]),boundary:'Candidate-hidden provisional geometry; qualified review, deduplication, and adjudication required.'};}
    byId('export').addEventListener('click',()=>{state.reviewer={name:byId('reviewer-name').value.trim(),role:byId('reviewer-role').value.trim()};if(!state.reviewer.name||!state.reviewer.role){byId('save-status').textContent='Add reviewer name and role before exporting audit evidence.';(state.reviewer.name?byId('reviewer-role'):byId('reviewer-name')).focus();return;}const conflictingTile=packet.tiles.find(tile=>{const decision=state.tile_reviews[tile.tile_id]?.decision||'';return decisionConflict(tile,decision);});if(conflictingTile){selectTile(conflictingTile);byId('save-status').textContent=`${conflictingTile.tile_id} has a contradictory saved review. Resolve it before exporting.`;byId('tile-decision').focus();return;}persist();const tileReviews=packet.tiles.map(tile=>({tile_id:tile.tile_id,...(state.tile_reviews[tile.tile_id]||{decision:'',note:'',saved_at:null})}));const reviewed=tileReviews.filter(review=>review.decision).length;const drafts=packet.tiles.map(tile=>({tile_id:tile.tile_id,points:draftForTile(tile).points,updated_at:draftForTile(tile).updated_at})).filter(draft=>draft.points.length);const exportData={labeling_export_version:'1.0.0',packet_id:packet.packet_id,processing_run_id:packet.processing_run_id,source_processing_manifest_sha256:packet.source_processing_manifest_sha256,reviewer:state.reviewer,exported_at:new Date().toISOString(),coverage:{status:reviewed===packet.tiles.length?'complete':'partial',reviewed_tiles:reviewed,total_tiles:packet.tiles.length},tile_reviews:tileReviews,reference_regions:state.regions.map(serializeRegion),incomplete_drafts:drafts,boundary:'Candidate geometry and scores were absent during labeling. Exported regions remain provisional until qualified independent review, deduplication, and adjudication.'};const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([JSON.stringify(exportData,null,2)+'\\n'],{type:'application/json'}));link.download=`${packet.packet_id}-labels.json`;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);});
    renderQueue();if(packet.tiles.length)selectTile(packet.tiles[0],false);
  </script>
</body>
</html>
"""
