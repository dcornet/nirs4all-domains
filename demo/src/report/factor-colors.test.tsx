import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { FactorColorLegend } from '../FactorColorLegend';
import { colorFactorPoints, type FactorColorField } from './factor-colors';

const points = [
  { id: 'a', x: 1, y: 2, label: 'kept-a' },
  { id: 'b', x: 3, y: 4, group: 'old' },
  { id: 'c', x: 5, y: 6 },
];

function field(overrides: Partial<FactorColorField> = {}): FactorColorField {
  return { id: 'moisture', kind: 'continuous', unit: '%', origin: 'declared', row_keys: ['c', 'a', 'b'], values: [3, 0, null], range: { min: 0, max: 3 }, ...overrides };
}

describe('factor color projection', () => {
  it('key-aligns values, treats zero as valid, separates missing, and preserves input points', () => {
    const original = structuredClone(points);
    const result = colorFactorPoints(points, field(), 'en');
    expect(result.points.map(point => point.id)).toEqual(['a', 'b', 'c']);
    expect(result.points.map(point => point.group)).toEqual(['factor-bin-0', 'factor-missing', 'factor-bin-10']);
    expect(result.groupColors['factor-bin-0']).not.toBe(result.legend.missing_color);
    expect(result.legend.missing_count).toBe(1);
    expect(result.legend.domain).toEqual({ min: 0, max: 3 });
    expect(result.points.map(point => [point.x, point.y])).toEqual([[1, 2], [3, 4], [5, 6]]);
    expect(points).toEqual(original);
  });

  it('requires an owner range and maps a constant domain to the middle color', () => {
    expect(() => colorFactorPoints(points, field({ range: null }), 'en')).toThrow('FACTOR_COLOR_OWNER_RANGE_REQUIRED');
    const result = colorFactorPoints(points.slice(0, 2), field({ row_keys: ['a', 'b'], values: [0, 0], range: { min: 0, max: 0 } }), 'en');
    expect(result.legend.domain).toEqual({ min: 0, max: 0 });
    expect(result.points[0]?.group).toBe('factor-bin-5');
    expect(result.groupColors['factor-bin-5']).not.toBe(result.legend.missing_color);
  });

  it('distinguishes typed category values and uses owner level labels/counts', () => {
    const categorical: FactorColorField = {
      id: 'code', kind: 'categorical', unit: null, origin: 'declared', row_keys: ['a', 'b', 'c'],
      values: [1, '1', null], levels: [
        { level_id: 'number-one', value: 1, label: 'Number one', count: 7 },
        { level_id: 'string-one', value: '1', label: 'String one', count: 2 },
      ],
    };
    const result = colorFactorPoints(points, categorical, 'en');
    expect(result.points.map(point => point.group)).toEqual(['factor-level-0', 'factor-level-1', 'factor-missing']);
    expect(result.legend.levels.map(level => [level.value, level.count])).toEqual([[1, 7], ['1', 2]]);
    expect(result.groupColors['factor-level-0']).not.toBe(result.groupColors['factor-level-1']);
  });

  it('renders escaped category labels and distinct missing legend in both locales', () => {
    const categorical: FactorColorField = {
      id: 'code', kind: 'categorical', unit: null, origin: 'declared', row_keys: ['a', 'b', 'c'],
      values: ['<batch>', true, null], levels: [
        { level_id: 'batch', value: '<batch>', label: '<script>& batch', count: 2 },
        { level_id: 'yes', value: true, label: 'Yes', count: 1 },
      ],
    };
    const legend = colorFactorPoints(points, categorical, 'fr').legend;
    const html = renderToStaticMarkup(<FactorColorLegend legend={legend} locale="fr" />);
    expect(html).toContain('&lt;script&gt;&amp; batch');
    expect(html).not.toContain('<script>');
    expect(html).toContain('Manquant (1)');
    expect(html).toContain('Affichage uniquement ; ce n’est pas un score de risque.');
  });

  it('rejects population/key mismatches and values outside the owner range', () => {
    expect(() => colorFactorPoints(points, field({ row_keys: ['a', 'b', 'other'] }), 'en')).toThrow('FACTOR_COLOR_POPULATION_KEYS_MISMATCH');
    expect(() => colorFactorPoints(points, field({ values: [4, 0, null] }), 'en')).toThrow('FACTOR_COLOR_VALUE_OUTSIDE_OWNER_RANGE');
  });
});
