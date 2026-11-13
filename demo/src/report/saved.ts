import Ajv2020 from 'ajv/dist/2020';
import schema from '../../../schemas/standalone-report.v1.schema.json';
import { sha256 } from '../engine/dataset-io';
import type { PredictionIntent } from '../ui-types';

const validate = new Ajv2020({ strict: false, allErrors: false }).compile(schema);
export function validateSaved(value: unknown): void {
  if (!validate(value)) throw new Error('INVALID_STANDALONE_REPORT_SCHEMA: ' + JSON.stringify(validate.errors));
}
export async function loadPublicSaved(intent: PredictionIntent): Promise<unknown> {
  const base = import.meta.env.BASE_URL + 'examples/';
  const response = await fetch(base + 'manifest.json');
  if (!response.ok) throw new Error('EXAMPLE_MANIFEST_UNAVAILABLE');
  const manifest = await response.json();
  const entry = manifest.examples[0];
  const variant = entry.variants?.[intent] ?? entry;
  if (!/^tablet(?:\.[a-z_]+)?\.saved\.json$/.test(variant.file)) throw new Error('INVALID_EXAMPLE_PATH');
  const file = await fetch(base + variant.file);
  if (!file.ok) throw new Error('EXAMPLE_UNAVAILABLE');
  const bytes = new Uint8Array(await file.arrayBuffer());
  if (await sha256(bytes) !== variant.sha256) throw new Error('EXAMPLE_CONTENT_HASH_MISMATCH');
  const report = JSON.parse(new TextDecoder().decode(bytes)); validateSaved(report); return report;
}
