import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { gzipSync, gunzipSync } from 'node:zlib';
import assert from 'node:assert/strict';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, weld, meshopt, getBounds } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const scene = JSON.parse(await fs.readFile(path.join(root, 'scenes/sun-yat-sen/map-package.json')));
const urls = [...new Set(JSON.stringify(scene).match(/\/assets\/scenics\/sun-yat-sen\/models\/[^" ]+/g))].sort();
const output = path.join(root, 'assets/scenics/sun-yat-sen/optimized');
await fs.mkdir(output, { recursive: true });
await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder,
});
const manifest = {};
const triangles = doc => doc.getRoot().listMeshes().reduce((n, m) => n + m.listPrimitives().reduce((s, p) => s + (p.getIndices()?.getCount() || p.getAttribute('POSITION').getCount()) / 3, 0), 0);
for (const url of urls) {
  const input = path.join(root, url.slice(1));
  const original = await fs.readFile(input);
  let bytes, suffix;
  if (url.endsWith('.glb')) {
    const doc = await io.read(input);
    const count = triangles(doc), bounds = getBounds(doc.getRoot().listScenes()[0]);
    await doc.transform(dedup(), weld(), meshopt({ encoder: MeshoptEncoder, level: 'medium', quantizePosition: 16, quantizeNormal: 12, quantizeTexcoord: 16 }));
    bytes = Buffer.from(await io.writeBinary(doc));
    const decoded = await io.readBinary(bytes);
    assert.equal(triangles(decoded), count, 'Do not remove geometry: ' + url);
    const after = getBounds(decoded.getRoot().listScenes()[0]);
    const extent = Math.max(...bounds.max.map((v, i) => v - bounds.min[i]));
    for (const key of ['min', 'max']) for (let i = 0; i < 3; i++) {
      assert.ok(Math.abs(bounds[key][i] - after[key][i]) <= Math.max(1e-5, extent / 10000), 'Bounds changed: ' + url);
    }
    const decodedBytes = bytes;
    bytes = gzipSync(bytes, { level: 9 });
    assert.deepEqual(gunzipSync(bytes), decodedBytes);
    // .bin prevents a static host from interpreting the gzip transport as HTTP encoding.
    suffix = '.glb.bin';
  } else {
    // Lossless encoding only: preserve dimensions, colors, alpha, and every pixel.
    bytes = await sharp(original).webp({ lossless: true, effort: 6 }).toBuffer();
    assert.deepEqual(await sharp(original).ensureAlpha().raw().toBuffer(), await sharp(bytes).ensureAlpha().raw().toBuffer());
    suffix = '.webp';
  }
  const hash = createHash('sha256').update(bytes).digest('hex');
  const filename = hash.slice(0, 24) + suffix;
  await fs.writeFile(path.join(output, filename), bytes);
  manifest[url] = { url: '/assets/scenics/sun-yat-sen/optimized/' + filename, bytes: bytes.length, sha256: hash, originalBytes: original.length, encoding: suffix === '.glb.bin' ? 'gzip' : 'identity' };
  console.log(`${url.split('/').at(-2).slice(0, 10)}: ${original.length} -> ${bytes.length}`);
}
const vendor = path.join(root, 'vendor/studio-20261023');
const keep = new Set(Object.values(manifest).map(v => path.basename(v.url)));
for (const file of await fs.readdir(output)) if (!keep.has(file)) await fs.unlink(path.join(output, file));
await fs.writeFile(path.join(vendor, 'sun-assets-v1.js'), 'export default ' + JSON.stringify(manifest, null, 2) + ';\n');
await fs.copyFile(new URL('./node_modules/meshoptimizer/meshopt_decoder.mjs', import.meta.url), path.join(vendor, 'meshopt-decoder-1.3.0.mjs'));
await fs.copyFile(new URL('./node_modules/meshoptimizer/LICENSE.md', import.meta.url), path.join(vendor, 'meshopt-LICENSE.md'));
const totals = Object.values(manifest).reduce((r, v) => ({ original: r.original + v.originalBytes, optimized: r.optimized + v.bytes }), { original: 0, optimized: 0 });
await fs.writeFile(path.join(root, 'scenes/sun-yat-sen/optimization-report.json'), JSON.stringify({ ...totals, files: manifest }, null, 2) + '\n');
console.log(totals);
