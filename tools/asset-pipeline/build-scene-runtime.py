"""Build a separate renderer: build-scene-runtime.py SCENE_ID [vN] [publishedAssetCommit]."""
from pathlib import Path
import sys,re
SID=sys.argv[1]
assert re.fullmatch(r"[a-z0-9-]+", SID)
VERSION=sys.argv[2] if len(sys.argv)>2 else 'v2'
assert re.fullmatch(r"v[0-9]+", VERSION)
FALLBACK_COMMIT=sys.argv[3] if len(sys.argv)>3 else None
if FALLBACK_COMMIT:
    assert re.fullmatch(r'[0-9a-f]{40}', FALLBACK_COMMIT)

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / 'vendor/studio-20261023'

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

loader=(VENDOR / 'sun-downloads-v1.js').read_text().replace('./sun-assets-v1.js', f'./{SID}-assets-v1.js')
loader=replace_once(loader, '  current = session;', '''  // Finish network transfers before parsing geometry or uploading textures. Heavy
  // model work can otherwise delay stream reads long enough to trip idle timers.
  session.downloadsReady = Promise.all(Object.values(assets).map(asset => session.queue.get(asset)))
    .then(() => true, error => { session.downloadError = error; return false; });
  current = session;''')
loader=replace_once(loader, '    loader.setMeshoptDecoder(MeshoptDecoder);', '    if (!await session.downloadsReady) throw session.downloadError;\n    loader.setMeshoptDecoder(MeshoptDecoder);')
loader=replace_once(loader, '      const bytes = await session.queue.get(asset);', '      if (!await session.downloadsReady) throw session.downloadError;\n      const bytes = await session.queue.get(asset);')
if FALLBACK_COMMIT:
    fallback=f'https://raw.githubusercontent.com/954545647/954545647.github.io/{FALLBACK_COMMIT}'
    loader=replace_once(loader, 'createAssetQueue({ onProgress: update,', '''createAssetQueue({ fetcher: (url, options) => {
    // The immutable mirror contains the same public files; SHA-256 still applies.
    const source = options.cache === 'reload' ? url : '''+repr(fallback)+''' + url;
    return fetch(source, options);
  }, onProgress: update,''')
    loader=loader.replace('./asset-queue-v1.mjs','./asset-queue-v2.mjs')
    (VENDOR / 'asset-queue-v2.mjs').write_text((VENDOR / 'asset-queue-v1.mjs').read_text())
(VENDOR / f'{SID}-downloads-{VERSION}.js').write_text(loader)

text = (VENDOR / 'chunk-CLUPJWV7.js').read_text()
text = 'import{loadModel as loadSunModel,loadTexture as loadSunTexture}from"./sun-downloads-v1.js";' + text
text = replace_once(text, 's.loadAsync(u)', 'loadSunTexture(s,u)')
text = replace_once(text, 'n.loadAsync(u)', 'loadSunModel(n,u)')
(VENDOR / f'chunk-CLUPJWV7-{SID}-{VERSION}.js').write_text(text.replace('./sun-downloads-v1.js', f'./{SID}-downloads-{VERSION}.js'))

text = (VENDOR / 'map3d-OZBHA54J.js').read_text()
text = 'import{beginAssets,assetsComplete,endAssets}from"./sun-downloads-v1.js";' + text
text = replace_once(text, '"./chunk-CLUPJWV7.js"', '"./chunk-CLUPJWV7-sun-v1.js"')
text = replace_once(text, ',ne=Qt(le,{geo:F,layout:w,style:j}),Fe=!1;', ',assetSession=beginAssets(l),ne=Qt(le,{geo:F,layout:w,style:j}),Fe=!1;')
text = replace_once(text, 'ne.assetsReady().then(()=>{Fe=!0})', 'ne.assetsReady().then(()=>{Fe=assetsComplete(assetSession)})')
text = replace_once(text, '$e=requestAnimationFrame(va);let e=', '$e=requestAnimationFrame(va);if(!Fe)return;let e=')
text = replace_once(text, 'return va(),()=>{Z=!1,', 'return va(),()=>{endAssets(assetSession);Z=!1,')
text = replace_once(text, '</p></div>\n</main>`,d();let r=', '</p><button id="m3-load-retry" class="m3-chip" hidden>重新加载三维地图</button></div><span id="m3-assets-status" role="status" hidden style="position:absolute;left:20px;bottom:86px;z-index:4;padding:6px 12px;border-radius:20px;background:#ffffffe6;color:#315c4e;font-size:12px"></span>\n</main>`,d();let r=')
text = text.replace('\\u6B63\\u5728\\u94FA\\u5F00\\u6E56\\u5C71\\u2026', '正在加载三维地图…')
(VENDOR / f'map3d-{SID}-reliable-{VERSION}.js').write_text(text.replace('./sun-downloads-v1.js', f'./{SID}-downloads-{VERSION}.js').replace('./chunk-CLUPJWV7-sun-v1.js',f'./chunk-CLUPJWV7-{SID}-{VERSION}.js'))

app = ROOT / 'app.js'
text = app.read_text()
old=':"./map3d-RE5GBLZV.js").then(r=>{a||(o=r.mountMap3D'
new=f':new URLSearchParams(location.hash.split("?")[1]).get("s")==="{SID}"?"./vendor/studio-20261023/map3d-{SID}-reliable-{VERSION}.js"'+old
existing=re.compile(r'\./vendor/studio-20261023/map3d-'+re.escape(SID)+r'-reliable-v[0-9]+\.js')
if existing.search(text):
    text=existing.sub(f'./vendor/studio-20261023/map3d-{SID}-reliable-{VERSION}.js',text)
    app.write_text(text)
elif new not in text:
    text=replace_once(text,old,new)
    app.write_text(text)
bridge=ROOT/'studio-map-bridge-20261023.js'
text=bridge.read_text()
if f"'{SID}'" not in text:
    text=replace_once(text,"['summer-palace', 'sun-yat-sen']",f"['summer-palace', 'sun-yat-sen', '{SID}']")
    bridge.write_text(text)
