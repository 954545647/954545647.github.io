const prefix = '/assets/scenics/summer-palace/models/';
const textures = new Map();
const waiting = [];
let active = 0, total = 0, finished = 0, failed = 0, received = 0;

function progress() {
  const text = document.querySelector('#m3-load-text');
  if (text) text.textContent = `正在加载园林地图 · ${finished}/${total} · 已接收 ${(received / 1e6).toFixed(1)} MB`;
  if (failed) {
    const status = document.querySelector('#m3-status');
    if (status) status.textContent = '部分地图资源下载失败，请刷新重试';
  }
}

function schedule(work) {
  total++;
  progress();
  return new Promise((resolve, reject) => {
    waiting.push(async () => {
      active++;
      try { resolve(await work()); }
      catch (error) { failed++; reject(error); }
      finally {
        active--; finished++; progress();
        if (waiting.length) waiting.shift()();
      }
    });
    if (active < 4) waiting.shift()();
  });
}

async function download(url) {
  let error;
  for (let attempt = 0; attempt < 3; attempt++) {
    const controller = new AbortController();
    let timer;
    const resetIdleTimeout = () => {
      clearTimeout(timer);
      timer = setTimeout(() => controller.abort(), 60000);
    };
    try {
      resetIdleTimeout();
      const response = await fetch(url, {signal: controller.signal});
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${url}`);
      const reader = response.body.getReader();
      const chunks = [];
      let length = 0;
      for (;;) {
        const {done, value} = await reader.read();
        resetIdleTimeout();
        if (done) break;
        chunks.push(value);
        length += value.byteLength;
        received += value.byteLength;
        progress();
      }
      const bytes = new Uint8Array(length);
      let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
      return bytes.buffer;
    } catch (reason) {
      error = reason;
      if (attempt < 2) await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
    } finally {
      clearTimeout(timer);
    }
  }
  throw error;
}

export function loadModel(loader, url) {
  if (!url.startsWith(prefix) || typeof DecompressionStream !== 'function') return loader.loadAsync(url);
  return schedule(async () => {
    let bytes = await download(url + '.gz');
    // Some CDNs decode gzip themselves; accept either HTTP representation.
    if (new Uint8Array(bytes)[0] === 0x1f) {
      bytes = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    }
    if (new TextDecoder().decode(bytes.slice(0, 4)) !== 'glTF') throw new Error('Invalid GLB: ' + url);
    return loader.parseAsync(bytes, url.slice(0, url.lastIndexOf('/') + 1));
  });
}

export function loadTexture(loader, url) {
  if (!url.startsWith(prefix)) return loader.loadAsync(url);
  if (!textures.has(url)) textures.set(url, schedule(async () => {
    const objectUrl = URL.createObjectURL(new Blob([await download(url)], {type: 'image/png'}));
    try { return await loader.loadAsync(objectUrl); }
    finally { URL.revokeObjectURL(objectUrl); }
  }).finally(() => textures.delete(url)));
  return textures.get(url);
}
