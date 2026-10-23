// A bounded, cancellable download queue. A timeout covers both headers and body.
export function createAssetQueue({ fetcher = fetch, concurrency = 3, attempts = 3,
  idleMs = 30000, totalMs = 180000, backoffMs = 800, onProgress = () => {},
  validate = async () => {} } = {}) {
  const entries = new Map(), waiting = [], controllers = new Set();
  let active = 0, cancelled = false;
  const abortError = () => new DOMException('Scene closed', 'AbortError');
  const snapshot = () => {
    const all = [...entries.values()];
    return { total: all.length, complete: all.filter(e => e.state === 'complete').length,
      failed: all.filter(e => e.state === 'failed').length, active,
      bytes: all.reduce((n, e) => n + e.received, 0),
      totalBytes: all.reduce((n, e) => n + (e.asset.bytes || 0), 0),
      retrying: all.some(e => e.state === 'active' && e.attempt > 1) };
  };
  const notify = () => { if (!cancelled) onProgress(snapshot()); };
  async function download(entry) {
    let lastError;
    for (let attempt = 1; attempt <= attempts; attempt++) {
      if (cancelled) throw abortError();
      const controller = new AbortController();
      controllers.add(controller);
      let idle, reader;
      const touch = () => { clearTimeout(idle); idle = setTimeout(() => controller.abort(), idleMs); };
      const deadline = setTimeout(() => controller.abort(), totalMs);
      entry.attempt = attempt; entry.received = 0; notify();
      try {
        touch();
        const response = await fetcher(entry.asset.url, { signal: controller.signal, cache: attempt > 1 ? 'reload' : 'default' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        reader = response.body.getReader();
        const chunks = []; let length = 0;
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          touch(); chunks.push(value); length += value.byteLength;
          entry.received = length; notify();
        }
        const bytes = new Uint8Array(length);
        let offset = 0;
        for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
        if (entry.asset.bytes && bytes.length !== entry.asset.bytes) throw new Error('Incomplete asset');
        await validate(bytes, entry.asset);
        if (cancelled) throw abortError();
        return bytes.buffer;
      } catch (error) {
        lastError = error;
        // Stop a stalled body before retrying, including failed integrity checks.
        controller.abort();
        if (reader) await reader.cancel().catch(() => {});
        if (cancelled) throw abortError();
      } finally {
        clearTimeout(idle); clearTimeout(deadline); controllers.delete(controller);
      }
      if (attempt < attempts) await new Promise(resolve => setTimeout(resolve, backoffMs * attempt));
    }
    throw lastError;
  }
  function pump() {
    while (!cancelled && active < concurrency && waiting.length) {
      const entry = waiting.shift(); active++; entry.state = 'active'; notify();
      download(entry).then(bytes => {
        entry.state = 'complete'; entry.resolve(bytes);
      }, error => {
        entry.state = 'failed'; entry.reject(error);
      }).finally(() => { active--; notify(); pump(); });
    }
  }
  return {
    get(asset) {
      if (cancelled) return Promise.reject(abortError());
      if (entries.has(asset.url)) return entries.get(asset.url).promise;
      const entry = { asset, state: 'queued', received: 0, attempt: 0 };
      entry.promise = new Promise((resolve, reject) => Object.assign(entry, { resolve, reject }));
      entries.set(asset.url, entry); waiting.push(entry); notify(); pump();
      return entry.promise;
    },
    snapshot,
    cancel() {
      cancelled = true;
      for (const controller of controllers) controller.abort();
      for (const entry of waiting.splice(0)) { entry.state = 'failed'; entry.reject(abortError()); }
    },
  };
}
