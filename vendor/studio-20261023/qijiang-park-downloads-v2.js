import assets from './qijiang-park-assets-v1.js';
import { MeshoptDecoder } from './meshopt-decoder-1.3.0.mjs';
import { createAssetQueue } from './asset-queue-v1.mjs';

let current;
export function beginAssets(root) {
  current?.queue.cancel();
  const session = { root, textures: new Map(), parseFailed: false, closed: false };
  const update = state => {
    const text = root.querySelector('#m3-load-text');
    if (text) text.textContent = `${state.retrying ? '网络较慢，正在重试' : '正在加载三维地图'} · ${state.complete}/${state.total} · ${(state.bytes / 1e6).toFixed(1)} / ${(state.totalBytes / 1e6).toFixed(1)} MB`;
    if (state.failed) showFailure(session);
  };
  session.queue = createAssetQueue({ onProgress: update, validate: async (bytes, asset) => {
    const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
    const hash = [...digest].map(x => x.toString(16).padStart(2, '0')).join('');
    if (hash !== asset.sha256) throw new Error('Asset checksum mismatch');
  } });
  // Finish network transfers before parsing geometry or uploading textures. Heavy
  // model work can otherwise delay stream reads long enough to trip idle timers.
  session.downloadsReady = Promise.all(Object.values(assets).map(asset => session.queue.get(asset)))
    .then(() => true, error => { session.downloadError = error; return false; });
  current = session;
  const retry = root.querySelector('#m3-load-retry');
  if (retry) retry.onclick = () => location.reload();
  return session;
}
function showFailure(session) {
  if (session.closed) return;
  const text = session.root.querySelector('#m3-load-text');
  if (text) text.textContent = '部分三维资源尚未加载成功，请重试。';
  const button = session.root.querySelector('#m3-load-retry');
  if (button) button.hidden = false;
}
export function assetsComplete(session) {
  const state = session.queue.snapshot();
  const success = !session.closed && !session.parseFailed && !state.failed && state.complete === state.total;
  if (success) {
    const badge = session.root.querySelector('#m3-assets-status');
    if (badge) { badge.textContent = `三维资源 ${state.complete}/${state.total} 已就绪`; badge.hidden = false; }
  } else showFailure(session);
  return success;
}
export function endAssets(session) {
  session.closed = true; session.queue.cancel(); session.textures.clear();
  if (current === session) current = null;
}
export async function loadModel(loader, url) {
  const asset = assets[url], session = current;
  if (!asset || !session) return loader.loadAsync(url);
  try {
    if (!await session.downloadsReady) throw session.downloadError;
    loader.setMeshoptDecoder(MeshoptDecoder);
    let bytes = await session.queue.get(asset);
    if (asset.encoding === 'gzip') {
      bytes = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    }
    return await loader.parseAsync(bytes, asset.url.slice(0, asset.url.lastIndexOf('/') + 1));
  } catch (error) { session.parseFailed = true; showFailure(session); throw error; }
}
export function loadTexture(loader, url) {
  const asset = assets[url], session = current;
  if (!asset || !session) return loader.loadAsync(url);
  if (!session.textures.has(url)) session.textures.set(url, (async () => {
    try {
      if (!await session.downloadsReady) throw session.downloadError;
      const bytes = await session.queue.get(asset);
      const objectUrl = URL.createObjectURL(new Blob([bytes], { type: 'image/webp' }));
      try { return await loader.loadAsync(objectUrl); }
      finally { URL.revokeObjectURL(objectUrl); }
    } catch (error) { session.parseFailed = true; showFailure(session); throw error; }
  })());
  return session.textures.get(url);
}
