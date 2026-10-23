import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import assets from '../../vendor/studio-20261023/qijiang-park-assets-v1.js';
import { beginAssets, loadModel, assetsComplete, endAssets } from '../../vendor/studio-20261023/qijiang-park-downloads-v2.js';

const root = new URL('../../', import.meta.url);
const entries = Object.entries(assets);
const dom = () => {
  const elements = new Map();
  return { querySelector(selector) {
    if (!elements.has(selector)) elements.set(selector, {});
    return elements.get(selector);
  } };
};

test('all scene downloads finish before any model parsing starts', async t => {
  let releaseLast, startedLast;
  const lastStarted = new Promise(resolve => { startedLast = resolve; });
  const holdLast = new Promise(resolve => { releaseLast = resolve; });
  const lastUrl = entries.at(-1)[1].url;
  t.mock.method(globalThis, 'fetch', async url => {
    if (url === lastUrl) { startedLast(); await holdLast; }
    return new Response(await readFile(new URL(url.slice(1), root)));
  });
  const view = dom(), session = beginAssets(view);
  t.after(() => endAssets(session));
  let parses = 0;
  const model = loadModel({ setMeshoptDecoder() {}, parseAsync(bytes) {
    parses++;
    assert.equal(new DataView(bytes).getUint32(0, true), 0x46546c67);
    return { scene: 'decoded model' };
  } }, entries[0][0]);
  await lastStarted;
  assert.equal(parses, 0, 'parsing must not contend with remaining downloads');
  assert.equal(assetsComplete(session), false);
  releaseLast();
  assert.deepEqual(await model, { scene: 'decoded model' });
  assert.equal(parses, 1);
  assert.equal(assetsComplete(session), true);
  assert.match(view.querySelector('#m3-assets-status').textContent, /16\/16/);
});

test('an incomplete scene never starts parsing or reports ready', async t => {
  const failedUrl = entries.at(-1)[1].url;
  t.mock.method(globalThis, 'fetch', async url => new Response(
    url === failedUrl ? new Uint8Array([0]) : await readFile(new URL(url.slice(1), root))
  ));
  const session = beginAssets(dom());
  t.after(() => endAssets(session));
  let parses = 0;
  await assert.rejects(loadModel({ setMeshoptDecoder() {}, parseAsync() { parses++; } }, entries[0][0]), /Incomplete asset/);
  assert.equal(parses, 0);
  assert.equal(assetsComplete(session), false);
});
