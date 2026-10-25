import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const lock=JSON.parse(fs.readFileSync('architecture/toolchain.json','utf8'));
const catalog=JSON.parse(fs.readFileSync('architecture/catalog.json','utf8'));
const get=(p)=>JSON.parse(fs.readFileSync(p,'utf8'));
const old=(p)=>execFileSync('git',['show',`${lock.sourceRevision}:${p}`],{encoding:'utf8',maxBuffer:4*1024*1024});
const specs=Object.fromEntries(lock.documents.map(x=>[x.name,get(`architecture/${x.name}.architecture.json`)]));
test('four current entry URLs use Archify and retain a source-backed map',()=>{
 assert.equal(lock.documents.length,4);
 for(const x of lock.documents){
  const html=fs.readFileSync(x.page,'utf8');
  assert.match(html,/archify/i);
  assert.match(html,/system-map/);
  assert.ok(!/C:[\\/]Users[\\/]|\\\\WIN-PKH9JPNF98L|file:\/\/\//i.test(html),'no author-local paths');
  for(const n of specs[x.name].components)assert.ok(n.sources?.length,'each node has a source');
 }
});
test('phase2 node IDs and original directed relationships survive',()=>{
 for(const name of ['phase2-logical','phase2-physical']){
  const before=old(catalog[name].page),d=specs[name];
  const ids=[...before.matchAll(/<g[^>]*data-node-id="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(ids.length,name==='phase2-logical'?17:14,'original node extractor must match the expected baseline inventory');
  assert.deepEqual(d.components.map(n=>n.id).sort(),ids.sort());
  const edges=[...before.matchAll(/<path[^>]*data-edge-from="([^"]+)"[^>]*data-edge-to="([^"]+)"[^>]*>/g)];
  assert.equal(edges.length,13,'original relationship extractor must match the expected baseline inventory');
  assert.equal(d.connections.length,14,'only the documented reverse VPN relation (logical) and Runner → Harbor push (physical) are added');
  for(const m of edges){
   const e=d.connections.find(e=>e.from===m[1]&&e.to===m[2]);assert.ok(e,`${m[1]} → ${m[2]}`);
   const label=m[0].match(/data-edge-label="([^"]*)"/);
   if(label){
    if(name==='phase2-logical'&&e.id==='txapi-to-relay')assert.equal(e.label,'DB 5432 · NP-03');
    else assert.equal(e.label,label[1]);
   }
   if(m[0].includes('marker-start='))assert.ok(d.connections.some(e=>e.from===m[2]&&e.to===m[1]),'bidirectional VPN needs the reverse relation');
  }
 }
});
test('all six phase2 logical guide IDs and full descriptions are steps',()=>{
 const before=old('phase2_logical_architecture.html');
 const views=JSON.parse(before.match(/<script id="archify-guided-views-data"[^>]*>([\s\S]*?)<\/script>/)[1]);
 assert.equal(views.length,6);
 assert.deepEqual(catalog['phase2-logical'].guides,views);
 const md=fs.readFileSync('architecture/phase2-logical.archify.md','utf8');
 for(const v of views){assert.ok(md.includes(`| ${v.id} |`));assert.ok(md.includes(v.note));}
});
test('DB ownership and node image-pull remain distinct',()=>{
 const d=specs['phase2-logical'];
 assert.ok(!d.connections.some(e=>e.from==='engine'&&e.to==='db'));
 assert.ok(d.connections.some(e=>e.from==='txapi'&&e.to==='relay'));
 assert.ok(d.connections.some(e=>e.from==='workers'&&e.to==='relay'&&e.label.includes('pull')));
 assert.ok(d.cards.some(c=>c.items.some(s=>s.includes('node pull은 Pod 정책과 별도'))));
});
test('historical phase1 diagrams remain unchanged in Git',()=>{
 for(const p of ['logical_architecture.html','physical_architecture.html'])execFileSync('git',['diff','--exit-code',lock.sourceRevision,'--',p]);
});
test('published build manifest matches the eight generated files',()=>{
 const manifest=get('architecture/build-manifest.json');assert.equal(manifest.outputs.length,8);
 assert.equal(manifest.archify.revision,lock.revision);assert.equal(manifest.sourceRevision,lock.sourceRevision);
 for(const o of manifest.outputs){
  const b=fs.readFileSync(o.path);assert.equal(createHash('sha256').update(b).digest('hex'),o.sha256);assert.equal(b.length,o.bytes);
  assert.equal(createHash('sha256').update(fs.readFileSync(o.source)).digest('hex'),o.sourceSha256);
  assert.ok(o.gates.validate==='pass'&&o.gates.deliver==='pass'&&o.gates.check==='pass');
  if(o.type==='architecture')assert.equal(o.gates['browser-check'],'pass');
 }
});
