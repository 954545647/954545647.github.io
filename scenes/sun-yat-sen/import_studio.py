"""Import this scene's published map and self-contained assets; retain credited 2D content.

Usage: python3 scenes/sun-yat-sen/import_studio.py /path/to/scene.json --base-url URL
The input is a single scene record, never a full account/workspace backup.
"""
import argparse
import hashlib
import json
import re
import struct
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent.parent
STUDIO_ID = 'scenic-amap-b02f802mx8'
SPOT_IDS = {
    'sun-home': 'sun-residence', 'memorial': 'memorial-museum',
    'village-houses': 'folk-houses', 'yang-yin': 'yang-yin',
    'lu-haodong': 'lu-haodong', 'feng-shrine': 'feng-ancestral-hall',
    'zhenyi': 'zhenyi-hall', 'bell': 'warning-bell',
    'lecture-hall': 'conference-hall',
}

def strings(v):
    if isinstance(v, dict):
        for item in v.values(): yield from strings(item)
    elif isinstance(v, list):
        for item in v: yield from strings(item)
    elif isinstance(v, str): yield v

def replace(v, mapping):
    if isinstance(v, dict): return {mapping.get(k, k): replace(x, mapping) for k, x in v.items()}
    if isinstance(v, list): return [replace(x, mapping) for x in v]
    return mapping.get(v, v) if isinstance(v, str) else v

def validate_asset(data, filename):
    if filename.endswith('.glb'):
        if data[:4] != b'glTF' or struct.unpack_from('<I', data, 8)[0] != len(data):
            raise ValueError('Invalid GLB: ' + filename)
        size, kind = struct.unpack_from('<II', data, 12)
        if kind != 0x4E4F534A: raise ValueError('Missing GLB JSON')
        model = json.loads(data[20:20 + size])
        for item in model.get('images', []) + model.get('buffers', []):
            uri = item.get('uri', '')
            if uri and not uri.startswith('data:'): raise ValueError('External GLB asset: ' + uri)
    elif not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Invalid PNG: ' + filename)
    if len(data) > 95_000_000: raise ValueError('Asset exceeds repository size limit')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--asset-cache', type=Path)
    parser.add_argument('--downloads', type=Path, help='Find completed files by SHA-256 prefix; never use .crdownload files')
    args = parser.parse_args()
    remote = json.loads(args.record.read_text())
    assert remote['id'] == STUDIO_ID
    published = remote.get('published')
    if not published: raise ValueError('Publish the studio scene before importing')
    package = published['mapPackage']
    landmarks = package['layout']['landmarks']
    assert len(landmarks) == 9 and all(x.get('asset', {}).get('url') and not x.get('pending') for x in landmarks)
    assert set(package['geography']['spots']) == set(SPOT_IDS)
    local = json.loads((ROOT / 'scenic.json').read_text())
    local_spots = {s['id']: s for s in local['published']['spots']}
    for spot in published['spots']:
        expected = local_spots[SPOT_IDS[spot['id']]]
        assert spot.get('guide', '').startswith(expected['guide']), spot['id']
        assert spot.get('factSource') == expected['factSource'], spot['id']
    mapping = {**SPOT_IDS, STUDIO_ID: 'sun-yat-sen', STUDIO_ID + '-interaction': 'sun-yat-sen-interaction'}
    staged = []
    completed = {}
    if args.downloads:
        for path in args.downloads.iterdir():
            if path.is_file() and path.suffix.lower() in ('.glb', '.png'):
                completed[hashlib.sha256(path.read_bytes()).hexdigest()[:48]] = path
    for url in sorted({u for u in strings(package) if u.startswith('/generated/')}):
        if not re.fullmatch(r'/generated/[0-9a-f]+/(model\.glb|texture\.png)', url):
            raise ValueError('Unexpected asset path: ' + url)
        rel = Path(url.removeprefix('/generated/'))
        cached = args.asset_cache / rel if args.asset_cache else None
        found = cached if cached and cached.is_file() else completed.get(rel.parts[0])
        data = found.read_bytes() if found else urllib.request.urlopen(args.base_url.rstrip('/') + url, timeout=60).read()
        if hashlib.sha256(data).hexdigest()[:48] != rel.parts[0]:
            raise ValueError('Asset hash does not match published reference: ' + url)
        validate_asset(data, rel.name)
        target = SITE / 'assets/scenics/sun-yat-sen/models' / rel
        mapping[url] = '/' + target.relative_to(SITE).as_posix()
        staged.append((target, data))
    package = replace(package, mapping)
    package['manifest']['name'] = '孙中山故居 · 翠亨寻迹'
    # The 2D image has its own WGS84 crop; keep its correctly aligned x/y positions.
    local['published']['mapPackage'] = package
    local['publishNumber'] = remote['publishNumber']
    local['publishedAt'] = remote['publishedAt']
    for target, data in staged:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (ROOT / 'map-package.json').write_text(json.dumps(package, ensure_ascii=False, indent=2))
    (ROOT / 'scenic.json').write_text(json.dumps(local, ensure_ascii=False, indent=2))
    print(f'Imported 9 landmarks and {len(staged)} assets; {sum(len(data) for _,data in staged)/1e6:.1f} MB')

if __name__ == '__main__': main()
