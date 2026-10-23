"""Merge one published studio scene into an existing, credited visitor scene package.

Never copies other scenes, account details or the studio task history into the repository.
Model files are copied from an optional cache, or downloaded from --base-url.
Usage: python3 tools/sync_studio_scene.py BACKUP scenes/summer-palace \
  --studio-id scenic-amap-b000a7o1cu --base-url https://studio.example
"""
import argparse
import copy
import json
import shutil
import struct
import urllib.request
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent

def walk(value):
    if isinstance(value, dict):
        for item in value.values(): yield from walk(item)
    elif isinstance(value, list):
        for item in value: yield from walk(item)
    elif isinstance(value, str): yield value

def transform(value, replace):
    if isinstance(value, dict): return {k: transform(v, replace) for k,v in value.items()}
    if isinstance(value, list): return [transform(v, replace) for v in value]
    return replace.get(value,value) if isinstance(value,str) else value

def check_asset(data, name):
    if name.endswith('.glb'):
        if data[:4] != b'glTF': raise ValueError(f'Not a GLB: {name}')
        length,kind=struct.unpack_from('<II',data,12)
        if kind != 0x4E4F534A: raise ValueError(f'GLB has no JSON: {name}')
        model=json.loads(data[20:20+length])
        for entry in model.get('images',[])+model.get('buffers',[]):
            uri=entry.get('uri','')
            if uri and not uri.startswith('data:'):
                raise ValueError(f'GLB has an unresolved external dependency: {name}: {uri}')
    elif name.endswith('.png') and not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError(f'Not a PNG: {name}')
    if len(data)>95_000_000: raise ValueError(f'Asset is too large for GitHub: {name}')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('backup',type=Path);ap.add_argument('scene',type=Path)
    ap.add_argument('--studio-id',required=True);ap.add_argument('--base-url',required=True)
    ap.add_argument('--asset-cache',type=Path)
    args=ap.parse_args()
    backup=json.loads(args.backup.read_text()); states=backup.get('state',backup)
    remote=next(s for s in states['scenics'] if s['id']==args.studio_id)
    published=remote.get('published')
    if not published: raise ValueError('The studio scene has not been published')
    pkg=copy.deepcopy(published['mapPackage'])
    if any(x.get('pending') for x in pkg['layout']['landmarks']):
        raise ValueError('Map still contains unfinished landmarks')
    scene=args.scene.resolve(); local=json.loads((scene/'scenic.json').read_text()); sid=local['id']
    local_spots={s['id']:s for s in local['published']['spots']}
    remote_spots={s['id']:s for s in published['spots']}
    if local_spots.keys()!=remote_spots.keys():raise ValueError('Spot IDs do not match')
    urls=sorted({u for u in walk(pkg) if u.startswith('/generated/')})
    staged=[]; rewrite={args.studio_id:sid}
    for url in urls:
        rel=Path(url.removeprefix('/generated/'))
        if '..' in rel.parts:raise ValueError('Unsafe asset path')
        cached=args.asset_cache/rel if args.asset_cache else None
        data=cached.read_bytes() if cached and cached.is_file() else urllib.request.urlopen(args.base_url.rstrip('/')+url,timeout=45).read()
        check_asset(data,rel.name)
        target=SITE/'assets/scenics'/sid/'models'/rel
        rewrite[url]='/'+target.relative_to(SITE).as_posix();staged.append((target,data))
    pkg=transform(pkg,rewrite)
    local['published']['mapPackage']=pkg
    for spot_id,raw in local_spots.items():
        current=remote_spots[spot_id]
        for k in ('x','y','heading','scene','narration'):
            if k in current:raw[k]=current[k]
        node=pkg['geography']['network']['nodes'][pkg['geography']['spots'][spot_id]['node']]
        frame=pkg['geography']['frame'];projection=frame['projection'];origin=frame['origin']
        raw['lnglat']=[round(origin[0]+node[0]/projection['lonUnits'],7),round(origin[1]-node[1]/projection['latUnits'],7)]
        raw['coordinateSource']='生成端地图包 · WGS84；北宫门与谐趣园已校正至园内可达位置'
        if raw['guide'].strip()!=current.get('guide','').strip():raise ValueError(f'Guide mismatch: {spot_id}')
        if not current.get('factSource'):raise ValueError(f'Missing official source: {spot_id}')
    local['publishNumber']=remote['publishNumber'];local['publishedAt']=remote['publishedAt'];local['draft']=False
    local['published']['map'].update(name='颐和园 · 湖山园林绘卷',legend='依据 OpenStreetMap 与三维地图坐标绘制；园林插画示意，非测绘地图',custom=True)
    if not (scene/'map-illustrated.png').is_file():raise ValueError('Missing aligned 2D illustration')
    for target,data in staged:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    shutil.copyfile(scene/'map-illustrated.png',scene/'map.png')
    (scene/'studio-map-package.json').write_text(json.dumps(pkg,ensure_ascii=False,indent=2))
    (scene/'scenic.json').write_text(json.dumps(local,ensure_ascii=False,indent=1))
    print(f'{sid}: synced {len(local_spots)} spots and {len(staged)} model/texture assets from published v{remote["publishNumber"]}')

if __name__=='__main__':main()
