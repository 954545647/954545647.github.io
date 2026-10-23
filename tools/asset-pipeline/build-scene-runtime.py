"""Build a separate reliable renderer for a new studio scene: python3 tools/asset-pipeline/build-scene-runtime.py SCENE_ID."""
from pathlib import Path
import sys,re
SID=sys.argv[1]
assert re.fullmatch(r"[a-z0-9-]+", SID)

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / 'vendor/studio-20261023'

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

loader=(VENDOR / 'sun-downloads-v1.js').read_text().replace('./sun-assets-v1.js', f'./{SID}-assets-v1.js')
(VENDOR / f'{SID}-downloads-v1.js').write_text(loader)

text = (VENDOR / 'chunk-CLUPJWV7.js').read_text()
text = 'import{loadModel as loadSunModel,loadTexture as loadSunTexture}from"./sun-downloads-v1.js";' + text
text = replace_once(text, 's.loadAsync(u)', 'loadSunTexture(s,u)')
text = replace_once(text, 'n.loadAsync(u)', 'loadSunModel(n,u)')
(VENDOR / f'chunk-CLUPJWV7-{SID}-v1.js').write_text(text.replace('./sun-downloads-v1.js', f'./{SID}-downloads-v1.js'))

text = (VENDOR / 'map3d-OZBHA54J.js').read_text()
text = 'import{beginAssets,assetsComplete,endAssets}from"./sun-downloads-v1.js";' + text
text = replace_once(text, '"./chunk-CLUPJWV7.js"', '"./chunk-CLUPJWV7-sun-v1.js"')
text = replace_once(text, ',ne=Qt(le,{geo:F,layout:w,style:j}),Fe=!1;', ',assetSession=beginAssets(l),ne=Qt(le,{geo:F,layout:w,style:j}),Fe=!1;')
text = replace_once(text, 'ne.assetsReady().then(()=>{Fe=!0})', 'ne.assetsReady().then(()=>{Fe=assetsComplete(assetSession)})')
text = replace_once(text, 'return va(),()=>{Z=!1,', 'return va(),()=>{endAssets(assetSession);Z=!1,')
text = replace_once(text, '</p></div>\n</main>`,d();let r=', '</p><button id="m3-load-retry" class="m3-chip" hidden>重新加载三维地图</button></div><span id="m3-assets-status" role="status" hidden style="position:absolute;left:20px;bottom:86px;z-index:4;padding:6px 12px;border-radius:20px;background:#ffffffe6;color:#315c4e;font-size:12px"></span>\n</main>`,d();let r=')
text = text.replace('\\u6B63\\u5728\\u94FA\\u5F00\\u6E56\\u5C71\\u2026', '正在加载三维地图…')
(VENDOR / f'map3d-{SID}-reliable-v1.js').write_text(text.replace('./sun-downloads-v1.js', f'./{SID}-downloads-v1.js').replace('./chunk-CLUPJWV7-sun-v1.js',f'./chunk-CLUPJWV7-{SID}-v1.js'))

app = ROOT / 'app.js'
text = app.read_text()
old=':"./map3d-RE5GBLZV.js").then(r=>{a||(o=r.mountMap3D'
new=f':new URLSearchParams(location.hash.split("?")[1]).get("s")==="{SID}"?"./vendor/studio-20261023/map3d-{SID}-reliable-v1.js"'+old
if new not in text:
    text=replace_once(text,old,new)
    app.write_text(text)
bridge=ROOT/'studio-map-bridge-20261023.js'
text=bridge.read_text()
if f"'{SID}'" not in text:
    text=replace_once(text,"['summer-palace', 'sun-yat-sen']",f"['summer-palace', 'sun-yat-sen', '{SID}']")
    bridge.write_text(text)
