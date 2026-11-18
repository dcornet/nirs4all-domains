// Small synthetic CSV submissions for the one-shot import boundary.
// These exercise published IO/UI behavior only; no model or numeric kernel runs.
const x = 'id,2000,1000\na,1,2\nb,3,4\nc,5,6';
const csv = (name, text) => ({ name, text });
const configured = (sources, sample_index) => csv('submission.nirs4all.json', JSON.stringify({
  schema_version: 1,
  ...(sample_index ? { sample_index } : {}),
  sources,
}));

export const oneShotFixtureCases = Object.freeze([
  { id: 'x-only', expected: 'loaded', files: [csv('train_x.csv', x)] },
  { id: 'x-y', expected: 'loaded', files: [csv('train_x.csv', x), csv('train_y.csv', 'id,yield\nc,30\na,10\nb,20')] },
  { id: 'x-m', expected: 'loaded', files: [csv('train_x.csv', x), csv('train_m.csv', 'id,batch\nb,B\nc,C\na,A')] },
  { id: 'x-y-m', expected: 'loaded', files: [csv('train_x.csv', x), csv('train_y.csv', 'id,yield\nc,30\na,10\nb,20'), csv('train_m.csv', 'id,batch\nb,B\nc,C\na,A')] },
  { id: 'keyed-train-test', expected: 'loaded', files: [
    csv('train_x.csv', x), csv('train_y.csv', 'id,yield\nc,30\na,10\nb,20'),
    csv('test_x.csv', 'id,2000,1000\nd,7,8\ne,9,10'), csv('test_y.csv', 'id,yield\ne,50\nd,40'),
  ] },
  { id: 'mixed-y-numeric-categorical', expected: 'loaded', files: [
    csv('train_x.csv', x), csv('train_y.csv', 'id,yield,class\na,10,A\nb,20,B\nc,30,C'),
  ] },
  { id: 'missing-y-cell', expected: 'loaded', files: [
    csv('train_x.csv', x), csv('train_y.csv', 'id,yield\na,10\nb,\nc,30'),
  ] },
  { id: 'all-missing-y', expected: 'loaded', files: [
    csv('train_x.csv', 'id,2000,1000\na,1,2\nb,3,4'), csv('train_y.csv', 'id,yield\na,\nb,'),
  ] },
  { id: 'missing-m-cell', expected: 'loaded', files: [
    csv('train_x.csv', x), csv('train_m.csv', 'id,batch\na,A\nb,\nc,C'),
  ] },
  { id: 'partial-m-inferred-allow-missing', expected: 'loaded', files: [
    csv('train_x.csv', x), csv('train_m.csv', 'id,batch\na,A\nc,C'),
  ] },
  { id: 'all-missing-m', expected: 'loaded', files: [
    csv('train_x.csv', x), csv('train_m.csv', 'id,batch\na,\nb,\nc,'),
  ] },
  { id: 'na-empty', expected: 'loaded', na: '', files: [
    csv('train_x.csv', 'id,2000,1000\na,1,2\nb,,4\nc,5,6'),
    csv('train_y.csv', 'id,yield\na,10\nb,\nc,30'), csv('train_m.csv', 'id,batch\na,A\nb,\nc,C'),
  ] },
  ...['NA', 'N/A', 'NaN', 'null', 'None', '.', 'missing'].map(token => ({
    id: `na-${token.replaceAll('/', '-')}`, expected: 'loaded', na: token,
    files: [csv('train_x.csv', `id,2000,1000\na,1,2\nb,${token},4\nc,5,6`),
      csv('train_y.csv', `id,yield\na,10\nb,${token}\nc,30`),
      csv('train_m.csv', `id,batch\na,A\nb,${token}\nc,C`)],
  })),
  { id: 'duplicate-m-keys', expected: 'needs_input', files: [
    csv('train_x.csv', x), csv('train_m.csv', 'id,batch\na,A\na,B\nc,C'),
  ] },
  { id: 'ambiguous-row-order-pairing', expected: 'needs_input', files: [
    csv('train_x.csv', 'id,2000,1000\na,1,2\nb,3,4'),
    csv('train_y.csv', 'id,yield\na,10\na,20'),
    configured([
      { id: 'X', input: 'train_x.csv', role: 'features', key: 'id', partition: 'train', params: { delimiter: ',', has_header: true } },
      { id: 'Y', input: 'train_y.csv', role: 'targets', partition: 'train', params: { delimiter: ',', has_header: true } },
    ]),
  ] },
  // Keep the inference-only duplicate-key case as a separate regression.
  // Its failed whole-dataset preview must not relabel the last X band as Y.
  { id: 'inferred-duplicate-y-keys-preserve-x-axis', expected: 'needs_input', files: [
    csv('train_x.csv', 'id,2000,1000\na,1,2\nb,3,4'),
    csv('train_y.csv', 'id,yield\na,10\na,20'),
  ] },
  { id: 'two-x-same-axis', expected: 'needs_input', files: [
    csv('train_x.csv', x), csv('other_x.csv', 'id,2000,1000\na,6,7\nb,8,9\nc,10,11'),
    configured([
      { id: 'X1', input: 'train_x.csv', role: 'features', key: 'id', partition: 'train', params: { delimiter: ',', has_header: true } },
      { id: 'X2', input: 'other_x.csv', role: 'features', key: 'id', partition: 'train', params: { delimiter: ',', has_header: true } },
    ]),
  ] },
  { id: 'two-x-different-axis', expected: 'needs_input', files: [
    csv('train_x.csv', x), csv('other_x.csv', 'id,2100,1100\na,6,7\nb,8,9\nc,10,11'),
    configured([
      { id: 'X1', input: 'train_x.csv', role: 'features', key: 'id', partition: 'train', params: { delimiter: ',', has_header: true } },
      { id: 'X2', input: 'other_x.csv', role: 'features', key: 'id', partition: 'train', params: { delimiter: ',', has_header: true } },
    ]),
  ] },
  { id: 'unassociated-y-no-key', expected: 'loaded', files: [
    csv('train_x.csv', '2000,1000\n1,2\n3,4'), csv('train_y.csv', 'yield\n10\n20'),
  ] },
  { id: 'unassociated-m-no-key', expected: 'loaded', files: [
    csv('train_x.csv', x), csv('train_m.csv', 'campaign\nwest\neast\nwest'),
  ] },
  { id: 'explicit-delimiter-correction', expected: 'needs_input', files: [
    csv('train_x.csv', 'id;2000;1000\na;1;2\nb;3;4\nc;5;6'),
    configured([{ id: 'X', input: 'train_x.csv', role: 'features', key: 'id', partition: 'train', params: { delimiter: ',', has_header: true } }]),
  ] },
]);

export function filesForOneShotCase(id) {
  const scenario = oneShotFixtureCases.find(item => item.id === id);
  if (!scenario) throw new Error(`UNKNOWN_ONE_SHOT_FIXTURE:${id}`);
  return scenario.files.map(file => ({ name: file.name, bytes: new TextEncoder().encode(file.text) }));
}
