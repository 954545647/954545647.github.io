import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createAyouAvatar,prepareAyouProfile,withAyouCharacters} from '../vendor/studio-20261023/ayou-avatar-v1.js';
import {ba as Box3,U as Vector3} from '../vendor/studio-20261023/chunk-XDO2H4SD.js';

test('A-you fits the existing avatar rig and shared geometry clone contract', () => {
  const avatar=createAyouAvatar();
  const {body,um,ring,raft,limbs}=avatar.parts;
  assert.equal(limbs.length,4);
  assert.equal(raft.visible,false);
  assert.equal(body.parent,avatar);
  assert.equal(um.parent,body);
  assert.equal(ring.parent,avatar);
  // This is the map runtime's clone/remap algorithm, including hidden boat parts.
  const clone=avatar.clone(true),original=[],copies=[];
  avatar.traverse(node=>original.push(node));clone.traverse(node=>copies.push(node));
  const mapping=new Map(original.map((node,index)=>[node.uuid,copies[index]]));
  for (const part of Object.values(avatar.parts).flat()) assert.ok(mapping.get(part.uuid));
  avatar.updateMatrixWorld(true);
  const bounds=new Box3().setFromObject(body),size=bounds.getSize(new Vector3());
  assert.ok(bounds.min.y>=-.01 && bounds.max.y<=.90,JSON.stringify(bounds));
  assert.ok(size.x>.4 && size.x<.6,`Width ${size.x}`);
  let triangles=0,draws=0;
  body.traverse(node=>{
    if(!node.isMesh)return;
    draws++;
    const geometry=node.geometry;
    for(const value of geometry.attributes.position.array) assert.ok(Number.isFinite(value));
    triangles+=(geometry.index?.count||geometry.attributes.position.count)/3;
  });
  assert.ok(triangles<30000,`Triangles ${triangles}`);
  assert.ok(draws<30,`Draw calls ${draws}`);
  console.log(`A-you geometry: ${Math.round(triangles)} triangles, ${draws} body draw calls; height ${size.y.toFixed(3)}`);
});

test('default migration is once per Zhongshan scene and preserves personal names and other scenes',()=>{
  const old={name:'小林',characters:{'qijiang-park':'fox',westlake:'bunny'},extra:'keep'};
  const upgraded=prepareAyouProfile(old,'qijiang-park');
  assert.equal(upgraded.name,'小林');assert.equal(upgraded.extra,'keep');
  assert.equal(upgraded.characters['qijiang-park'],'ayou');assert.equal(upgraded.characters.westlake,'bunny');
  assert.equal(old.characters['qijiang-park'],'fox');
  const chosen={...upgraded,characters:{...upgraded.characters,'qijiang-park':'fox'}};
  assert.equal(prepareAyouProfile(chosen,'qijiang-park').characters['qijiang-park'],'fox');
  assert.equal(prepareAyouProfile(chosen,'sun-yat-sen').characters['sun-yat-sen'],'ayou');
  assert.equal(prepareAyouProfile(old,'westlake'),old);
  assert.equal(prepareAyouProfile({name:'旅人1162'},'qijiang-park').name,'阿游');
});

test('A-you is present once and existing options remain selectable',()=>{
  const choices=withAyouCharacters([{id:'fox'},{id:'ayou'},{id:'bunny'}]);
  assert.deepEqual(choices.map(c=>c.id),['ayou','fox','bunny']);
});

test('both runtime builds preserve movement and download code with only avatar hooks',async()=>{
  for(const [before,after] of [['map3d-qijiang-park-reliable-v5.js','map3d-qijiang-ayou-v1.js'],['map3d-sun-reliable-v1.js','map3d-sun-ayou-v1.js']]){
    const dir=new URL('../vendor/studio-20261023/',import.meta.url);
    const source=await readFile(new URL(before,dir),'utf8');
    let built=await readFile(new URL(after,dir),'utf8');
    built=built.replace('import{createAyouAvatar,withAyouCharacters,prepareAyouProfile}from"./ayou-avatar-v1.js";','')
      .replace('function Fn(l){if(l.shape==="ayou")return createAyouAvatar();','function Fn(l){')
      .replace('T[w].rotation.z=p&&w===3?(l.userData.characterId==="ayou"?2.25:-2.25)+','T[w].rotation.z=p&&w===3?-2.25+')
      .replace('let Y=!1,','let Y=ee&&p.interaction.companions?.enabled!==!1,')
      .replace('单人漫游中，可以切换旅伴、挥手和探索地图。',String.raw`\u6B64\u5730\u56FE\u672A\u5F00\u653E\u540C\u6E38`)
      .replace('let B=withAyouCharacters(dn(p.interaction)),','let B=dn(p.interaction),')
      .replace('b=prepareAyouProfile(b,f);let S=','let S=')
      .replace('JSON.stringify({...b,name:U,characters:{...b.characters,[f]:S}})','JSON.stringify({name:U,characters:{...b.characters,[f]:S}})');
    assert.equal(built,source);
  }
});
