import { describe, expect, it } from 'vitest';
import { HtmlRenderer, Parser, type Node } from 'commonmark';
import { reportModel, savedView } from './model';
import { serializeReport } from './export';
import source from '../../public/examples/tablet.unknown.saved.json';

const adversaries = [
  '~~~', '```', '~'.repeat(64), '> note', '    indented code',
  '\r~~~\r# hidden', '\r\n> quote\r\n~~~', '\t```\n\t> quote',
  '---\n# injected\n1. ordered\n- unordered',
  '[remote]: https://external.invalid/beacon\n![image][remote]',
  '![image](https://external.invalid/image) and [link](https://external.invalid/link)',
  '<https://external.invalid/autolink> <img src="https://external.invalid/image">',
  '&gt; entity &#126;&#126;&#126; `code` *emphasis* _word_ \\',
];

function nodes(root: Node): Node[] {
  const result: Node[] = [], walker = root.walker();
  for (let event = walker.next(); event; event = walker.next()) {
    if (event.entering) result.push(event.node);
  }
  return result;
}

describe('CommonMark rendering of untrusted report prose', () => {
  it.each(adversaries)('keeps following sections and exact JSON evidence for %j', payload => {
    const view = savedView(source);
    view.dataset.name = payload; view.dataset.identity = payload; view.summary = payload;
    Object.assign(view.findings[0], { title: payload, observation: payload,
      hypothesis: payload, relevance: payload, verification: payload, limitation: payload });
    view.limitations = [payload];
    const report = reportModel(view, source, 'unknown', 'en');
    const before = JSON.stringify(report), original = JSON.stringify(source);
    const json = serializeReport(report, 'json');
    const markdown = serializeReport(report, 'markdown');
    const tree = new Parser().parse(markdown), all = nodes(tree);
    const headings = all.filter(n => n.type === 'heading' && n.level === 2)
      .map(n => nodes(n).filter(c => c.type === 'text').map(c => c.literal).join(''));
    expect(headings).toEqual(['Understand the data', 'Observations and conditional checks',
      'Scientific limitations', 'Original evidence and methods']);
    expect(all.filter(n => ['link', 'image', 'block_quote', 'html_block', 'html_inline', 'thematic_break', 'code'].includes(n.type))).toEqual([]);
    const blocks = all.filter(n => n.type === 'code_block');
    expect(blocks).toHaveLength(1);
    expect(blocks[0].info).toBe('json');
    expect(blocks[0].literal).toBe(json);
    expect(JSON.parse(blocks[0].literal!)).toEqual(report);
    // Use the unsanitized renderer: its safety mode must not hide serializer bugs.
    const html = new HtmlRenderer({ safe: false }).render(tree);
    expect(html).not.toMatch(/<(?:a|img|blockquote|script|iframe)(?:\s|>)/i);
    expect(html).toContain('<h2>Scientific limitations</h2>');
    expect(html).toContain('<h2>Original evidence and methods</h2>');
    expect(JSON.stringify(report)).toBe(before);
    expect(JSON.stringify(source)).toBe(original);
    expect(report.scientific_report).toBe(source);
  });

  it('keeps all ASCII punctuation literal in prose and leaves JSON/HTML behavior unchanged', () => {
    const punctuation = Array.from({length: 94}, (_, i) => String.fromCharCode(i + 33))
      .filter(c => !/[A-Za-z0-9]/.test(c)).join('');
    const view = savedView(source); view.dataset.name = punctuation;
    const report = reportModel(view, source, 'unknown', 'en');
    const jsonBefore = serializeReport(report, 'json'), htmlBefore = serializeReport(report, 'html');
    const all = nodes(new Parser().parse(serializeReport(report, 'markdown')));
    const paragraph = all.find(n => n.type === 'paragraph')!;
    const text = nodes(paragraph).filter(n => n.type === 'text').map(n => n.literal).join('');
    expect(text).toContain(punctuation);
    expect(serializeReport(report, 'json')).toBe(jsonBefore);
    expect(serializeReport(report, 'html')).toBe(htmlBefore);
    expect(JSON.parse(jsonBefore)).toEqual(report);
    expect(htmlBefore).toContain("default-src 'none'");
  });
});
