import test from 'node:test';
import assert from 'node:assert/strict';
import { createAssetQueue } from '../../vendor/studio-20261023/asset-queue-v1.mjs';

const asset = url => ({ url, bytes: 3 });
const good = () => new Response(new Uint8Array([1, 2, 3]));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

test('limits concurrency and coalesces shared texture downloads', async () => {
  let active = 0, peak = 0, calls = 0;
  const queue = createAssetQueue({ concurrency: 2, fetcher: async () => {
    calls++; peak = Math.max(peak, ++active); await delay(10); active--; return good();
  } });
  const first = queue.get(asset('/shared'));
  assert.equal(first, queue.get(asset('/shared')));
  await Promise.all([first, ...Array.from({ length: 5 }, (_, n) => queue.get(asset('/' + n)))]);
  assert.equal(calls, 6); assert.equal(peak, 2);
  assert.equal(queue.snapshot().complete, 6);
});

test('retries a network failure and an incomplete response before succeeding', async () => {
  let calls = 0;
  const queue = createAssetQueue({ backoffMs: 0, fetcher: async () => {
    calls++;
    if (calls === 1) throw new TypeError('connection reset');
    if (calls === 2) return new Response(new Uint8Array([1]));
    return good();
  } });
  assert.deepEqual(new Uint8Array(await queue.get(asset('/model'))), new Uint8Array([1, 2, 3]));
  assert.equal(calls, 3); assert.equal(queue.snapshot().failed, 0);
});

test('aborts a stalled response body and exposes terminal failure', async () => {
  let calls = 0;
  const queue = createAssetQueue({ attempts: 2, idleMs: 20, backoffMs: 0, fetcher: async (_, { signal }) => {
    calls++;
    return new Response(new ReadableStream({ start(controller) {
      signal.addEventListener('abort', () => controller.error(new DOMException('Timed out', 'AbortError')), { once: true });
    } }));
  } });
  await assert.rejects(queue.get(asset('/stalled')), { name: 'AbortError' });
  assert.equal(calls, 2); assert.equal(queue.snapshot().failed, 1);
  assert.equal(queue.snapshot().complete, 0);
});

test('allows a slow transfer while chunks continue arriving', async () => {
  const queue = createAssetQueue({ idleMs: 35, totalMs: 500, fetcher: async () => new Response(new ReadableStream({
    async start(controller) {
      for (let n = 1; n <= 3; n++) { await delay(20); controller.enqueue(new Uint8Array([n])); }
      controller.close();
    },
  })) });
  assert.deepEqual(new Uint8Array(await queue.get(asset('/slow'))), new Uint8Array([1, 2, 3]));
});

test('leaving a scene cancels in-flight and queued work without new requests', async () => {
  let calls = 0;
  const queue = createAssetQueue({ concurrency: 1, fetcher: async (_, { signal }) => {
    calls++;
    return new Promise((_, reject) => signal.addEventListener('abort', () => reject(new DOMException('Closed', 'AbortError')), { once: true }));
  } });
  const one = queue.get(asset('/one')), two = queue.get(asset('/two'));
  const assertions = [assert.rejects(one, { name: 'AbortError' }), assert.rejects(two, { name: 'AbortError' })];
  queue.cancel(); await Promise.all(assertions);
  assert.equal(calls, 1);
});

test('rejects corrupted complete-sized payloads and retries integrity checks', async () => {
  let validations = 0;
  const queue = createAssetQueue({ attempts: 2, backoffMs: 0, fetcher: async () => good(), validate: async () => {
    validations++; throw new Error('checksum mismatch');
  } });
  await assert.rejects(queue.get(asset('/corrupt')), /checksum/);
  assert.equal(validations, 2); assert.equal(queue.snapshot().failed, 1);
});
