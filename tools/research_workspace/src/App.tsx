import { createContext, useContext, useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from 'react';
import {
  type Workspace, type Investigation, type GraphNode, type Citation, type Operator, type PilotExport, type Scope,
  human, kindLabel, evidenceLabel, inScope, loadWorkspace, parsePilot, metricNames, violationText,
} from './contracts';

type Page = 'desk' | 'investigations' | 'connections' | 'memory' | 'pilot' | 'archive';
type Route = { page: Page; id?: string };
type SourceRequest = { path: string; quote?: string };
const pages: { id: Page; title: string; icon: string }[] = [
  { id: 'desk', title: 'Your desk', icon: 'desk' },
  { id: 'investigations', title: 'Investigations', icon: 'book' },
  { id: 'connections', title: 'Connections', icon: 'graph' },
  { id: 'memory', title: 'Research memory', icon: 'memory' },
  { id: 'pilot', title: 'Pilot notebook', icon: 'compare' },
  { id: 'archive', title: 'Experiment archive', icon: 'archive' },
];
const Context = createContext<{ data: Workspace; navigate: (page: Page, id?: string) => void; source: (request: SourceRequest) => void }>(null!);
const useWorkspace = () => useContext(Context);
function tabKeys(event: ReactKeyboardEvent) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  const tabs = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]'));
  const current = tabs.indexOf(document.activeElement as HTMLButtonElement);
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (current + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
  event.preventDefault(); tabs[next]?.focus(); tabs[next]?.click();
}
function routeFromHash(): Route {
  const [page, id] = window.location.hash.slice(1).split('/');
  try { return { page: pages.some(p => p.id === page) ? page as Page : 'desk', id: id ? decodeURIComponent(id) : undefined }; }
  catch { return { page: 'desk' }; }
}

function Icon({ name, size = 19 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    desk: <><path d="M3 10h18M5 10V5h14v5M5 10v10m14-10v10M8 14h8" /></>,
    book: <><path d="M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1Zm0 0v15" /></>,
    graph: <><circle cx="12" cy="12" r="3" /><circle cx="4" cy="5" r="2" /><circle cx="20" cy="5" r="2" /><circle cx="19" cy="20" r="2" /><path d="m6 7 4 3m4 0 4-3m-4 7 4 4" /></>,
    memory: <><path d="M5 5h14v15H5zM8 2v6m8-6v6M8 12h8m-8 4h5" /></>,
    compare: <><path d="M4 5h6v14H4zM14 5h6v14h-6zM7 9v6m10-4v4" /></>,
    archive: <><path d="M3 4h18v5H3zM5 9v11h14V9M9 13h6" /></>,
    search: <><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 4 4" /></>,
    arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
    back: <path d="M19 12H5m5-5-5 5 5 5" />,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1" /></>,
    moon: <path d="M20 14a8 8 0 0 1-10-10 8.5 8.5 0 1 0 10 10Z" />,
    source: <><path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8m-8 4h6" /></>,
    leaf: <><path d="M5 20C3 7 12 4 21 3c0 11-5 17-12 13M5 20 16 9" /></>,
    upload: <><path d="M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6m0-10v1" /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] ?? paths.source}</svg>;
}

function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) { return <span className={`badge ${tone}`}>{children}</span>; }
function Empty({ title, children, icon = 'leaf' }: { title: string; children: ReactNode; icon?: string }) {
  return <div className="empty"><span className="empty-icon"><Icon name={icon} size={25} /></span><h3>{title}</h3><p>{children}</p></div>;
}
function SourceLink({ citation, label = 'Read source' }: { citation: Citation; label?: string }) {
  const { source } = useWorkspace();
  return <button className="source-link" onClick={() => source(citation)}><Icon name="source" size={14} />{label}</button>;
}
function CitationBlock({ citation }: { citation: Citation }) {
  return <blockquote className="citation"><p>{citation.quote}</p><SourceLink citation={citation} label={citation.path.split('/').at(-1)!.replaceAll('_', ' ')} /></blockquote>;
}
function PageHeader({ eyebrow, title, children, action }: { eyebrow: string; title: string; children?: ReactNode; action?: ReactNode }) {
  return <header className="page-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1>{children && <p>{children}</p>}</div>{action}</header>;
}
function SectionTitle({ title, children }: { title: string; children?: ReactNode }) {
  return <div className="section-title"><h2>{title}</h2>{children}</div>;
}
function ScopeSelect({ scope, onChange }: { scope: Scope; onChange: (value: Scope) => void }) {
  return <label className="select-label">Records<select aria-label="Records" value={scope} onChange={e => onChange(e.target.value as Scope)}><option value="historical">Historical memory</option><option value="live">Live campaigns</option><option value="synthetic">Synthetic records</option></select></label>;
}
function ScopeEmpty({ scope }: { scope: Scope }) {
  return <Empty title={scope === 'live' ? 'No live campaigns in this snapshot' : 'No synthetic records included'}>
    {scope === 'live' ? 'This workspace deliberately leaves campaign ledgers and active pilot arms unopened. Explore the historical notebook while those records stay separate.' : 'Software rehearsals are kept separate from scientific evidence. This export contains historical memory only.'}
  </Empty>;
}

export function App() {
  const [data, setData] = useState<Workspace | null>(null);
  const [error, setError] = useState('');
  const [route, setRoute] = useState(routeFromHash);
  const [source, setSource] = useState<SourceRequest | null>(null);
  const [search, setSearch] = useState<string | null>(null);
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('research-workspace-theme') ?? 'light'; } catch { return 'light'; }
  });
  const [pilot, setPilot] = useState<PilotExport | null>(null);
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/workspace.json', { signal: controller.signal }).then(r => { if (!r.ok) throw new Error('The local export is missing. Run npm run export, then reload.'); return r.json(); })
      .then(loadWorkspace).then(setData).catch(e => { if (e.name !== 'AbortError') setError(e.message); });
    return () => controller.abort();
  }, []);
  useEffect(() => { const listener = () => setRoute(routeFromHash()); addEventListener('hashchange', listener); return () => removeEventListener('hashchange', listener); }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('research-workspace-theme', theme); } catch { /* Optional local preference. */ }
  }, [theme]);
  useEffect(() => { document.title = `${pages.find(p => p.id === route.page)?.title} · Research OS`; main.current?.focus(); window.scrollTo(0, 0); }, [route]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); setSearch(''); } };
    addEventListener('keydown', key); return () => removeEventListener('keydown', key);
  }, []);
  const navigate = (page: Page, id?: string) => { window.location.hash = page + (id ? '/' + encodeURIComponent(id) : ''); };
  if (error) return <div className="startup"><Icon name="book" size={32} /><h1>A small setup step.</h1><p role="alert">{error}</p><button onClick={() => location.reload()}>Try again</button></div>;
  if (!data) return <div className="startup" role="status"><Icon name="book" size={32} /><p>Opening your research notebook…</p></div>;
  return <Context.Provider value={{ data, navigate, source: setSource }}>
    <a href="#main" className="skip-link" onClick={e => { e.preventDefault(); main.current?.focus(); }}>Skip to content</a>
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#desk"><span className="brand-mark">r<span>.</span></span><span>research os<small>your own little study</small></span></a>
        <button className="search-trigger" aria-label="Find something" title="Find something (Ctrl or Command + K)" onClick={() => setSearch('')}><Icon name="search" size={16} /><span>Find something</span><kbd>⌘ K</kbd></button>
        <div className="nav-caption">YOUR WORKSPACE</div>
        <nav aria-label="Main navigation">{pages.map(p => <a key={p.id} aria-label={p.title} title={p.title} href={`#${p.id}`} className={route.page === p.id ? 'active' : ''} aria-current={route.page === p.id ? 'page' : undefined}><Icon name={p.icon} /><span>{p.title}</span>{p.id === 'investigations' && <small>{data.investigations.length}</small>}</a>)}</nav>
        <div className="sidebar-bottom"><div className="local-note"><span className="local-dot" /><div>Just here, on your computer<small>Offline · read-only research</small></div></div><button className="theme-toggle" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}><Icon name={theme === 'light' ? 'moon' : 'sun'} size={17} />{theme === 'light' ? 'A softer evening view' : 'Back to daylight'}</button></div>
      </aside>
      <div className="main-column">
        <div className="topbar"><div><span className="breadcrumb">Your workspace</span><span className="slash">/</span>{pages.find(p => p.id === route.page)?.title}</div><span className="snapshot-label">Historical snapshot <span>·</span> {new Date(data.catalogue.recorded_at_utc).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Europe/London' })}</span></div>
        <main id="main" tabIndex={-1} ref={main}>
          {route.page === 'desk' && <Desk />}
          {route.page === 'investigations' && <Investigations selected={route.id} />}
          {route.page === 'connections' && <Connections initial={route.id} />}
          {route.page === 'memory' && <Memory />}
          {route.page === 'pilot' && <Pilot pilot={pilot} setPilot={setPilot} />}
          {route.page === 'archive' && <Archive />}
        </main>
        <footer><Icon name="info" size={14} /><span>Derived research view · not independent evidence · no research authority.</span><button className="text-button" onClick={() => setSource({ path: data.software_validation.path })}>About this snapshot</button></footer>
      </div>
    </div>
    {source && <DocumentModal request={source} onClose={() => setSource(null)} />}
    {search !== null && <SearchModal query={search} setQuery={setSearch} onClose={() => setSearch(null)} />}
  </Context.Provider>;
}

function Desk() {
  const { data, navigate, source } = useWorkspace();
  const findings = data.investigations.reduce((s, i) => s + i.findings.length, 0);
  const recurring = [...data.requirements].sort((a, b) => data.same_gap[b.id].results.length - data.same_gap[a.id].results.length);
  const f19 = data.investigations.find(i => i.family === 'F19')!;
  return <>
    <section className="welcome"><span className="eyebrow"><span className="tiny-sun">☼</span> A LITTLE ROOM TO THINK</span><h1>Your research.<br /><em>A little more clear.</em></h1><p>A quiet place to follow the evidence, find the missing pieces,<br className="desktop-break" /> and remember what you’ve already learned.</p></section>
    <div className="desk-counts" aria-label="Snapshot contents"><div><strong>{data.investigations.length}</strong><span>historical investigations</span></div><div><strong>{findings}</strong><span>recorded findings</span></div><div><strong>{data.requirements.length}</strong><span>measurement needs</span></div><span className="count-note">From your existing research.<br />Nothing new has been inferred.</span></div>
    <div className="desk-grid">
      <section><SectionTitle title="On your reading desk"><button className="text-button" onClick={() => navigate('investigations')}>View all <Icon name="arrow" size={15} /></button></SectionTitle>
        <article className="reading-note"><div className="note-top"><span className="eyebrow">{f19.family} · HISTORICAL INVESTIGATION</span><Badge tone="amber">On hold</Badge></div><h2>{f19.title}</h2><p>{f19.findings.find(f => f.kind === 'MEASUREMENT_GAP')?.text}</p><div className="note-bottom"><button className="button primary" onClick={() => navigate('investigations', f19.id)}>Open the notebook <Icon name="arrow" size={16} /></button><span>Existing hold remains in place</span></div></article>
        <div className="quiet-info"><Icon name="leaf" size={19} /><p><strong>Room for the unknown.</strong> A stopped investigation can still be useful. The notebook keeps what was learned, what wasn’t established, and the evidence that could change the assessment.</p></div>
      </section>
      <section><SectionTitle title="The missing pieces"><span className="small-label">Shared measurement needs</span></SectionTitle><div className="gap-list">{recurring.slice(0, 3).map(r => <button key={r.id} onClick={() => navigate('memory', r.id)}><span className="gap-number">{String(data.same_gap[r.id].results.length).padStart(2, '0')}</span><span><strong>{r.label}</strong><small>historical claims with this recorded need</small></span><Icon name="arrow" size={16} /></button>)}</div><p className="caption">Shared gaps help you reuse knowledge. They do not establish an economic connection.</p></section>
    </div>
    <section className="notebook-section"><SectionTitle title="A few pages from your notebook"><span className="small-label">Historical memory · no live activity</span></SectionTitle><div className="notebook-list">{data.investigations.filter(i => i.family !== 'F19').slice(0, 4).map(i => <InvestigationRow key={i.id} investigation={i} />)}</div></section>
    <div className="desk-bottom"><div><span className="local-dot" /><p><strong>No live campaigns in this export.</strong><span>Active pilot records stay separate from this reading workspace.</span></p></div><button className="text-button" onClick={() => navigate('pilot')}>Visit the pilot notebook <Icon name="arrow" size={16} /></button></div>
    <details className="snapshot-details"><summary>What is included in this snapshot?</summary><p>Catalogue V002, recorded {data.catalogue.recorded_at_utc}. {Object.keys(data.nodes).length} graph nodes and {data.edges.length} structural connections. Original observations: 0. Documented economic relationship assertions: 0.</p><ul>{data.limits.map(l => <li key={l}>{l}</li>)}</ul><p>Graph digest <code>{data.graph_digest}</code></p><p>The recorded graph review reports {data.software_validation.graph_tests} software tests passing. This is a software check, not a scientific result.</p><button className="source-link" onClick={() => source({ path: data.software_validation.path })}>Read the recorded validation</button></details>
  </>;
}

function InvestigationRow({ investigation: i }: { investigation: Investigation }) {
  const { navigate } = useWorkspace();
  return <button className="investigation-row" onClick={() => navigate('investigations', i.id)}><span className="family-label">{i.family}</span><span className="row-body"><strong>{i.title}</strong><small>{i.verdict.scope}</small></span><Badge tone={i.verdict.status_class === 'HOLD' ? 'amber' : 'neutral'}>{human(i.verdict.status_class)}</Badge><Icon name="arrow" size={16} /></button>;
}

function Investigations({ selected }: { selected?: string }) {
  const { data } = useWorkspace();
  const [query, setQuery] = useState(''); const [status, setStatus] = useState('all'); const [scope, setScope] = useState<Scope>('historical');
  const investigation = data.investigations.find(i => i.id === selected);
  if (selected && !investigation) return <Empty title="That notebook isn’t in this snapshot">Choose an investigation from the navigation to return to the historical records.</Empty>;
  if (investigation) return <InvestigationNotebook key={investigation.id} investigation={investigation} />;
  const filtered = data.investigations.filter(i => (status === 'all' || i.verdict.status_class === status) && `${i.family} ${i.title} ${i.claims.map(c => c.object).join(' ')} ${i.findings.map(f => f.text).join(' ')}`.toLowerCase().includes(query.toLowerCase()));
  return <><PageHeader eyebrow="YOUR RESEARCH NOTEBOOK" title="Follow a question.">The idea, the evidence, and the point where certainty runs out.</PageHeader><div className="toolbar"><label className="search-field"><Icon name="search" size={17} /><input aria-label="Search investigations" placeholder="Search an idea, family, or missing measurement…" value={query} onChange={e => setQuery(e.target.value)} /></label><label className="select-label">Disposition<select value={status} onChange={e => setStatus(e.target.value)}><option value="all">All recorded states</option>{[...new Set(data.investigations.map(i => i.verdict.status_class))].map(s => <option key={s}>{s}</option>)}</select></label><ScopeSelect scope={scope} onChange={setScope} /></div>{scope !== 'historical' ? <ScopeEmpty scope={scope} /> : <><div className="list-heading"><span>{filtered.length} investigations</span><span>Recorded disposition</span></div>{filtered.length ? <div className="notebook-list">{filtered.map(i => <InvestigationRow key={i.id} investigation={i} />)}</div> : <Empty title="No matching investigations">Try a broader phrase or choose all recorded states.</Empty>}<p className="caption roomy">These are cited historical conclusions. They do not create original observations, new M/H reviews, or fresh research authority.</p></>}</>;
}

function InvestigationNotebook({ investigation: i }: { investigation: Investigation }) {
  const { data, navigate, source } = useWorkspace();
  const [tab, setTab] = useState('overview'); const [findingFilter, setFindingFilter] = useState('all');
  const change = i.findings.filter(f => f.kind === 'EVIDENCE_TO_CHANGE');
  const limits = i.findings.filter(f => ['ACQUISITION_LIMIT', 'ACCESS_BLOCKED', 'ACCESS_NOTE', 'SOURCE_OMISSION', 'SCOPE_LIMIT', 'IDENTITY_LIMIT', 'INFORMATION_LIMIT', 'RETROSPECTIVE_ONLY'].includes(f.kind));
  const findings = i.findings.filter(f => findingFilter === 'all' || (findingFilter === 'gaps' ? f.kind === 'MEASUREMENT_GAP' : findingFilter === 'limits' ? limits.includes(f) : findingFilter === 'change' ? f.kind === 'EVIDENCE_TO_CHANGE' : f.kind === 'SOURCE_FIELD_PRESENT'));
  return <><button className="back-link" onClick={() => navigate('investigations')}><Icon name="back" size={16} />All investigations</button><PageHeader eyebrow={`${i.family} · HISTORICAL NOTEBOOK`} title={i.title} action={<button className="button" onClick={() => navigate('connections', i.node)}><Icon name="graph" size={17} />Explore connections</button>}>{i.verdict.scope}</PageHeader><div className="notebook-meta"><Badge tone={i.verdict.status_class === 'HOLD' ? 'amber' : 'neutral'}>{human(i.verdict.status_class)}</Badge><span>Closed {i.historical_closure.date}</span><span>Citations: {human(i.citation_status)}</span><span>Mapping: pending human review</span></div><div className="tabs" role="tablist" onKeyDown={tabKeys} aria-label="Investigation sections">{[['overview', 'The question'], ['evidence', `Evidence & gaps (${i.findings.length})`], ['claims', `Claim history (${i.claims.length})`], ['sources', `Sources (${i.documents.length})`]].map(([id, title]) => <button key={id} id={`tab-${id}`} role="tab" tabIndex={tab === id ? 0 : -1} aria-selected={tab === id} aria-controls={`panel-${id}`} onClick={() => setTab(id)}>{title}</button>)}</div><div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
      {tab === 'overview' && <div className="notebook-columns"><div><section className="prose-section"><span className="eyebrow">THE ORIGINAL IDEA</span><h2>{i.claims.find(c => c.counts_as_original)?.object ?? i.claims[0]?.object}</h2><p>Recorded financial basis: <strong>{human(i.claims[0]?.financial_basis)}</strong>. Read the original report for the full mechanism and its boundaries.</p><button className="source-link" onClick={() => source({ path: i.report })}><Icon name="source" size={15} />Read the original investigation</button></section><section className="prose-section"><span className="eyebrow">WHERE IT LANDED</span><h2 className="verdict-title">{i.verdict.text}</h2><CitationBlock citation={i.verdict.citation} /><p>{i.verdict.scope}</p><CitationBlock citation={i.verdict.scope_citation} /></section><section className="prose-section"><span className="eyebrow">WHAT COULD CHANGE THE ASSESSMENT</span>{change.length ? change.map(f => <FindingCard key={f.id} finding={f} />) : <p>No specific change-of-assessment evidence is recorded in this catalogue. The original report remains the reference.</p>}<p className="caption">A recorded evidence need is a proposal for understanding. Existing stops and holds still stand.</p></section></div><aside className="notebook-aside"><section><h3>The missing measurements</h3>{i.gaps.results.length ? i.gaps.results.map((g, n) => <div className="mini-gap" key={n}><span className="little-dash" /><p>{g.link}</p></div>) : <p className="caption">No separate measurement gaps were catalogued.</p>}</section><section><h3>Entities mentioned</h3>{i.entities.map(e => <button className="entity-item" key={e.id} onClick={() => navigate('connections', Object.values(data.nodes).find(n => n.kind === 'entity' && n.attrs.identifier === e.id)?.id ?? i.node)}><strong>{e.name}</strong><code>{e.id}</code><small>{human(e.identity_basis)}</small></button>)}<p className="caption">Names and archive-path identifiers do not establish ownership or listed exposure.</p></section></aside></div>}
      {tab === 'evidence' && <><div className="filter-pills" aria-label="Finding filters">{[['all', 'All findings'], ['gaps', 'Measurement gaps'], ['present', 'Fields present'], ['limits', 'Source & scope limits'], ['change', 'Evidence to change']].map(([id, label]) => <button key={id} aria-pressed={findingFilter === id} onClick={() => setFindingFilter(id)}>{label}</button>)}</div><p className="caption">Supporting and limiting findings are preserved as written. The catalogue records no new contradictory assertion.</p>{findings.length ? findings.map(f => <FindingCard finding={f} key={f.id} />) : <Empty title="No findings in this category">Nothing in this catalogue is labelled this way. An empty category is not evidence of absence.</Empty>}</>}
      {tab === 'claims' && <><div className="quiet-info"><Icon name="info" /><p>Versions remain separate. A reformulated or restricted claim never counts as a success for the original question.</p></div><div className="claim-timeline">{i.claims.map(c => <article key={c.id}><div className="claim-dot" /><span className="eyebrow">VERSION {c.version} · {c.id}</span><h2>{c.object}</h2><div className="claim-meta"><Badge tone={c.reformulates ? 'amber' : 'sage'}>{c.reformulates ? `Reformulates ${c.reformulates}` : 'Original claim'}</Badge><span>Financial basis: {human(c.financial_basis)}</span><span>After outcome: {human(c.post_outcome)}</span></div>{c.recorded_status.map((s, n) => <div key={n}><h3>{s.text}</h3><CitationBlock citation={s.citation} /></div>)}{c.reformulates && <p className="caption">Counts as original: {c.counts_as_original ? 'yes' : 'no'}. Previous findings and boundaries are preserved.</p>}</article>)}</div></>}
      {tab === 'sources' && <><p className="caption roomy">These are recorded source references and receipts. Original response bodies stay private and are never loaded by this workspace. A complete document is not the same as a verified field.</p>{i.documents.map(d => <article className="source-card" key={d.sha256}><div className="note-top"><Badge tone={d.http_status !== 200 || !d.complete ? 'amber' : 'neutral'}>{d.http_status} · {d.complete ? 'Complete response' : 'Incomplete prefix'}</Badge><span className="caption">{d.body_bytes.toLocaleString()} body bytes</span></div><h3>{d.role}</h3><p className="locator">{d.locator}</p><p className="hash">SHA-256 {d.sha256}</p><button className="source-link" onClick={() => source({ path: d.receipt, quote: d.sha256 })}><Icon name="source" size={15} />Read the recorded receipt</button></article>)}</>}
    </div></>;
}

function FindingCard({ finding: f }: { finding: Investigation['findings'][number] }) {
  const { data, navigate } = useWorkspace();
  return <article className="finding-card"><div className="note-top"><Badge tone={f.kind === 'EVIDENCE_TO_CHANGE' ? 'sage' : f.kind.includes('LIMIT') || f.kind.includes('BLOCKED') ? 'amber' : 'neutral'}>{human(f.kind)}</Badge><span className="caption">{f.id}{f.claim ? ` · claim ${f.claim}` : ''}</span></div><h3>{f.text}</h3><CitationBlock citation={f.citation} />{f.requirement && <button className="text-button requirement-link" onClick={() => navigate('memory', f.requirement!)}>Measurement need: {data.requirements.find(r => r.id === f.requirement)?.label ?? f.requirement}<Icon name="arrow" size={14} /></button>}</article>;
}

function Connections({ initial }: { initial?: string }) {
  const { data, navigate } = useWorkspace();
  const defaultRoot = initial && data.nodes[initial] ? initial : data.investigations.find(i => i.family === 'F19')!.node;
  const [root, setRoot] = useState(defaultRoot); const [selected, setSelected] = useState(defaultRoot);
  const [bound, setBound] = useState('8'); const [scope, setScope] = useState<Scope>('historical');
  const [kind, setKind] = useState('all'); const [edgeKind, setEdgeKind] = useState('all'); const [query, setQuery] = useState('');
  const [onlyVerified, setOnlyVerified] = useState(false); const [showVersions, setShowVersions] = useState(true);
  const [explanationKey, setExplanationKey] = useState<string | null>(null); const [zoom, setZoom] = useState(1);
  const explanationRef = useRef<HTMLElement>(null);
  useEffect(() => { if (explanationKey) explanationRef.current?.scrollIntoView({ block: 'start' }); }, [explanationKey]);
  useEffect(() => { setRoot(defaultRoot); setSelected(defaultRoot); setExplanationKey(null); }, [defaultRoot]);
  const result = data.neighbourhoods[root]?.[bound];
  const neighbourhood = result?.results[0]?.nodes as string[] ?? [];
  const nodeIds = neighbourhood.filter(id => {
    const n = data.nodes[id];
    return inScope(n, scope) && (showVersions || !n.superseded) &&
      (!onlyVerified || ['ORIGINAL_FIELD_OBSERVED', 'DOCUMENTED_RELATIONSHIP'].includes(n.status ?? '')) &&
      (id === root || kind === 'all' || n.kind === kind);
  });
  const exportedEdges = new Set<number>(result?.results[0]?.edges ?? []);
  const edges = data.edges.filter((e, index) => exportedEdges.has(index) && nodeIds.includes(e.src) && nodeIds.includes(e.dst) && (edgeKind === 'all' || e.kind === edgeKind));
  const matches = Object.values(data.nodes).filter(n => inScope(n, scope) && n.search_text.includes(query.toLowerCase())).slice(0, 12);
  const node = data.nodes[selected];
  const positions = useMemo(() => {
    const result: Record<string, { x: number; y: number }> = {};
    const others = nodeIds.filter(id => id !== root);
    const height = Math.max(510, Math.ceil(others.length / 2) * 80 + 60);
    result[root] = { x: 420, y: height / 2 };
    others.forEach((id, index) => {
      const left = index % 2 === 0; const row = Math.floor(index / 2);
      const total = Math.ceil((others.length - (left ? 0 : 1)) / 2);
      result[id] = { x: left ? 155 : 685, y: height / 2 + (row - (total - 1) / 2) * Math.min(110, (height - 100) / Math.max(1, total - 1)) };
    });
    return { nodes: result, height };
  }, [nodeIds.join('|'), root]);
  const focus = (id: string) => { setRoot(id); setSelected(id); setExplanationKey(null); setQuery(''); };
  const explain = (from: string, to: string) => {
    const direct = `${from}\n${to}`, reverse = `${to}\n${from}`;
    setExplanationKey(data.explanations[direct] ? direct : data.explanations[reverse] ? reverse : 'unavailable');
  };
  const incident = data.edges.filter(e => e.src === selected || e.dst === selected);
  return <><PageHeader eyebrow="ONE CONNECTION AT A TIME" title="See how things connect.">A small map of research memory. Every line has a reason, and a limit.</PageHeader><div className="graph-toolbar"><label className="search-field"><Icon name="search" size={17} /><input aria-label="Search graph nodes" placeholder="Find an entity, document, claim…" value={query} onChange={e => setQuery(e.target.value)} /></label><ScopeSelect scope={scope} onChange={setScope} /><label className="select-label">Neighbourhood<select value={bound} onChange={e => setBound(e.target.value)}><option value="8">Small · 8 nodes</option><option value="16">Expand · 16 nodes</option><option value="30">Wide · 30 nodes</option></select></label></div>{query && <div className="graph-search-results" aria-label="Graph search results">{matches.length ? matches.map(n => <button key={n.id} onClick={() => focus(n.id)}><Badge>{kindLabel(n.kind)}</Badge><span>{n.label}</span><Icon name="arrow" size={15} /></button>) : <p>No matching records in this scope.</p>}</div>}
    <div className="graph-filters"><label>Node type<select aria-label="Filter node type" value={kind} onChange={e => setKind(e.target.value)}><option value="all">All types</option>{[...new Set(Object.values(data.nodes).map(n => n.kind))].map(k => <option key={k} value={k}>{kindLabel(k)}</option>)}</select></label><label>Connection<select aria-label="Filter connection type" value={edgeKind} onChange={e => setEdgeKind(e.target.value)}><option value="all">All connections</option>{[...new Set(data.edges.map(e => e.kind))].map(k => <option key={k}>{k}</option>)}</select></label><label className="check-label"><input type="checkbox" checked={onlyVerified} onChange={e => setOnlyVerified(e.target.checked)} />Verified assertions only</label><label className="check-label"><input type="checkbox" checked={showVersions} onChange={e => setShowVersions(e.target.checked)} />Include earlier versions</label></div>
    {scope !== 'historical' ? <ScopeEmpty scope={scope} /> : nodeIds.length === 0 ? <Empty title="No assertions meet these filters">Historical conclusions are not newly verified assertions. Clear the verified-only filter to explore the historical memory.</Empty> : <div className="graph-layout"><section className="graph-canvas"><div className="canvas-header"><span><span className="local-dot" />{nodeIds.length} nodes · {edges.length} connections</span><div className="zoom-controls"><button aria-label="Zoom out" onClick={() => setZoom(z => Math.max(.65, z - .15))}>−</button><button aria-label="Reset zoom" onClick={() => setZoom(1)}>{Math.round(zoom * 100)}%</button><button aria-label="Zoom in" onClick={() => setZoom(z => Math.min(1.6, z + .15))}>+</button></div></div><div className="graph-scroll"><svg role="group" aria-label="Interactive research graph" viewBox={`0 0 840 ${positions.height}`} style={{ width: `${zoom * 100}%`, minHeight: 400 }}>
      {edges.map((e, index) => { const a = positions.nodes[e.src], b = positions.nodes[e.dst]; if (!a || !b) return null; const weak = ['REQUIRES', 'MAY_MEASURE', 'SUGGESTS', 'RELATED'].includes(e.kind) || e.attrs.basis?.includes('MAPPING'); return <g className={`graph-edge ${weak ? 'suggested' : ''}`} key={index} role="button" tabIndex={0} aria-label={`Explain ${e.kind} connection`} onClick={() => explain(e.src, e.dst)} onKeyDown={event => { if (['Enter', ' '].includes(event.key)) { event.preventDefault(); explain(e.src, e.dst); } }}><title>{human(e.kind)} · click to explain</title><line className="edge-hit" x1={a.x} y1={a.y} x2={b.x} y2={b.y} /><line x1={a.x} y1={a.y} x2={b.x} y2={b.y} /></g>; })}
      {nodeIds.map(id => { const n = data.nodes[id], p = positions.nodes[id]; const isRoot = id === root; const label = n.kind === 'document' ? (n.attrs.locators?.[0]?.split('/').at(-1) || 'Recorded document') : n.label; const lines = wrapLabel(label, isRoot ? 25 : 29); return <g key={id} role="button" tabIndex={0} aria-label={`${kindLabel(n.kind)}: ${n.label}`} className={`graph-node ${selected === id ? 'selected' : ''} ${isRoot ? 'root' : ''}`} transform={`translate(${p.x},${p.y})`} onClick={() => { setSelected(id); setExplanationKey(null); }} onKeyDown={e => { if (['Enter', ' '].includes(e.key)) { e.preventDefault(); setSelected(id); setExplanationKey(null); } }}><title>{n.label} — {evidenceLabel(n)}</title><rect x={isRoot ? -108 : -121} y="-33" width={isRoot ? 216 : 242} height="74" rx="9" /><text className="node-kind" textAnchor="middle" y="-12">{kindLabel(n.kind).toUpperCase()}</text>{lines.map((line, index) => <text key={index} textAnchor="middle" y={9 + index * 15}>{line}</text>)}</g>; })}
    </svg></div><div className="graph-legend"><span><i />Recorded structural link</span><span><i className="dashed" />Curated mapping / suggestion</span></div><p className="canvas-note">Connectivity is not evidence of financial exposure. Click a line to inspect its limits.</p>{result.notes.map((n, index) => <p className="caption canvas-note" key={index}>{n}</p>)}</section>
    <aside className="inspector" aria-label="Selected graph record"><span className="eyebrow">A CLOSER LOOK</span><Badge>{kindLabel(node.kind)}</Badge><h2>{node.label}</h2><Badge tone={node.status === 'SUGGESTION_ONLY' ? 'amber' : 'neutral'}>{evidenceLabel(node)}</Badge><p className="inspector-id">{node.id}</p><dl className="record-facts"><dt>Record scope</dt><dd>{human(node.fixture) || 'Derived'}</dd><dt>{node.attrs.historical_closure ? 'Investigation closure' : 'Economic period'}</dt><dd>{node.attrs.historical_closure?.date ?? (typeof node.attrs.period === 'string' ? node.attrs.period : 'Not established for this node')}</dd>{node.attrs.identity_status && <><dt>Identity</dt><dd>{human(node.attrs.identity_status)}</dd></>}{node.attrs.finding_kind && <><dt>Finding kind</dt><dd>{human(node.attrs.finding_kind)}</dd></>}{node.attrs.receipt_status && <><dt>Receipt depth</dt><dd>{node.attrs.receipt_status.join(', ')}</dd></>}</dl>{node.attrs.definition && <p>{node.attrs.definition}</p>}{node.restrictions.map((r, index) => <p className="inspector-note" key={index}>{r}</p>)}{node.attrs.citation && <CitationBlock citation={node.attrs.citation} />}{node.attrs.verdict && <SourceLink citation={node.attrs.verdict.citation} />}
      <div className="inspector-actions"><button className="button" onClick={() => focus(selected)}>Focus here <Icon name="graph" size={16} /></button>{root !== selected && <button className="text-button" onClick={() => explain(root, selected)}>Explain connection to focus <Icon name="arrow" size={14} /></button>}{node.origin.investigation && <button className="text-button" onClick={() => navigate('investigations', node.origin.investigation)}>Open investigation <Icon name="arrow" size={14} /></button>}</div><h3>Connected records <span className="caption">{incident.length}</span></h3><div className="incident-list">{incident.slice(0, 12).map((e, index) => { const target = e.src === selected ? e.dst : e.src; return <button key={index} onClick={() => { setSelected(target); explain(selected, target); }}><small>{human(e.kind)}</small><span>{data.nodes[target].label}</span></button>; })}</div>{incident.length > 12 && <p className="caption">Showing 12 connections. Focus this record and expand the bounded neighbourhood to explore more.</p>}</aside></div>}
    {explanationKey && <section ref={explanationRef} className="explanation" aria-live="polite"><SectionTitle title="What this connection actually says"><button className="icon-button" aria-label="Close connection explanation" onClick={() => setExplanationKey(null)}><Icon name="close" /></button></SectionTitle>{data.explanations[explanationKey] ? <Explanation result={data.explanations[explanationKey]} /> : <p>This pair has no exported explanation. Select a visible line to inspect a bounded Graph v1 explanation. No economic inference has been filled in.</p>}</section>}
  </>;
}

function wrapLabel(value: string, width: number): string[] {
  const words = value.split(/\s+/); const lines = [''];
  for (const word of words) {
    const last = lines.length - 1;
    if ((lines[last] + ' ' + word).length > width && lines[last]) { if (lines.length >= 2) { lines[last] = lines[last].slice(0, width - 2) + '…'; break; } lines.push(word.slice(0, width)); }
    else lines[last] += (lines[last] ? ' ' : '') + word.slice(0, width);
  }
  return lines;
}

function Explanation({ result }: { result: Operator }) {
  const { data } = useWorkspace(); const [pathIndex, setPathIndex] = useState(0);
  useEffect(() => setPathIndex(0), [result]);
  const path = result.results[Math.min(pathIndex, result.results.length - 1)];
  return <>{result.results.length > 1 && <label className="select-label">Bounded paths<select value={pathIndex} onChange={e => setPathIndex(Number(e.target.value))}>{result.results.map((_, index) => <option value={index} key={index}>Path {index + 1}</option>)}</select></label>}{path && <><div className="path-list">{path.steps.map((step: any, index: number) => <div key={index}><span className="path-index">{index + 1}</span><div><strong>{data.nodes[step.to]?.label ?? step.to}</strong><small>{human(step.edge)} · {human(step.connection)}</small><p>{step.establishes}</p>{step.evidence.filter((e: any) => e.citation).map((e: any, n: number) => <SourceLink key={n} citation={e.citation} />)}</div></div>)}</div><div className="unsupported"><Icon name="info" size={20} /><div><span className="eyebrow">FIRST UNSUPPORTED ECONOMIC INFERENCE</span><h3>{human(path.first_unsupported_leap.code)}</h3><p>{path.first_unsupported_leap.detail}</p></div></div></>}{result.abstentions.map(a => <p key={a.code}>{a.reason}</p>)}<p className="caption">{result.notes.join(' ')}</p></>;
}

function Memory() {
  const { data, navigate } = useWorkspace(); const route = routeFromHash();
  const [view, setView] = useState('gaps'); const [selected, setSelected] = useState(route.id && data.same_gap[route.id] ? route.id : data.requirements[0].id);
  const [query, setQuery] = useState('');
  useEffect(() => { if (route.id && data.same_gap[route.id]) { setSelected(route.id); setView('gaps'); } }, [route.id, data]);
  const req = data.requirements.find(r => r.id === selected)!; const result = data.same_gap[selected];
  const shared = data.investigations.flatMap(i => i.shared.results.map(r => ({ ...r, investigation: i })));
  return <><PageHeader eyebrow="KEEP WHAT YOU’VE LEARNED" title="You’ve been here before.">Find familiar gaps, source limits, and useful context without repeating the work.</PageHeader><div className="tabs" role="tablist" onKeyDown={tabKeys} aria-label="Memory views">{[['gaps', 'Shared measurement needs'], ['limits', 'Source limitations'], ['shared', 'Documented overlaps'], ['changes', 'What has changed?']].map(([id, title]) => <button role="tab" id={`memory-tab-${id}`} aria-controls="memory-panel" tabIndex={view === id ? 0 : -1} aria-selected={view === id} key={id} onClick={() => setView(id)}>{title}</button>)}</div>
    <div id="memory-panel" role="tabpanel" aria-labelledby={`memory-tab-${view}`}>{view === 'gaps' && <div className="memory-layout"><aside className="requirement-list"><h3>Measurement needs</h3>{data.requirements.map(r => <button key={r.id} aria-pressed={selected === r.id} onClick={() => setSelected(r.id)}><span>{r.label}</span><small>{data.same_gap[r.id].results.length}</small></button>)}</aside><section className="memory-detail"><Badge tone="sage">Knowledge to reuse</Badge><h2>{req.label}</h2><p>{req.definition}</p><details className="does-not-mean"><summary>What this requirement does not mean</summary><ul>{req.does_not_mean.map(s => <li key={s}>{s}</li>)}</ul></details><SectionTitle title="Where this gap appeared"><span className="small-label">{result.results.length} historical claims</span></SectionTitle>{result.results.map((r, index) => { const node = data.nodes[r.claim]; const inv = data.investigations.find(i => i.node === r.origin); return <article className="memory-result" key={index}><div className="note-top"><span className="eyebrow">{inv?.family} · {human(r.fixture)}</span><Badge>Curated retrieval match</Badge></div><button className="result-title" onClick={() => navigate('investigations', inv?.id)}>{node.label}<Icon name="arrow" size={17} /></button><p>{r.status}</p>{r.why_blocked.map((s: string, n: number) => <p className="muted" key={n}>{s}</p>)}{r.evidence.map((c: Citation, n: number) => <CitationBlock citation={c} key={n} />)}</article>; })}{!result.results.length && <Empty title="No matching historical claims">Graph v1 abstains from suggesting a match for this requirement.</Empty>}<div className="quiet-info"><Icon name="info" /><p>{result.notes.join(' ')} Mappings remain pending human review.</p></div><details className="snapshot-details"><summary>What could be worth revisiting?</summary><p>Graph v1 records no open Discovery Lab claims in this snapshot. A new observation is needed before the revisit operator can suggest a check. Historical evidence-to-change notes remain in each notebook; nothing is reopened here.</p>{data.operators.next.abstentions.map(a => <p key={a.code}><code>{a.code}</code> · {a.reason}</p>)}</details></section></div>}
    {view === 'limits' && <><label className="search-field memory-search"><Icon name="search" size={17} /><input aria-label="Search source limitations" placeholder="Find a source, access stop, or missing field…" value={query} onChange={e => setQuery(e.target.value)} /></label>{(() => { const rows = data.investigations.flatMap(i => i.findings.filter(f => ['SOURCE_OMISSION', 'ACQUISITION_LIMIT', 'ACCESS_BLOCKED', 'ACCESS_NOTE', 'INFORMATION_LIMIT', 'IDENTITY_LIMIT', 'SCOPE_LIMIT'].includes(f.kind)).map(f => ({ i, f }))).filter(({ i, f }) => `${i.title} ${i.family} ${f.text} ${f.kind}`.toLowerCase().includes(query.toLowerCase())); return rows.length ? rows.map(({ i, f }) => <div key={i.id + f.id} className="source-limit-result"><button className="text-button" onClick={() => navigate('investigations', i.id)}>{i.family} · {i.title}<Icon name="arrow" size={14} /></button><FindingCard finding={f} /></div>) : <Empty title="No matching source limits">Try a broader phrase. Missing information remains unknown.</Empty>; })()}</>}
    {view === 'shared' && <><p className="caption roomy">Graph v1’s shared operator matches exact document hashes and identifiers. These results are suggestions for review, never accepted discoveries.</p>{shared.length ? shared.map((s, index) => <article className="finding-card" key={index}><Badge tone="amber">Suggestion only</Badge><h3>{s.investigation.title}</h3><p>Match basis: {s.match_bases?.map(human).join(', ')}</p><button className="text-button" onClick={() => navigate('connections', s.investigation.node)}>Inspect the matching records <Icon name="arrow" size={15} /></button><Structured value={s} /></article>) : <Empty title="No useful overlap to suggest">The existing shared operator found no other campaign or investigation sharing a qualifying document hash or identified entity. Similar wording alone is not enough.</Empty>}<details className="snapshot-details"><summary>Why no complement or revisit suggestions?</summary><p>Those operators require a documented observation. Historical narrative findings never become original observations, so this export does not run them on historical claims.</p></details></>}
    {view === 'changes' && <>{data.operators.changes.results.length ? data.operators.changes.results.map((r, index) => <article className="finding-card" key={index}><h3>{human(r.code)}</h3><Structured value={r} /></article>) : <Empty title="No recorded changes or conflicts">The existing Graph v1 change operator reports none in this snapshot. This does not mean external circumstances are unchanged.</Empty>}<p className="caption roomy">Catalogue V002 preserves 12 cited mapping corrections. Earlier verdicts remain unchanged. This workspace does not refresh historical citations or research conclusions.</p></>}</div>
  </>;
}

function Pilot({ pilot, setPilot }: { pilot: PilotExport | null; setPilot: (p: PilotExport | null) => void }) {
  const [confirmed, setConfirmed] = useState(false); const [error, setError] = useState('');
  const fields: string[] = [...metricNames];
  return <><PageHeader eyebrow="A PLACE FOR THE RESULTS, WHEN THEY’RE READY" title="The pilot notebook.">Read a completed comparison without disturbing the research in progress.</PageHeader>{!pilot ? <><div className="pilot-empty"><Empty title="No completed pilot report loaded" icon="compare">The workspace has not opened arm ledgers, packet snapshots, or blinded adjudication files. When a completed, authorised report is unsealed, you can read its export here.</Empty><div className="pilot-import"><h3>Bring in a completed report</h3><p>The file stays in this tab’s memory. It is never uploaded or saved to the research repository.</p><label className="confirm-label"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />I confirm this is a completed, unsealed report authorised for viewing.</label><label className={`button ${!confirmed ? 'disabled' : ''}`}><Icon name="upload" size={17} />Choose report export<input type="file" aria-label="Import completed pilot report" accept=".json,application/json" disabled={!confirmed} onChange={async e => { const file = e.target.files?.[0]; if (!file) return; try { if (file.size > 1_000_000) throw new Error('Please choose an export smaller than 1 MB.'); setPilot(parsePilot(await file.text())); setError(''); } catch (err) { setError(err instanceof Error ? err.message : 'Unable to read this export.'); } e.target.value = ''; }} /></label>{error && <p className="form-error" role="alert">{error}</p>}<p className="caption">Accepts WORKSPACE_COMPLETED_PILOT_V1 with the existing PILOT_PAIRED_REPORT output. Format and limits are documented in the app README.</p></div></div><div className="quiet-info"><Icon name="leaf" /><p>No results have been inferred. Synthetic rehearsals and software tests are separate from scientific pilot outcomes.</p></div></> : <><div className="import-header"><Badge tone="sage">Completed · declared unsealed</Badge><button className="text-button" onClick={() => { setPilot(null); setConfirmed(false); }}>Remove report from this tab</button></div><div className="quiet-info"><Icon name="info" /><p>Owner-supplied export. The app validates its structure and displays recorded values; it cannot independently certify completion, authorisation, unsealing, or the scientific judgments.</p></div><h2>{human(pilot.report.classification)}</h2>{pilot.report.notes.map((n, index) => <p key={index}>{n}</p>)}{pilot.report.packets.map(p => <section className="pilot-packet" key={p.packet}><SectionTitle title={`${p.packet} · ${p.method}`} /><div className="table-scroll"><table><caption>Recorded paired outcomes. Unknown values stay unknown. All analyst time is retained in the report’s denominator.</caption><thead><tr><th scope="col">Recorded measure</th><th scope="col">Structured search · S</th><th scope="col">Graph assisted · G</th></tr></thead><tbody>{fields.map(f => <tr key={f}><th scope="row">{human(f)}{f.includes('minutes') ? ' (min)' : ''}</th><td>{p.S[f] ?? 'Unknown'}</td><td>{p.G[f] ?? 'Unknown'}</td></tr>)}<tr><th scope="row">False / trivial graph suggestions</th><td>{p.S.graph_suggestions_false_or_trivial.join(' / ')}</td><td>{p.G.graph_suggestions_false_or_trivial.join(' / ')}</td></tr><tr><th scope="row">Recorded budget violations</th><td>{p.S.budget_violations.map(violationText).join('; ') || 'None recorded'}</td><td>{p.G.budget_violations.map(violationText).join('; ') || 'None recorded'}</td></tr></tbody></table></div><details><summary>Recorded comparison directions and decisive checks</summary><Structured value={{ directions: p.directions, decisive_falsification: { S: p.S.decisive_falsification, G: p.G.decisive_falsification } }} /></details></section>)}<div className="source-card"><h3>Export provenance</h3><p>Declared authorisation: {pilot.authorisation.path}</p><p className="hash">Declared authorisation SHA-256: {pilot.authorisation.sha256}</p><p className="hash">Declared source-report SHA-256: {pilot.source_report_sha256}</p><p className="caption">Source counts, missing-evidence detail, and protocol deviations beyond budget violations are not fields in the current paired-report contract. They remain unavailable here.</p></div></>}</>;
}

function Archive() {
  const { data, source } = useWorkspace();
  return <><PageHeader eyebrow="THE LONGER MEMORY" title="Every attempt has a place.">Seven experiment references, with their recorded findings and original boundaries.</PageHeader><p className="caption roomy">Reports are historical records, not invitations to rerun a study. No performance is recomputed in this workspace.</p><div className="archive-list">{data.experiments.map(e => { const doc = data.documents[e.path]; const paragraphs = doc.text.split(/\r?\n\s*\r?\n/); const title = paragraphs[0]?.replace(/^#\s*/, ''); const lead = paragraphs.find((p, index) => index > 0 && !p.startsWith('#') && p.trim().length > 40); return <article className="archive-entry" key={e.id}><span className="family-label">{e.id}</span><div><h2>{title}</h2><p>{lead}</p><button className="source-link" onClick={() => source({ path: e.path })}><Icon name="source" size={15} />Read the historical report</button><p className="caption">{e.path}</p></div></article>; })}</div></>;
}

function Modal({ children, onClose, labelledBy, className = '' }: { children: ReactNode; onClose: () => void; labelledBy: string; className?: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { const d = dialog.current!; if (!d.open) d.showModal(); return () => { if (d.open) d.close(); }; }, []);
  return <dialog ref={dialog} className={className} aria-labelledby={labelledBy} onCancel={e => { e.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>{children}</dialog>;
}

function DocumentModal({ request, onClose }: { request: SourceRequest; onClose: () => void }) {
  const { data } = useWorkspace(); const doc = data.documents[request.path];
  const [query, setQuery] = useState(request.quote ?? '');
  const body = useRef<HTMLDivElement>(null);
  useEffect(() => { body.current?.querySelector('mark')?.scrollIntoView({ block: 'center' }); }, [query, request.path]);
  return <Modal onClose={onClose} labelledBy="document-title" className="document-modal"><header className="modal-header"><div><span className="eyebrow">FROM THE ORIGINAL NOTEBOOK</span><h2 id="document-title">{request.path.split('/').at(-1)?.replaceAll('_', ' ')}</h2></div><button className="icon-button" aria-label="Close source document" onClick={onClose}><Icon name="close" /></button></header>{!doc ? <Empty title="This document is outside the export">The viewer only opens its fixed set of included public documents. Arbitrary local paths are never resolved.</Empty> : <><div className="document-meta"><Badge tone={doc.status.includes('CHANGED') ? 'amber' : 'neutral'}>{human(doc.status)}</Badge><span>{doc.path}</span><details><summary>Source integrity</summary><p className="hash">Current file SHA-256: {doc.sha256}</p>{doc.expected_sha256 && <p className="hash">Catalogue SHA-256: {doc.expected_sha256}</p>}<p>Exact tracked document text. Links and HTML in this document are displayed as text and cannot run.</p></details></div><label className="search-field document-search"><Icon name="search" size={17} /><input aria-label="Find in source document" placeholder="Find an exact passage…" value={query} onChange={e => setQuery(e.target.value)} /><span className="caption">{query ? doc.text.includes(query) ? 'Passage found' : 'No exact match' : 'Original text'}</span></label><div className="document-body" ref={body}><pre>{highlight(doc.text, query)}</pre></div></>}</Modal>;
}
function highlight(text: string, query: string): ReactNode {
  if (!query) return text;
  const index = text.indexOf(query); if (index < 0) return text;
  return <>{text.slice(0, index)}<mark>{text.slice(index, index + query.length)}</mark>{text.slice(index + query.length)}</>;
}

function SearchModal({ query, setQuery, onClose }: { query: string; setQuery: (q: string) => void; onClose: () => void }) {
  const { data, navigate } = useWorkspace();
  const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const rows = Object.values(data.nodes).filter(n => words.length && words.every(w => n.search_text.includes(w))).slice(0, 25);
  return <Modal onClose={onClose} labelledBy="search-title" className="search-modal"><div className="modal-header"><h2 id="search-title">Find a thread to follow.</h2><button className="icon-button" aria-label="Close search" onClick={onClose}><Icon name="close" /></button></div><label className="search-field"><Icon name="search" /><input autoFocus aria-label="Search all research" placeholder="A question, entity, source, or missing measurement…" value={query} onChange={e => setQuery(e.target.value)} /></label><div className="global-results">{rows.length ? rows.map(n => <button key={n.id} onClick={() => { navigate(n.kind === 'history' ? 'investigations' : 'connections', n.kind === 'history' ? n.origin.investigation : n.id); onClose(); }}><span><Badge>{kindLabel(n.kind)}</Badge><strong>{n.label}</strong><small>{evidenceLabel(n)} · {n.origin.investigation ?? 'Graph v1'}</small></span><Icon name="arrow" size={16} /></button>) : <Empty title={words.length ? 'No matching threads' : 'Your notebook is here'}>{words.length ? 'Try fewer words or search a family such as F19.' : 'Search across the existing Graph v1 record labels and indexed fields.'}</Empty>}</div><p className="caption">Up to 25 text matches · historical records only · search does not establish identity or exposure.</p></Modal>;
}

function Structured({ value }: { value: unknown }) { return <details className="snapshot-details"><summary>Inspect the recorded operator output</summary><pre className="structured">{JSON.stringify(value, null, 2)}</pre></details>; }
