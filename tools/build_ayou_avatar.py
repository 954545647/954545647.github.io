"""Apply narrow, checked hooks to the frozen map runtimes and version the entry."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/studio-20261023'


def replace_once(text, before, after):
    count = text.count(before)
    if count != 1:
        raise ValueError(f'Expected one runtime hook, found {count}: {before[:100]}')
    return text.replace(before, after, 1)


def build():
    filenames = [
        ('map3d-qijiang-park-reliable-v5.js', 'map3d-qijiang-ayou-v1.js'),
        ('map3d-sun-reliable-v1.js', 'map3d-sun-ayou-v1.js'),
    ]
    for original, output in filenames:
        text = (VENDOR / original).read_text()
        text = 'import{createAyouAvatar,withAyouCharacters,prepareAyouProfile}from"./ayou-avatar-v1.js";' + text
        text = replace_once(text, 'function Fn(l){', 'function Fn(l){if(l.shape==="ayou")return createAyouAvatar();')
        text = replace_once(text, 'T[w].rotation.z=p&&w===3?-2.25+', 'T[w].rotation.z=p&&w===3?(l.userData.characterId==="ayou"?2.25:-2.25)+')
        text = replace_once(text, 'let B=dn(p.interaction),', 'let B=withAyouCharacters(dn(p.interaction)),')
        text = replace_once(text, 'let S=ge.has(b.characters?.[f])?', 'b=prepareAyouProfile(b,f);let S=ge.has(b.characters?.[f])?')
        # Preserve the migration flag when the native nickname/character selector saves.
        text = replace_once(text, 'JSON.stringify({name:U,characters:{...b.characters,[f]:S}})', 'JSON.stringify({...b,name:U,characters:{...b.characters,[f]:S}})')
        # GitHub Pages has no companion server; keep local avatar controls usable.
        text = replace_once(text, 'let Y=ee&&p.interaction.companions?.enabled!==!1,', 'let Y=!1,')
        text = replace_once(text, r'\u6B64\u5730\u56FE\u672A\u5F00\u653E\u540C\u6E38', '单人漫游中，可以切换旅伴、挥手和探索地图。')
        (VENDOR / output).write_text(text)
    app = (ROOT / 'app-qijiang-v5.js').read_text()
    for original, output in filenames:
        app = replace_once(app, original, output)
    (ROOT / 'app-ayou-avatar-v1.js').write_text(app)
    (ROOT / 'app.js').write_text(app)
    boot = (ROOT / 'boot-qijiang-v5.js').read_text().replace('app-qijiang-v5.js', 'app-ayou-avatar-v1.js')
    (ROOT / 'boot-ayou-avatar-v1.js').write_text(boot)
    index = ROOT / 'index.html'
    index.write_text(index.read_text().replace('/boot-qijiang-v5.js','/boot-ayou-avatar-v1.js'))
    print('A-you integrated into both Zhongshan map runtimes; versioned entry ready.')


if __name__ == '__main__':
    build()
