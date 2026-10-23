import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import assets from '../../vendor/studio-20261023/qijiang-park-assets-v1.js';
import { beginAssets, loadModel, assetsComplete, endAssets } from '../../vendor/studio-20261023/qijiang-park-downloads-v5.js';

const root = new URL('../../', import.meta.url);
const entries = Object.entries(assets);
const assetPath = url => url.slice(url.indexOf('/assets/') + 1);
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
    if (url.endsWith(lastUrl)) { startedLast(); await holdLast; }
    return new Response(await readFile(new URL(assetPath(url), root)));
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
    url.endsWith(failedUrl) ? new Uint8Array([0]) : await readFile(new URL(assetPath(url), root))
  ));
  const session = beginAssets(dom());
  t.after(() => endAssets(session));
  let parses = 0;
  await assert.rejects(loadModel({ setMeshoptDecoder() {}, parseAsync() { parses++; } }, entries[0][0]), /Incomplete asset/);
  assert.equal(parses, 0);
  assert.equal(assetsComplete(session), false);
});

test('uses the immutable GitHub mirror first and retries through Pages', async t => {
  const firstUrl = entries[0][1].url;
  const mirrors = [], pages = [];
  t.mock.method(globalThis, 'fetch', async url => {
    if (url.startsWith('https:')) mirrors.push(url);
    else pages.push(url);
    if (url.startsWith('https:') && url.endsWith(firstUrl)) throw new TypeError('Mirror connection stalled');
    return new Response(await readFile(new URL(assetPath(url), root)));
  });
  const session = beginAssets(dom());
  t.after(() => endAssets(session));
  await loadModel({ setMeshoptDecoder() {}, parseAsync() { return {}; } }, entries[0][0]);
  assert.equal(mirrors.length, 16);
  assert.deepEqual(pages, [firstUrl]);
  assert.match(mirrors[0], /^https:\/\/raw\.githubusercontent\.com\/954545647\/954545647\.github\.io\/[0-9a-f]{40}\/assets\//);
  assert.equal(assetsComplete(session), true);
});
