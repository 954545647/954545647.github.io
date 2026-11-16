// A-you: a lightweight, fully three-dimensional character built with local geometry.
// Part names match the existing travel, walking, waving and boat animation contract.
import {
  ua as Group, ma as Mesh, fb as MeshStandardMaterial, ia as MeshBasicMaterial,
  bb as SphereGeometry, $a as RingGeometry, cb as TorusGeometry,
  db as TubeGeometry, Ua as CatmullRomCurve3, U as Vector3,
  la as BufferGeometry, ka as Float32BufferAttribute,
} from './chunk-XDO2H4SD.js';
import {a as mergeGeometries} from './chunk-6OCEZDHF.js';

export const AYOU = Object.freeze({id:'ayou', name:'阿游', shape:'ayou', color:'#f1dfb9', accent:'#b95943', accessory:'paper-boat'});

export function withAyouCharacters(characters) {
  return [AYOU, ...characters.filter(character => character.id !== AYOU.id)];
}

// Migrate each Zhongshan scene once, then respect later explicit character choices.
export function prepareAyouProfile(profile, scenicId) {
  const previous = profile && typeof profile === 'object' && !Array.isArray(profile) ? profile : {};
  if (!['sun-yat-sen', 'qijiang-park'].includes(scenicId) || previous.ayouVersions?.[scenicId] === 1) return previous;
  const result = {
    ...previous,
    name: !previous.name || /^旅人\d{4}$/.test(previous.name) ? '阿游' : previous.name,
    characters: {...previous.characters, [scenicId]: AYOU.id},
    ayouVersions: {...previous.ayouVersions, [scenicId]: 1},
  };
  try { localStorage.setItem('jj-companion-profile', JSON.stringify(result)); } catch { /* Private browsing still gets A-you for this visit. */ }
  return result;
}

export function createAyouAvatar() {
  const avatar = new Group();
  avatar.name = 'A-you';
  const body = new Group();
  const umbrella = new Group();
  body.add(umbrella);
  avatar.add(body);
  const limbs = [];
  const materials = new Map();
  const palette = {cream:'#f1dfb9', green:'#245b49', fold:'#33725b', darkGreen:'#184535', scarf:'#ad5035', brown:'#60432c', leather:'#95642f', gold:'#d5a34f', paper:'#fff0cf', ink:'#39291f', cheek:'#e8a47e'};

  function material(color) {
    if (!materials.has(color)) materials.set(color, new MeshStandardMaterial({color,roughness:.84,metalness:0,side:2}));
    return materials.get(color);
  }
  function mesh(geometry, color, parent=body, position=[0,0,0], scale=[1,1,1]) {
    const object = new Mesh(geometry, material(color));
    object.position.set(...position);
    object.scale.set(...scale);
    object.castShadow = object.receiveShadow = true;
    parent.add(object);
    return object;
  }
  function sphere(color, position, scale, parent=body) {
    return mesh(new SphereGeometry(1,24,16),color,parent,position,scale);
  }
  function surface(color, points, faces, parent=body) {
    const geometry = new BufferGeometry();
    geometry.setAttribute('position',new Float32BufferAttribute(points.flat(),3));
    geometry.setAttribute('uv',new Float32BufferAttribute(points.flatMap(() => [0,0]),2));
    geometry.setIndex(faces.flat());
    geometry.computeVertexNormals();
    return mesh(geometry,color,parent);
  }
  function curve(color, points, radius, parent=body) {
    return mesh(new TubeGeometry(new CatmullRomCurve3(points.map(p=>new Vector3(...p))),16,radius,6,false),color,parent);
  }

  // Soft cream body and four separate pivots: leg, leg, arm, waving arm.
  sphere(palette.cream,[0,.265,0],[.125,.16,.091]);
  for (const side of [-1,1]) {
    const leg = new Group(); leg.position.set(side*.063,.135,0); body.add(leg); limbs.push(leg);
    sphere(palette.cream,[0,-.051,0],[.043,.067,.046],leg);
    sphere(palette.cream,[0,-.104,.023],[.049,.032,.068],leg);
  }
  for (const side of [-1,1]) {
    const arm = new Group(); arm.position.set(side*.132,.355,.004); body.add(arm); limbs.push(arm);
    sphere(palette.cream,[side*.018,-.055,.013],[.037,.073,.038],arm);
    sphere(palette.cream,[side*.021,-.106,.028],[.042,.042,.039],arm);
  }
  // Large, rounded head; facial features are geometry, visible from every direction.
  sphere(palette.cream,[0,.511,.005],[.167,.153,.132]);
  for (const side of [-1,1]) {
    const eye = sphere(palette.ink,[side*.058,.531,.124],[.020,.029,.010]); eye.rotation.z=side*-.11;
    sphere('#fff8e8',[side*.058-.005,.542,.134],[.006,.008,.003]);
    sphere(palette.cheek,[side*.107,.482,.105],[.027,.017,.005]);
    curve(palette.brown,[[side*.079,.579,.116],[side*.059,.587,.124],[side*.040,.581,.124]],.003);
  }
  curve(palette.ink,[[-.038,.485,.137],[0,.469,.143],[.038,.485,.137]],.0045);

  // A folded paper boat, with an asymmetric paper peak and raised front/rear folds.
  const hat = new Group(); body.add(hat);
  surface(palette.green,[[-.211,.629,.085],[.211,.629,.085],[.192,.638,-.100],[-.192,.638,-.100],[-.035,.838,-.025],[.035,.785,-.060]],[[0,1,4],[1,2,5],[1,5,4],[2,3,5],[3,4,5],[3,0,4]],hat);
  surface(palette.fold,[[-.224,.638,.096],[0,.647,.151],[.224,.638,.096],[.192,.711,.066],[0,.680,.119],[-.192,.711,.066]],[[0,1,4],[0,4,5],[1,2,4],[2,3,4]],hat);
  surface(palette.darkGreen,[[-.215,.640,-.106],[0,.643,-.145],[.215,.640,-.106],[.185,.693,-.083],[0,.673,-.122],[-.185,.693,-.083]],[[0,1,4],[0,4,5],[1,2,4],[2,3,4]],hat);
  curve('#49816a',[[-.188,.707,.069],[0,.678,.122],[.188,.707,.069]],.0025,hat);

  // Rolled scarf and two fabric tails, distinctive even at sandbox scale.
  const scarf = mesh(new TorusGeometry(.096,.020,10,28),palette.scarf,body,[0,.386,.005],[1.24,1,.76]);
  scarf.rotation.x=Math.PI/2;
  surface(palette.scarf,[[-.082,.388,-.015],[-.145,.376,-.052],[-.217,.334,-.039],[-.185,.316,-.040],[-.119,.347,-.020]],[[0,1,4],[1,2,3],[1,3,4]]);
  surface('#963c2c',[[-.077,.383,-.026],[-.115,.357,-.061],[-.166,.299,-.062],[-.132,.294,-.054],[-.087,.343,-.038]],[[0,1,4],[1,2,3],[1,3,4]]);

  // The bag strap wraps around the torso; the bag has a rounded flap and brass button.
  curve(palette.brown,[[.098,.386,.073],[.022,.304,.101],[-.096,.211,.083]],.011);
  curve(palette.brown,[[.098,.386,-.053],[.010,.301,-.098],[-.096,.211,-.061]],.010);
  sphere(palette.leather,[-.115,.197,.055],[.061,.069,.048]);
  sphere('#a3763b',[-.115,.223,.087],[.062,.038,.025]);
  sphere(palette.gold,[-.115,.215,.112],[.009,.011,.004]);
  // A three-panel folded map carried in front of the body.
  const mapPoints=[[-.085,.319,.114],[-.028,.305,.135],[.031,.320,.113],[.086,.306,.134],[-.085,.215,.119],[-.028,.201,.140],[.031,.216,.118],[.086,.202,.139]];
  surface(palette.paper,mapPoints,[[0,4,1],[1,4,5],[1,5,2],[2,5,6],[2,6,3],[3,6,7]]);
  curve('#d7c7a5',[[-.028,.305,.138],[-.028,.201,.143]],.0018);
  curve('#dccdad',[[.031,.320,.116],[.031,.216,.121]],.0018);
  // Map-pin badge beside the scarf.
  const badge=mesh(new TorusGeometry(.014,.0045,8,18),palette.gold,body,[.105,.355,.087]);
  badge.rotation.z=.18;
  surface(palette.gold,[[.092,.348,.090],[.118,.348,.090],[.105,.322,.090]],[[0,1,2]]);

  // Collapse static geometry by material while retaining independently moving limbs.
  function mergeStatic(group) {
    for (const child of [...group.children]) if (child.isGroup) mergeStatic(child);
    const byMaterial = new Map();
    for (const child of [...group.children]) if (child.isMesh) {
      child.updateMatrix();
      const geometry=child.geometry.clone().applyMatrix4(child.matrix);
      const list=byMaterial.get(child.material)||[]; list.push(geometry); byMaterial.set(child.material,list);
      group.remove(child); child.geometry.dispose();
    }
    for (const [mat,geometries] of byMaterial) {
      const merged=mergeGeometries(geometries);
      if (!merged) throw new Error('A-you geometry merge failed');
      const part=new Mesh(merged,mat); part.castShadow=part.receiveShadow=true; group.add(part);
      geometries.forEach(geometry=>geometry.dispose());
    }
  }
  mergeStatic(body);

  const ring = new Mesh(new RingGeometry(.19,.22,40),new MeshBasicMaterial({color:'#43816b',transparent:true,opacity:.52,depthWrite:false}));
  ring.rotation.x=-Math.PI/2; ring.position.y=.012; avatar.add(ring);
  const raft = new Group();
  sphere('#bca480',[0,.035,0],[.29,.065,.42],raft);
  sphere('#dfc89e',[0,.074,0],[.25,.024,.36],raft);
  raft.visible=false; avatar.add(raft);
  avatar.parts={body,um:umbrella,ring,raft,limbs};
  avatar.userData.characterId=AYOU.id;
  return avatar;
}
