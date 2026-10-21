import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { evidenceLabel, human, inScope, loadWorkspace, parsePilot, metricNames, dimensionNames } from '../src/contracts';

const workspace = () => JSON.parse(readFileSync(new URL('../public/workspace.json', import.meta.url), 'utf8'));
export function completedReport() {
  const arm = () => ({ campaign: 'COMPLETED-EXPORT-TEST', ...Object.fromEntries(metricNames.map(n => [n, null])),
    decisive_falsification: {}, graph_suggestions_false_or_trivial: [0, 0], budget_violations: [] });
  return {
    schema: 'WORKSPACE_COMPLETED_PILOT_V1', lifecycle: 'COMPLETED_UNSEALED',
    authorisation: { path: 'docs/strategy/owner_completed_report.md', sha256: 'a'.repeat(64) },
    source_report_sha256: 'b'.repeat(64),
    report: { banner: 'DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY',
      scope: 'PILOT_PAIRED_REPORT', classification: 'INCONCLUSIVE', notes: ['Software contract test only.'],
      packets: [{ packet: 'CONTRACT-TEST', method: 'SYNTHETIC_TEST_ONLY', S: arm(), G: arm(),
        directions: Object.fromEntries(dimensionNames.map(n => [n, 'NOT_COMPARABLE'])) }] },
  };
}

test('real export loads, maintains claim versions, and keeps unknown information', () => {
  const w = loadWorkspace(workspace());
  assert.equal(w.investigations.length, 7);
  assert.equal(w.investigations.find(i => i.family === 'EF06')?.claims.length, 2);
  assert.deepEqual(w.campaigns, []);
  assert.equal(w.pilot, null);
});
test('scope filters exclude historical assertions from live and synthetic scopes', () => {
  const w = loadWorkspace(workspace());
  for (const n of Object.values(w.nodes)) {
    assert.equal(inScope(n, 'live'), false);
    assert.equal(inScope(n, 'synthetic'), false);
  }
});
test('evidence statuses distinguish historical findings, neutral identities and suggestions', () => {
  assert.equal(evidenceLabel({ kind: 'history_finding', status: 'HISTORICAL_CONCLUSION' }), 'Historical conclusion');
  assert.equal(evidenceLabel({ kind: 'entity', status: null }), 'Neutral joining point');
  assert.equal(evidenceLabel({ kind: 'relationship', status: 'SUGGESTION_ONLY' }), 'Suggestion only');
  assert.equal(human(true), 'Yes');
  assert.equal(human(false), 'No');
  assert.equal(human(null), 'Not recorded');
});
test('mixed scope and dangling edges fail instead of appearing as live research', () => {
  const w = workspace(); Object.values(w.nodes as Record<string, any>)[0].fixture = 'LIVE';
  assert.throws(() => loadWorkspace(w), /mixed-scope/);
  const broken = workspace(); broken.edges[0].src = 'unknown';
  assert.throws(() => loadWorkspace(broken), /Dangling/);
});
test('completed report format preserves unknown values and requires unsealed lifecycle', () => {
  const report = completedReport();
  assert.equal(parsePilot(JSON.stringify(report)).report.packets[0].S.analyst_minutes_all, null);
  assert.throws(() => parsePilot(JSON.stringify({ ...report, lifecycle: 'ACTIVE' })));
  assert.throws(() => parsePilot(JSON.stringify(report.report)));
});
test('native report decisive-check unknowns and structured budget violations are preserved', () => {
  const report: any = completedReport();
  report.report.packets[0].G.decisive_falsification = { 'CLAIM-A': 'UNKNOWN', 'CLAIM-B': 'NOT_NAMED' };
  report.report.packets[0].G.budget_violations = [
    { effort: 'EFF-1', code: 'UNCATEGORISED_EFFORT' },
    { code: 'OVER_CAMPAIGN_CEILING', field: 'source_starts', used: 7, ceiling: 6 },
  ];
  const accepted = parsePilot(JSON.stringify(report));
  assert.equal(accepted.report.packets[0].G.decisive_falsification['CLAIM-A'], 'UNKNOWN');
  assert.equal(accepted.report.packets[0].G.budget_violations[1].used, 7);
});
test('report imports reject keys, arm ledgers, HTML paths, invalid numbers and unknown fields', () => {
  const mutate = (fn: (x: any) => void) => { const r = completedReport(); fn(r); assert.throws(() => parsePilot(JSON.stringify(r))); };
  mutate(r => { r.blind_key = 'concealed'; });
  mutate(r => { r.authorisation.path = '../../.env'; });
  mutate(r => { r.authorisation.path = '<script>alert(1)</script>'; });
  mutate(r => { r.report.packets[0].S.analyst_minutes_all = -1; });
  mutate(r => { r.report.packets[0].G.ledger = []; });
  mutate(r => { r.report.packets.push(r.report.packets[0]); });
  mutate(r => { r.report.classification = 'WINNING_STRATEGY'; });
  assert.throws(() => parsePilot(' '.repeat(1_000_001)), /smaller/);
});
