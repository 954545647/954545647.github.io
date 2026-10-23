"""Patch only the Sun Yat-sen entry in the mirrored bundle; keep other scenes intact."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / 'vendor/studio-20261023'

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

text = (VENDOR / 'chunk-CLUPJWV7.js').read_text()
text = 'import{loadModel as loadSunModel,loadTexture as loadSunTexture}from"./sun-downloads-v1.js";' + text
text = replace_once(text, 's.loadAsync(u)', 'loadSunTexture(s,u)')
text = replace_once(text, 'n.loadAsync(u)', 'loadSunModel(n,u)')
(VENDOR / 'chunk-CLUPJWV7-sun-v1.js').write_text(text)

text = (VENDOR / 'map3d-OZBHA54J.js').read_text()
text = 'import{beginAssets,assetsComplete,endAssets}from"./sun-downloads-v1.js";' + text
text = replace_once(text, '"./chunk-CLUPJWV7.js"', '"./chunk-CLUPJWV7-sun-v1.js"')
text = replace_once(text, ',ne=Qt(le,{geo:F,layout:w,style:j}),Fe=!1;', ',assetSession=beginAssets(l),ne=Qt(le,{geo:F,layout:w,style:j}),Fe=!1;')
text = replace_once(text, 'ne.assetsReady().then(()=>{Fe=!0})', 'ne.assetsReady().then(()=>{Fe=assetsComplete(assetSession)})')
text = replace_once(text, 'return va(),()=>{Z=!1,', 'return va(),()=>{endAssets(assetSession);Z=!1,')
text = replace_once(text, '</p></div>\n</main>`,d();let r=', '</p><button id="m3-load-retry" class="m3-chip" hidden>重新加载三维地图</button></div><span id="m3-assets-status" role="status" hidden style="position:absolute;left:20px;bottom:86px;z-index:4;padding:6px 12px;border-radius:20px;background:#ffffffe6;color:#315c4e;font-size:12px"></span>\n</main>`,d();let r=')
text = text.replace('\\u6B63\\u5728\\u94FA\\u5F00\\u6E56\\u5C71\\u2026', '正在加载三维地图…')
(VENDOR / 'map3d-sun-reliable-v1.js').write_text(text)

app = ROOT / 'app.js'
text = app.read_text()
old = '"./vendor/studio-20261023/map3d-OZBHA54J.js?v=20261023-sun3d"'
new = '"./vendor/studio-20261023/map3d-sun-reliable-v1.js"'
if old in text:
    text = replace_once(text, old, new)
    app.write_text(text)
else:
    assert new in text
