import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
process.chdir(root);
const lock=JSON.parse(fs.readFileSync('architecture/toolchain.json','utf8'));
const tool=path.resolve(process.env.ARCHIFY_ROOT || '.cache/archify');
function run(command,args){
  const p=spawnSync(command,args,{cwd:root,encoding:'utf8',maxBuffer:12*1024*1024});
  if(p.error)throw p.error;
  if(p.status!==0)throw new Error(`${command} failed (${p.status})\n${p.stdout}\n${p.stderr}`);
  return p.stdout.trim();
}
const actual=run('git',['-C',tool,'rev-parse','HEAD']);
if(actual!==lock.revision)throw new Error(`Archify revision mismatch: expected ${lock.revision}, found ${actual}`);
if(run('git',['-C',tool,'status','--porcelain','--untracked-files=normal']))throw new Error('Archify checkout must be clean');
const pkg=JSON.parse(fs.readFileSync(path.join(tool,'archify/package.json'),'utf8'));
if(pkg.version!==lock.version)throw new Error('Archify version mismatch');
const cli=path.join(tool,'archify/bin/archify.mjs');
const checkOnly=process.argv.includes('--check');
const previous=checkOnly?JSON.parse(fs.readFileSync('architecture/build-manifest.json','utf8')):null;
if(checkOnly){
  if(previous.schemaVersion!==1||previous.archify?.revision!==actual||previous.archify?.version!==pkg.version||previous.sourceRevision!==lock.sourceRevision)throw new Error('Manifest toolchain or source revision differs from lock');
  const expected=lock.documents.flatMap(e=>[`diagrams/${e.name}.html`,e.page]).sort();
  if(JSON.stringify(previous.outputs.map(o=>o.path).sort())!==JSON.stringify(expected))throw new Error('Manifest output inventory differs from lock');
}
run('git',['cat-file','-e',`${lock.sourceRevision}^{commit}`]);
const receipts=path.join('.archify-receipts',new Date().toISOString().replace(/[:.]/g,'-'));
const manifest={schemaVersion:1,archify:{revision:actual,version:pkg.version},sourceRevision:lock.sourceRevision,outputs:[]};
for(const entry of lock.documents){
  if(!/^[a-z0-9-]+$/.test(entry.name)||!/^phase[12]_[a-z_]+\.html$/.test(entry.page))throw new Error('Unsafe document manifest path');
  const input=`architecture/${entry.name}.architecture.json`, diagram=`diagrams/${entry.name}.html`;
  const spec=JSON.parse(fs.readFileSync(input,'utf8'));
  if(spec.meta.repository?.revision!==lock.sourceRevision)throw new Error('Source revision differs from toolchain lock');
  const pageSource=`architecture/${entry.name}.archify.md`;
  for(const [type,source,output] of [['architecture',input,diagram],['explainer',pageSource,entry.page]]){
    const args=checkOnly?['check',output,'--require-provenance','--json']:['finalize',type,source,output,'--repo-root','.',...(type==='architecture'?['--quality','showcase']:[]),'--out-dir',path.join(receipts,`${entry.name}-${type}`),'--json'];
    const response=JSON.parse(run(process.execPath,[cli,...args]));
    if(!(response.ok===true || response.status==='pass'))throw new Error(`Unsuccessful ${type} receipt`);
    const bytes=fs.readFileSync(output);
    const sha256=createHash('sha256').update(bytes).digest('hex');
    const sourceSha256=createHash('sha256').update(fs.readFileSync(source)).digest('hex');
    if(checkOnly){
      const record=previous.outputs.find(x=>x.path===output);
      if(!record||record.type!==type||record.source!==source||record.sha256!==sha256||record.bytes!==bytes.length||record.sourceSha256!==sourceSha256)throw new Error(`Manifest mismatch: ${output}`);
    }else{
      const gates=response.gates;
      if(!gates||gates.validate!=='pass'||gates.deliver!=='pass'||gates.check!=='pass'||(type==='architecture'&&gates['browser-check']!=='pass'))throw new Error('Required gates absent or unsuccessful');
      manifest.outputs.push({path:output,source,type,sourceSha256,sha256,bytes:bytes.length,gates});
    }
    console.log(`${entry.name} ${type}: pass`);
  }
}
if(!checkOnly)fs.writeFileSync('architecture/build-manifest.json',JSON.stringify(manifest,null,2)+'\n');
