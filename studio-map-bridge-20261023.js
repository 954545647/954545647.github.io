import {
  MAP_PACKAGES as visitorPackages,
  registerMapPackage as registerLegacyPackage,
} from './packages-IXPDYRHP.js';
import {e as registerStudioPackage} from './vendor/studio-20261023/chunk-HYDGCO3D.js';
import {c as studioPackageFor} from './vendor/studio-20261023/chunk-IE6RBOGA.js';

// The visitor router and the newer renderer have separate package registries.
// Validate new scenes with their matching schema, then expose the same runtime
// package to the visitor router so its 3D links and scene detection agree.
export function registerMapPackage(id, data) {
  const scenicId = id.replace(/^draft:/, '');
  if (!['summer-palace', 'sun-yat-sen'].includes(scenicId)) {
    return registerLegacyPackage(id, data);
  }
  const errors = registerStudioPackage(id, data);
  if (errors.length) throw new Error(`${scenicId}: ${errors.join('; ')}`);
  const runtime = studioPackageFor(id);
  if (runtime) visitorPackages[id] = runtime;
  else delete visitorPackages[id];
  return [];
}
