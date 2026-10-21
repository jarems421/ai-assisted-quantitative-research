export type Citation = { path: string; quote: string };
export type Operator = { operator: string; results: any[]; abstentions: { code: string; reason: string }[]; notes: string[]; [key: string]: any };
export type GraphNode = {
  id: string; kind: string; label: string; status: string | null; fixture: string | null;
  origin: { type: string; investigation?: string; report?: string }; attrs: Record<string, any>;
  restrictions: string[]; reasons: string[]; superseded: boolean; search_text: string;
};
export type Edge = { src: string; dst: string; kind: string; attrs: Record<string, any> };
export type Finding = { id: string; kind: string; text: string; citation: Citation; requirement: string | null; claim: string | null };
export type Claim = {
  id: string; version: number; object: string; financial_basis: string; reformulates: string | null;
  post_outcome: string | boolean; counts_as_original: boolean; recorded_status: { text: string; citation: Citation }[];
};
export type Investigation = {
  id: string; node: string; family: string; title: string; report: string; citation_status: string;
  historical_closure: { date: string; note: string };
  verdict: { text: string; status_class: string; scope: string; citation: Citation; scope_citation: Citation };
  claims: Claim[]; findings: Finding[]; entities: { id: string; type: string; name: string; identity_basis: string; citation?: Citation; name_citation?: Citation }[];
  documents: { locator: string; sha256: string; receipt: string; role: string; complete: boolean; http_status: number; body_bytes: number }[];
  trace: Operator; gaps: Operator; shared: Operator; related: string[];
};
export type Workspace = {
  schema: string; banner: string; scope: string;
  catalogue: { version: string; recorded_at_utc: string; path: string; sha256: string; mapping_review: string };
  graph_digest: string; nodes: Record<string, GraphNode>; edges: Edge[];
  investigations: Investigation[]; requirements: { id: string; label: string; definition: string; does_not_mean: string[] }[];
  neighbourhoods: Record<string, Record<string, Operator>>; explanations: Record<string, Operator>;
  same_gap: Record<string, Operator>; operators: Record<string, Operator>;
  documents: Record<string, { path: string; sha256: string; text: string; expected_sha256?: string; status: string }>;
  issues: any[]; experiments: { id: string; path: string }[]; campaigns: []; pilot: null;
  software_validation: { status: string; graph_tests: number; recorded_at_utc: string; path: string };
  input_hashes: Record<string, string>; limits: string[];
};

export const human = (value: unknown): string => value === null || value === undefined || value === '' ? 'Not recorded' :
  typeof value === 'boolean' ? value ? 'Yes' : 'No' : String(value).toLowerCase().replaceAll('_', ' ').replace(/^./, s => s.toUpperCase());
export const kindLabel = (kind: string) => ({ history: 'Investigation', history_claim: 'Historical claim', history_finding: 'Recorded finding', relationship: 'Relationship assertion' }[kind] ?? human(kind));
export const evidenceLabel = (node: Pick<GraphNode, 'kind' | 'status'>) => node.status ? human(node.status) : ['entity', 'document'].includes(node.kind) ? 'Neutral joining point' : 'Retrieval aid';
export const scopes = ['historical', 'live', 'synthetic'] as const;
export type Scope = typeof scopes[number];
export function inScope(node: GraphNode, scope: Scope) {
  if (scope === 'live') return node.fixture === 'LIVE';
  if (scope === 'synthetic') return node.fixture === 'SYNTHETIC';
  return node.fixture === 'HISTORICAL_MEMORY' || node.fixture === 'RETROSPECTIVE_INSPECTED' ||
    (!node.fixture && node.origin.type === 'DERIVED');
}

export function loadWorkspace(value: unknown): Workspace {
  if (!value || typeof value !== 'object') throw new Error('Workspace export is not an object.');
  const d = value as Workspace;
  if (d.schema !== 'RESEARCH_WORKSPACE_V1' || d.scope !== 'HISTORICAL_MEMORY_ONLY' ||
      d.banner !== 'DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY' ||
      !Array.isArray(d.investigations) || !d.nodes || !Array.isArray(d.edges) ||
      !d.documents || !d.neighbourhoods || !d.explanations || !d.same_gap || !d.catalogue ||
      !Array.isArray(d.campaigns) || d.campaigns.length !== 0 || d.pilot !== null) {
    throw new Error('Unsupported workspace export. Regenerate it with the local adapter.');
  }
  for (const [id, n] of Object.entries(d.nodes)) {
    if (n.id !== id || typeof n.label !== 'string' || typeof n.search_text !== 'string' ||
        !inScope(n, 'historical') || !Array.isArray(n.restrictions)) throw new Error('Invalid or mixed-scope graph record.');
  }
  for (const e of d.edges) if (!d.nodes[e.src] || !d.nodes[e.dst]) throw new Error('Dangling graph connection.');
  for (const i of d.investigations) {
    if (!d.nodes[i.node] || !Array.isArray(i.claims) || !Array.isArray(i.findings) || !d.documents[i.report]) throw new Error('Incomplete investigation.');
    for (const f of i.findings) if (!d.documents[f.citation.path]) throw new Error('Finding has no included source.');
  }
  return d;
}

export type PilotExport = {
  schema: 'WORKSPACE_COMPLETED_PILOT_V1'; lifecycle: 'COMPLETED_UNSEALED';
  authorisation: { path: string; sha256: string }; source_report_sha256: string;
  report: { banner: string; scope: string; classification: string; notes: string[]; packets: any[] };
};
const hash = (x: unknown) => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
const record = (v: unknown): v is Record<string, any> => !!v && typeof v === 'object' && !Array.isArray(v);
const exact = (v: Record<string, any>, keys: string[]) => Object.keys(v).length === keys.length && keys.every(k => Object.hasOwn(v, k));
const texts = (v: unknown) => Array.isArray(v) && v.length <= 500 && v.every(x => typeof x === 'string' && x.length <= 20000);
function violations(value: unknown): boolean {
  if (!Array.isArray(value) || value.length > 500) return false;
  return value.every(v => {
    if (!record(v)) return false;
    if (['UNCATEGORISED_EFFORT', 'GRAPH_TIME_IN_STRUCTURED_ARM', 'SEARCH_NOT_CATEGORISED_SOURCE_SEARCH'].includes(v.code)) {
      return exact(v, ['effort', 'code']) && typeof v.effort === 'string' && v.effort.length <= 150;
    }
    return v.code === 'OVER_CAMPAIGN_CEILING' && exact(v, ['code', 'field', 'used', 'ceiling']) &&
      ['analyst_minutes', 'source_starts', 'searches', 'bytes'].includes(v.field) &&
      [v.used, v.ceiling].every(n => typeof n === 'number' && Number.isFinite(n) && n >= 0);
  });
}
export function violationText(v: Record<string, any>): string {
  return `${human(v.code)}${v.effort ? ` · ${v.effort}` : ''}${v.field ? ` · ${human(v.field)}: ${v.used} / ${v.ceiling}` : ''}`;
}
export const metricNames = [
  'analyst_minutes_all', 'graph_minutes', 'verified_connections', 'verified_connections_per_hour',
  'graph_only_verified', 'false_or_premature_joins_made', 'false_joins_declined', 'true_connections_declined',
  'median_minutes_per_connection', 'median_minutes_to_decisive_falsification', 'duplicate_research_avoided',
  'review_burden_items', 'adjudicator_minutes', 'suggestion_review_minutes', 'original_frozen_m_passes',
  'original_frozen_m_passes_per_hour', 'h_plausible_human',
] as const;
export const dimensionNames = [
  'verified_connections_per_hour', 'false_or_premature_joins_made', 'median_minutes_per_connection',
  'median_minutes_to_decisive_falsification', 'duplicate_research_avoided', 'original_frozen_m_passes_per_hour',
  'review_burden_items', 'adjudicator_minutes',
];
export function parsePilot(text: string): PilotExport {
  if (new TextEncoder().encode(text).length > 1_000_000) throw new Error('Please choose an export smaller than 1 MB.');
  const e: unknown = JSON.parse(text);
  const fail = () => { throw new Error('This is not a completed, unsealed pilot-report export. See the local README for the exact format.'); };
  if (!record(e) || !exact(e, ['schema', 'lifecycle', 'authorisation', 'source_report_sha256', 'report']) ||
      e.schema !== 'WORKSPACE_COMPLETED_PILOT_V1' || e.lifecycle !== 'COMPLETED_UNSEALED' ||
      !record(e.authorisation) || !exact(e.authorisation, ['path', 'sha256']) ||
      typeof e.authorisation.path !== 'string' || !/^docs\/strategy\/[a-zA-Z0-9_-]+\.md$/.test(e.authorisation.path) ||
      !hash(e.authorisation.sha256) || !hash(e.source_report_sha256) || !record(e.report)) return fail();
  const r = e.report;
  if (!exact(r, ['banner', 'scope', 'packets', 'classification', 'notes']) ||
      r.banner !== 'DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY' ||
      r.scope !== 'PILOT_PAIRED_REPORT' || !['INVALID_CRITICAL_STOP', 'INCONCLUSIVE', 'GRAPH_INCREMENT_OBSERVED', 'NO_GRAPH_INCREMENT_OBSERVED'].includes(r.classification) ||
      !texts(r.notes) || !Array.isArray(r.packets) || r.packets.length < 1 || r.packets.length > 4) return fail();
  const ids = new Set<string>();
  const numeric = (v: unknown) => v === null || typeof v === 'number' && Number.isFinite(v) && v >= 0;
  for (const p of r.packets) {
    if (!record(p) || !exact(p, ['packet', 'method', 'S', 'G', 'directions']) || typeof p.packet !== 'string' ||
        p.packet.length > 100 || ids.has(p.packet) || typeof p.method !== 'string' || p.method.length > 200 ||
        !record(p.directions) || !exact(p.directions, dimensionNames) ||
        !Object.values(p.directions).every(x => ['S', 'G', 'EQUAL', 'NOT_COMPARABLE'].includes(x))) return fail();
    ids.add(p.packet);
    for (const arm of ['S', 'G']) {
      const m = p[arm];
      if (!record(m) || !exact(m, ['campaign', ...metricNames, 'decisive_falsification', 'graph_suggestions_false_or_trivial', 'budget_violations']) ||
          typeof m.campaign !== 'string' || m.campaign.length > 150 || !metricNames.every(k => numeric(m[k])) ||
          !record(m.decisive_falsification) || !Object.values(m.decisive_falsification).every(x => numeric(x) || x === 'UNKNOWN' || x === 'NOT_NAMED') ||
          !Array.isArray(m.graph_suggestions_false_or_trivial) || m.graph_suggestions_false_or_trivial.length !== 2 ||
          !m.graph_suggestions_false_or_trivial.every((x: unknown) => Number.isSafeInteger(x) && Number(x) >= 0) ||
          !violations(m.budget_violations)) return fail();
    }
  }
  return e as PilotExport;
}
