export type FactorColorKind = 'categorical' | 'continuous';
export type FactorColorValue = string | number | boolean;
export interface FactorColorLevel {
  level_id: string;
  value: FactorColorValue;
  label: string;
  count: number;
  color: string;
}
export interface FactorColorLegendDescriptor {
  protocol_version: 'domains.factor_colors.v1';
  factor_id: string;
  kind: FactorColorKind;
  unit: string | null;
  origin: string;
  missing_color: string;
  missing_label: string;
  missing_count: number;
  domain: { min: number; max: number } | null;
  levels: FactorColorLevel[];
}
export interface FactorColorField {
  id: string;
  kind: FactorColorKind;
  unit: string | null;
  origin: string;
  row_keys: string[];
  values: (string | number | boolean | null)[];
  levels?: { level_id: string; value: FactorColorValue; label: string; count: number }[];
  range?: { min: number; max: number } | null;
}

const missingColor = '#6b7280';
const categoryPalette = ['#0f766e', '#7c3aed', '#d97706', '#0284c7', '#db2777', '#65a30d', '#b91c1c', '#4f46e5', '#a16207', '#0e7490', '#9333ea', '#15803d'];
const continuousLow = [37, 99, 235] as const;
const continuousHigh = [15, 118, 110] as const;
const typedKey = (value: FactorColorValue) => `${typeof value}:${JSON.stringify(value)}`;
const colorHex = (rgb: readonly number[]) => `#${rgb.map(channel => Math.round(channel).toString(16).padStart(2, '0')).join('')}`;

function continuousColor(value: number, min: number, max: number): string {
  const position = min === max ? 0.5 : Math.max(0, Math.min(1, (value - min) / (max - min)));
  return colorHex(continuousLow.map((channel, index) => channel + (continuousHigh[index]! - channel) * position));
}

function uniqueKeys(keys: string[], label: string): void {
  if (keys.some(key => typeof key !== 'string') || new Set(keys).size !== keys.length) throw new Error(`FACTOR_COLOR_${label}_KEYS_INVALID`);
}

/** Builds a display-only point coloring from an owner-aligned factor vector and owner summaries. */
export function colorFactorPoints<T extends { id: string; x: number; y: number; group?: string }>(
  points: T[], field: FactorColorField, locale: 'en' | 'fr',
): { points: T[]; groupColors: Record<string, string>; legend: FactorColorLegendDescriptor } {
  if (points.length !== field.row_keys.length || field.values.length !== field.row_keys.length) throw new Error('FACTOR_COLOR_POPULATION_LENGTH_MISMATCH');
  const pointKeys = points.map(point => point.id);
  uniqueKeys(pointKeys, 'POINT');
  uniqueKeys(field.row_keys, 'FACTOR');
  const valuesByKey = new Map(field.row_keys.map((key, index) => [key, field.values[index]!]));
  if (pointKeys.some(key => !valuesByKey.has(key))) throw new Error('FACTOR_COLOR_POPULATION_KEYS_MISMATCH');
  const aligned = pointKeys.map(key => valuesByKey.get(key)!);
  const missingCount = aligned.filter(value => value === null).length;
  const missingLabel = locale === 'fr' ? 'Manquant' : 'Missing';
  const groupColors: Record<string, string> = {};
  let levels: FactorColorLevel[] = [];
  let domain: FactorColorLegendDescriptor['domain'] = null;
  const tokens = new Map<string, string>();

  if (field.kind === 'categorical') {
    if (!field.levels) throw new Error('FACTOR_COLOR_LEVEL_SUMMARY_REQUIRED');
    const keys = new Set<string>();
    const ids = new Set<string>();
    levels = field.levels.map((level, index) => {
      const key = typedKey(level.value);
      if (keys.has(key) || ids.has(level.level_id)) throw new Error('FACTOR_COLOR_LEVELS_INVALID');
      keys.add(key); ids.add(level.level_id);
      const color = categoryPalette[index] ?? `hsl(${Math.round((index * 137.508) % 360)} 62% 42%)`;
      const token = `factor-level-${index}`;
      tokens.set(key, token); groupColors[token] = color;
      return { ...level, color };
    });
    aligned.forEach(value => {
      if (value !== null && !tokens.has(typedKey(value))) throw new Error('FACTOR_COLOR_VALUE_NOT_IN_OWNER_LEVELS');
    });
  } else {
    const range = field.range;
    if (!range || !Number.isFinite(range.min) || !Number.isFinite(range.max) || range.min > range.max) throw new Error('FACTOR_COLOR_OWNER_RANGE_REQUIRED');
    domain = { min: range.min, max: range.max };
    const bins = 11;
    for (let index = 0; index < bins; index++) groupColors[`factor-bin-${index}`] = continuousColor(index / (bins - 1), 0, 1);
    aligned.forEach(value => {
      if (value !== null && (typeof value !== 'number' || !Number.isFinite(value) || value < range.min || value > range.max))
        throw new Error('FACTOR_COLOR_VALUE_OUTSIDE_OWNER_RANGE');
    });
  }

  const missingToken = 'factor-missing';
  groupColors[missingToken] = missingColor;
  const coloredPoints = points.map((point, index) => {
    const value = aligned[index]!;
    let token: string;
    if (value === null) token = missingToken;
    else if (field.kind === 'categorical') token = tokens.get(typedKey(value))!;
    else {
      const range = domain!;
      const normalized = range.min === range.max ? 0.5 : (value as number - range.min) / (range.max - range.min);
      token = `factor-bin-${Math.round(normalized * 10)}`;
    }
    return { ...point, group: token };
  });
  return {
    points: coloredPoints,
    groupColors,
    legend: {
      protocol_version: 'domains.factor_colors.v1', factor_id: field.id, kind: field.kind,
      unit: field.unit, origin: field.origin, missing_color: missingColor, missing_label: missingLabel,
      missing_count: missingCount, domain, levels,
    },
  };
}
