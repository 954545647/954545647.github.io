// A-you is a local-content guide, with no AI endpoint or account requirement.
const supported = new Set(['sun-yat-sen', 'qijiang-park']);
const root = document.createElement('aside');
root.id = 'ayou-guide';
root.setAttribute('aria-label', '阿游文化导览');
root.innerHTML = `<button class="ayou-launch" type="button" aria-label="打开阿游导览" aria-expanded="false" aria-controls="ayou-panel">
  <img src="/assets/ayou/ayou-welcome-v1.webp" alt="" width="108" height="136" decoding="async">
  <span class="ayou-label">阿游带你逛</span>
</button><section class="ayou-panel" id="ayou-panel" role="dialog" aria-labelledby="ayou-title" hidden>
  <header class="ayou-header"><img src="/assets/ayou/ayou-welcome-v1.webp" alt="戴纸船帽、拿地图的阿游" width="69" height="88">
    <div><p class="ayou-kicker">香山漫游 · 文化向导</p><h2 id="ayou-title">你好，我是阿游</h2><p class="ayou-subtitle">陪你看风景，也读懂故事。</p></div>
  </header><button class="ayou-close" type="button" aria-label="收起阿游导览">×</button>
  <div class="ayou-content"></div>
</section>`;
document.body.append(root);
const launcher = root.querySelector('.ayou-launch');
const panel = root.querySelector('.ayou-panel');
const content = root.querySelector('.ayou-content');
const closer = root.querySelector('.ayou-close');
let scenes = null;
let loading = null;
let revision = 0;

function route() {
  const [page = '', query = ''] = location.hash.slice(1).split('?');
  const params = new URLSearchParams(query);
  return {page: page || 'home', scene: params.get('s'), spot: params.get('id')};
}
function isSupported() {
  const current = route();
  return ['home', 'scenics'].includes(current.page) || (['map', 'spot'].includes(current.page) && supported.has(current.scene));
}
function esc(value = '') {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
}
function safeURL(value) {
  if (typeof value !== 'string' || !value) return '';
  try {
    const url = new URL(value, location.origin);
    return ['http:', 'https:'].includes(url.protocol) ? esc(url.href) : '';
  } catch { return ''; }
}
function mapURL(id) { return '#map?s=' + encodeURIComponent(id); }
function spotURL(scene, id) { return '#spot?s=' + encodeURIComponent(scene) + '&id=' + encodeURIComponent(id); }
function currentScene() { return scenes?.find(s => s.id === route().scene); }
function footer() { return '<nav class="ayou-footer" aria-label="更多风景"><a href="#scenics">全部场景 ↗</a><a href="#home">回到首页</a></nav>'; }
function display(html, focus = false) {
  content.innerHTML = html;
  content.scrollTop = 0;
  if (focus) content.querySelector('h3')?.focus({preventScroll:true});
}
async function loadScenes() {
  if (scenes) return scenes;
  if (!loading) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    loading = fetch('/assets/ayou/content-v1.json', {signal:controller.signal})
      .then(response => { if (!response.ok) throw new Error('Guide content unavailable'); return response.json(); })
      .then(data => {
        if (!Array.isArray(data.scenes) || !data.scenes.every(s => supported.has(s.id) && Array.isArray(s.spots))) throw new Error('Invalid guide content');
        scenes = data.scenes;
        return scenes;
      }).finally(() => { clearTimeout(timer); loading = null; });
  }
  return loading;
}
function showScenes() {
  display(`<p>从哪里开始？跟我去街巷寻迹，或到水岸读一段船厂往事。</p>${scenes.map(s => `<a class="ayou-scene" href="${mapURL(s.id)}"><strong>${esc(s.title)}</strong><small>${s.spots.length} 处文化点位 · 打开沙盘 →</small></a>`).join('')}${footer()}`);
}
function showSpots(scene, focus = false) {
  display(`<p class="ayou-eyebrow">阿游带路 / ${scene.spots.length} 处文化点位</p><h3 tabindex="-1">${esc(scene.title)}</h3><p class="ayou-muted">选一处，我把这里的故事讲给你。</p>${scene.spots.map((s, i) => `<button class="ayou-spot" data-story="${esc(s.id)}" type="button"><span class="ayou-num">${String(i + 1).padStart(2,'0')}</span><span>${esc(s.name)}</span><span class="ayou-arrow" aria-hidden="true">→</span></button>`).join('')}${footer()}`, focus);
}
function showStory(scene, id) {
  const spot = scene.spots.find(s => s.id === id);
  if (!spot) return showSpots(scene);
  const credit = spot.credit || {};
  const creditURL = safeURL(credit.source);
  const licenseURL = safeURL(credit.licenseUrl);
  const creditText = `${esc(credit.artist || '')} · ${esc(credit.license || '')}`;
  const photo = safeURL(spot.photo);
  const source = safeURL(spot.factSource);
  display(`<button class="ayou-back" data-back type="button">← 返回点位列表</button><p class="ayou-eyebrow">阿游讲故事</p><h3 tabindex="-1">${esc(spot.name)}</h3>
    ${photo ? `<figure class="ayou-photo"><img src="${photo}" alt="${esc(spot.name)}实拍" loading="lazy"><figcaption class="ayou-credit">实拍 · ${creditURL ? `<a href="${creditURL}" target="_blank" rel="noopener noreferrer">${creditText}</a>` : creditText}${licenseURL ? ` · <a href="${licenseURL}" target="_blank" rel="noopener noreferrer">许可</a>` : ''}<br>图片按版面缩放、裁切。</figcaption></figure>` : ''}
    <p class="ayou-story">${esc(spot.guide || spot.description || '这处点位的讲解正在整理。')}</p>
    ${source ? `<a class="ayou-muted" href="${source}" target="_blank" rel="noopener noreferrer">查看讲解来源 ↗</a>` : ''}
    <div class="ayou-actions"><button class="ayou-primary" data-locate="${esc(spot.id)}" type="button">在地图上找到它</button><a class="ayou-secondary" href="${spotURL(scene.id, spot.id)}">查看实拍</a></div>${footer()}`, true);
}
function close({focus = false} = {}) {
  revision++;
  panel.hidden = true;
  launcher.hidden = false;
  launcher.setAttribute('aria-expanded', 'false');
  if (focus && !root.hidden) launcher.focus({preventScroll:true});
}
async function open() {
  const token = ++revision;
  panel.hidden = false;
  launcher.hidden = true;
  launcher.setAttribute('aria-expanded', 'true');
  closer.focus({preventScroll:true});
  display('<p role="status">阿游正在翻开地图…</p>');
  try {
    await loadScenes();
    if (token !== revision || panel.hidden) return;
    const scene = currentScene();
    if (scene && route().page === 'spot' && route().spot) showStory(scene, route().spot);
    else if (scene) showSpots(scene);
    else showScenes();
  } catch {
    if (token !== revision || panel.hidden) return;
    display('<p role="status">故事暂时没能打开，请再试一次。</p><button class="ayou-primary" data-retry type="button">重新加载故事</button>' + footer());
  }
}
function updateRoute() {
  close();
  root.hidden = !isSupported();
}
launcher.addEventListener('click', open);
closer.addEventListener('click', () => close({focus:true}));
root.addEventListener('click', event => {
  event.stopPropagation();
  const button = event.target.closest('button');
  const scene = currentScene();
  if (button?.hasAttribute('data-retry')) open();
  if (scene && button?.hasAttribute('data-story')) showStory(scene, button.dataset.story);
  if (scene && button?.hasAttribute('data-back')) showSpots(scene, true);
  if (scene && button?.hasAttribute('data-locate')) {
    const id = button.dataset.locate;
    // Reuse native map markers so the 3D camera and detail card stay in sync.
    const marker = document.querySelector(`.m3-tag[data-spot="${CSS.escape(id)}"], [data-marker="${CSS.escape(id)}"]`);
    close();
    if (route().page === 'map' && marker) { marker.click(); marker.focus({preventScroll:true}); }
    else location.hash = `${mapURL(scene.id)}&id=${encodeURIComponent(id)}&view=scroll`;
  }
  if (event.target.closest('a[href^="#"]')) close();
});
root.addEventListener('keydown', event => {
  event.stopPropagation();
  if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); close({focus:true}); }
});
// Do not let guide gestures reach the map's document-level controls.
for (const type of ['pointerdown', 'pointerup', 'wheel']) {
  root.addEventListener(type, event => event.stopPropagation(), {passive:true});
}
document.addEventListener('pointerdown', event => { if (!panel.hidden && !root.contains(event.target)) close(); });
window.addEventListener('hashchange', updateRoute);
updateRoute();
