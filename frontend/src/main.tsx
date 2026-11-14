import { StrictMode, useEffect, useRef, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import type { Bootstrap, CaseResult, Feedback, Matter, MatterDetail, ResearchSource, Round, Scenario, Settings } from './types';
import './styles.css';
import { ConnectionError, requestAPI } from './api';
import { canSearch, isCourtListenerCase, passageLocation } from './source';

const defaultSettings: Settings = { theme: 'light', font_size: 'normal', density: 'comfortable', preferred_summary: 'concise' };
const today = new Date().toISOString().slice(0, 10);
function newMatter(source: ResearchSource = 'local') {
  return { title: '', question: '', facts: '', source, court: source === 'local' ? 'scotus' : 'all', date_from: source === 'local' ? '1980-01-01' : '1900-01-01', date_to: source === 'local' ? '2020-12-31' : today };
}
const fallbackCourts = [
  { id: 'all', label: 'All available U.S. courts' }, { id: 'scotus', label: 'U.S. Supreme Court' },
  ...Array.from({ length: 11 }, (_, index) => ({ id: `ca${index + 1}`, label: `U.S. Court of Appeals · Circuit ${index + 1}` })),
  { id: 'cadc', label: 'U.S. Court of Appeals · D.C. Circuit' }, { id: 'cafc', label: 'U.S. Court of Appeals · Federal Circuit' },
];
function message(error: unknown) { return error instanceof Error ? error.message : 'Something went wrong. Please try again.'; }
function safeURL(url: string) { try { const parsed = new URL(url); return ['https:', 'http:'].includes(parsed.protocol) ? parsed.href : undefined; } catch { return undefined; } }
function SourceLink({ url, children }: { url: string; children: React.ReactNode }) { const href = safeURL(url); return href ? <a href={href} target="_blank" rel="noopener noreferrer">{children} ↗</a> : <span>Source link unavailable</span>; }

function App() {
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null);
  const [detail, setDetail] = useState<MatterDetail | null>(null);
  const [settings, setSettings] = useState(defaultSettings);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [draft, setDraft] = useState(() => newMatter());
  const [creating, setCreating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [activeRound, setActiveRound] = useState<string | null>(null);
  const [reader, setReader] = useState<CaseResult | null>(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [connectionLost, setConnectionLost] = useState(false);
  const [notice, setNotice] = useState('');
  const [filter, setFilter] = useState('');
  const [useModel, setUseModel] = useState(false);
  const [consentExternal, setConsentExternal] = useState(false);
  const [consentSource, setConsentSource] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dialog = useRef<HTMLDialogElement>(null);
  const token = useRef('');

  async function api<T>(url: string, method = 'GET', body?: unknown): Promise<T> {
    try {
      return await requestAPI<T>(url, method, body, {
        getToken: () => token.current, setToken: value => { token.current = value; },
      });
    } catch (e) {
      if (e instanceof ConnectionError) setConnectionLost(true);
      throw e;
    }
  }
  async function initialize(preserveCurrent = false) {
    setBusy('Connecting to your local workspace…'); setError('');
    try {
      const data = await api<Bootstrap>('/api/bootstrap'); token.current = data.csrf_token;
      const examples = await api<Scenario[]>('/api/examples');
      const currentId = preserveCurrent && detail && data.matters.some(item => item.id === detail.matter.id) ? detail.matter.id : data.matters[0]?.id;
      const found = currentId ? await api<MatterDetail>(`/api/matters/${currentId}`) : null;
      setBootstrap(data); setSettings(data.settings); setScenarios(examples);
      setDetail(found);
      if (!preserveCurrent) {
        setCreating(!found);
        setDraft(newMatter(data.capabilities.courtlistener_available ? 'courtlistener' : 'local'));
        setUseModel(found?.matter.source === 'courtlistener' && data.capabilities.agent_available);
      }
      else if (!found && !creating) setCreating(true);
      if (found) setActiveRound(previous => preserveCurrent && found.rounds.some(item => item.id === previous) ? previous : found.rounds.at(-1)?.id ?? null);
      setConnectionLost(false);
      if (preserveCurrent) setNotice('Connected. Your entries are preserved and saved history is refreshed. Check whether the previous action completed before trying it again.');
    } catch (e) { setError(message(e)); }
    finally { setBusy(''); }
  }
  useEffect(() => { void initialize(); }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme;
    document.documentElement.dataset.font = settings.font_size;
    document.documentElement.dataset.density = settings.density;
  }, [settings]);
  useEffect(() => { if (reader && dialog.current && !dialog.current.open) dialog.current.showModal(); }, [reader]);
  useEffect(() => {
    setConsentSource(false); setConsentExternal(false); setSearchQuery('');
  }, [detail?.matter.id]);

  async function perform(label: string, action: () => Promise<void>) {
    setBusy(label); setError(''); setNotice('');
    try { await action(); } catch (e) { setError(message(e)); } finally { setBusy(''); }
  }
  async function reloadMatter(id = detail?.matter.id) {
    if (!id) return;
    const updated = await api<MatterDetail>(`/api/matters/${id}`); setDetail(updated); return updated;
  }
  function openMatter(id: string) {
    void perform('Opening matter…', async () => {
      const updated = await reloadMatter(id); setActiveRound(updated?.rounds.at(-1)?.id ?? null); setCreating(false); setFilter('');
      if (id !== detail?.matter.id) setUseModel(updated?.matter.source === 'courtlistener' && !!bootstrap?.capabilities.agent_available);
    });
  }
  function createMatter(event: FormEvent) {
    event.preventDefault();
    void perform('Creating matter…', async () => {
      const matter = await api<Matter>('/api/matters', 'POST', draft);
      setBootstrap(previous => previous ? { ...previous, matters: [matter, ...previous.matters] } : previous);
      await reloadMatter(matter.id); setActiveRound(null); setCreating(false); setDraft(newMatter(bootstrap?.capabilities.courtlistener_available ? 'courtlistener' : 'local')); setUseModel(matter.source === 'courtlistener' && !!bootstrap?.capabilities.agent_available); setNotice('Matter saved locally. Review the search controls, then run the first search.');
    });
  }
  function search() {
    if (!detail) return;
    void perform(detail.matter.source === 'courtlistener' ? 'Searching CourtListener case law…' : 'Searching the local opinion collection…', async () => {
      const round = await api<Round>(`/api/matters/${detail.matter.id}/search`, 'POST', { use_model: useModel, consent_external: consentExternal, consent_source: consentSource, search_query: searchQuery.trim(), request_id: crypto.randomUUID() });
      await reloadMatter(); setActiveRound(round.id); setFilter('');
      setNotice(round.status === 'completed' ? `Round ${round.number} completed. ${round.results.length} result${round.results.length === 1 ? '' : 's'}.` : `Round ${round.number} ${round.status === 'failed' ? 'failed' : 'stopped early'}. Your previous research is preserved.`);
    });
  }
  function updateFeedback(id: string, value: Feedback | null) {
    if (!detail) return;
    void perform('Saving feedback…', async () => {
      await api(`/api/matters/${detail.matter.id}/feedback/${id}`, value ? 'PUT' : 'DELETE', value ?? undefined);
      await reloadMatter(); setNotice('Feedback updated. It will be used in the next search.');
    });
  }
  function toggleSelection(item: CaseResult) {
    if (!detail) return;
    const saved = detail.selections.some(entry => entry.id === item.id);
    void perform(saved ? 'Removing saved case…' : 'Saving case…', async () => {
      await api(`/api/matters/${detail.matter.id}/selections/${item.id}`, saved ? 'DELETE' : 'PUT', saved ? undefined : {});
      await reloadMatter(); setNotice(saved ? 'Case removed from your collection.' : 'Case saved. Its relevance feedback is unchanged.');
    });
  }
  function saveSettings(next: Settings) {
    void perform('Saving settings…', async () => { await api('/api/settings', 'PUT', next); setSettings(next); setNotice('Settings saved on this device.'); });
  }
  function deleteMatter() {
    if (!detail || !window.confirm(`Delete “${detail.matter.title}” and its local history, feedback, and saved cases? The shared source cache will remain on this device. This cannot be undone.`)) return;
    void perform('Deleting matter…', async () => {
      await api(`/api/matters/${detail.matter.id}`, 'DELETE');
      setBootstrap(previous => previous ? { ...previous, matters: previous.matters.filter(item => item.id !== detail.matter.id) } : previous);
      setDetail(null); setCreating(true); setActiveRound(null); setNotice('Matter and workspace history deleted. The shared source cache remains on this device.');
    });
  }
  const round = detail?.rounds.find(item => item.id === activeRound) ?? detail?.rounds.at(-1);
  const retryAfter = round?.error?.retry_after_seconds ?? round?.error?.retry_after;
  const suggestedWait = typeof retryAfter === 'number' && Number.isFinite(retryAfter) && retryAfter > 0 ? Math.ceil(retryAfter) : null;
  const results = round?.results.filter(item => `${item.case_name} ${item.citation} ${item.explanation}`.toLowerCase().includes(filter.toLowerCase())) ?? [];
  const corpusCount = bootstrap?.capabilities.corpus_count ?? 0;
  const source = creating ? draft.source : detail?.matter.source ?? 'local';
  const liveSource = source === 'courtlistener';
  const courtlistenerAvailable = !!bootstrap?.capabilities.courtlistener_available;
  const courts = bootstrap?.courts ?? fallbackCourts;
  const courtLabel = (court: string) => courts.find(item => item.id === court)?.label ?? court.toUpperCase();
  const searchReady = canSearch({ source, corpusCount, courtlistenerAvailable, consentSource, useModel,
    agentAvailable: !!bootstrap?.capabilities.agent_available, consentModel: consentExternal });
  const readerIsLive = reader ? isCourtListenerCase(reader) : false;

  return <div className="workspace">
    <a className="skip-link" href="#main">Skip to research</a>
    <aside className="sidebar" aria-label="Workspace navigation">
      <div className="brand"><span className="brand-mark" aria-hidden="true">§</span><div><strong>Casework</strong><span>LEGAL RESEARCH WORKSPACE</span></div></div>
      <button className="new-button" disabled={!!busy || !bootstrap} onClick={() => { setCreating(true); setShowSettings(false); setDraft(newMatter(courtlistenerAvailable ? 'courtlistener' : 'local')); setConsentSource(false); setConsentExternal(false); setSearchQuery(''); }}>＋ New matter</button>
      <div className="sidebar-label">YOUR MATTERS <span>{bootstrap?.matters.length ?? 0}</span></div>
      <nav className="matters">{bootstrap?.matters.map(item => <button className={!creating && detail?.matter.id === item.id ? 'matter-item active' : 'matter-item'} key={item.id} disabled={!!busy} onClick={() => openMatter(item.id)}><span>{item.title}</span><small>{item.source === 'courtlistener' ? 'CourtListener' : 'Demo'} · {item.court === 'all' ? 'All courts' : item.court.toUpperCase()} · {item.date_from.slice(0, 4)}–{item.date_to.slice(0, 4)}</small></button>)}
      {bootstrap?.matters.length === 0 && <p className="sidebar-empty">Your research stays organized here, one matter at a time.</p>}</nav>
      <div className="sidebar-bottom"><button className="sidebar-settings" onClick={() => setShowSettings(!showSettings)} aria-expanded={showSettings}>⚙ Workspace settings</button><div className="local-badge"><span aria-hidden="true"/> Stored on this device</div><p>History, saved cases, and preferences stay in your local workspace.</p></div>
    </aside>
    <div className="content">
      <header className="topbar"><span>Research workspace <span className="breadcrumb">/ {creating ? 'New matter' : detail?.matter.title ?? 'Overview'}</span></span><span className="mode-badge">{liveSource ? 'COURTLISTENER' : 'LOCAL DEMO'}</span></header>
      <div className="coverage">{liveSource ? <><strong>CourtListener case search</strong><span>U.S. case law · choose court and date filters for each matter</span><p>Search CourtListener and cache retrieved opinion text on this device. Queries leave your device; source access limits apply. Coverage varies, and subsequent treatment is not checked.</p></> : <><strong>Demonstration collection</strong><span>{corpusCount} imported opinions · U.S. Supreme Court · vehicle searches · 1980–2020</span><p>This small historical collection is for reproducible examples. {courtlistenerAvailable ? 'Create a new matter with CourtListener to search beyond these opinions.' : 'Configure CourtListener access to search a broader collection.'} Subsequent treatment is not checked.</p></>}</div>
      <main id="main">
        {error && <div className="alert error" role="alert"><strong>We couldn’t complete that action.</strong><p>{error}</p>{(connectionLost || !bootstrap) && <button onClick={() => void initialize(true)} disabled={!!busy}>Retry connection</button>}</div>}
        <div className="live-status" role="status" aria-live="polite">{busy || notice}</div>
        {showSettings && <section className="settings panel"><div className="section-heading"><div><p className="eyebrow">PERSONAL WORKSPACE</p><h2>Settings</h2></div><button className="text-button" onClick={() => setShowSettings(false)}>Close</button></div><div className="settings-grid">
          <label>Appearance<select value={settings.theme} disabled={!!busy} onChange={e => saveSettings({ ...settings, theme: e.target.value as Settings['theme'] })}><option value="light">Light</option><option value="dark">Dark</option></select></label>
          <label>Text size<select value={settings.font_size} disabled={!!busy} onChange={e => saveSettings({ ...settings, font_size: e.target.value as Settings['font_size'] })}><option value="normal">Standard</option><option value="large">Large</option></select></label>
          <label>Result spacing<select value={settings.density} disabled={!!busy} onChange={e => saveSettings({ ...settings, density: e.target.value as Settings['density'] })}><option value="comfortable">Comfortable</option><option value="compact">Compact</option></select></label>
          <label>Preferred explanation length<select value={settings.preferred_summary} disabled={!!busy} onChange={e => saveSettings({ ...settings, preferred_summary: e.target.value as Settings['preferred_summary'] })}><option value="concise">Concise</option><option value="detailed">Detailed</option></select></label>
        </div><p className="muted small">Explicit preferences only; the application does not learn across matters. Explanation length applies to model-assisted analysis; local keyword results are unchanged. Downloads use your browser’s save settings.</p><button className="text-button" disabled={!!busy} onClick={() => saveSettings(defaultSettings)}>Reset preferences</button></section>}
        {creating ? <section className="new-matter"><p className="eyebrow">BEGIN A RESEARCH MATTER</p><h1>Follow the question.<br/><em>Keep the evidence.</em></h1><p className="intro">Describe the issue you are investigating. Search the collection, inspect the source, and build a set of cases worth keeping.</p>
          {scenarios.length > 0 && <div className="scenario-picker"><label htmlFor="scenario">Start with a synthetic example</label><select id="scenario" defaultValue="" onChange={event => { const scenario = scenarios.find(item => item.id === event.target.value); if (scenario) setDraft(previous => ({ ...previous, title: scenario.title, question: scenario.research_question, facts: scenario.fact_pattern })); }}><option value="" disabled>Choose a demo scenario…</option>{scenarios.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></div>}
          <form className="panel matter-form" onSubmit={createMatter}><label>Case source<select value={draft.source} onChange={event => { const next = event.target.value as ResearchSource; const defaults = newMatter(next); setDraft(previous => ({ ...previous, source: next, court: defaults.court, date_from: defaults.date_from, date_to: defaults.date_to })); }}><option value="courtlistener" disabled={!courtlistenerAvailable}>CourtListener · broader U.S. case search{!courtlistenerAvailable ? ' (not configured)' : ''}</option><option value="local">Local demo · {corpusCount} imported opinions</option></select></label><p className="small muted">{draft.source === 'courtlistener' ? 'Search the external collection within your selected scope. Opinions are fetched as needed and cached locally.' : 'A small offline collection for demonstrations and repeatable checks.'}</p><label>Matter title<input required maxLength={160} value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} placeholder="e.g. Vehicle search following an arrest"/></label><label>Research question<textarea required rows={3} maxLength={6000} value={draft.question} onChange={e => setDraft({ ...draft, question: e.target.value })} placeholder="What issue should the cases help you examine?"/></label><label>Facts and context<textarea rows={4} maxLength={12000} value={draft.facts} onChange={e => setDraft({ ...draft, facts: e.target.value })} placeholder="Describe the facts that matter to your search."/></label><div className="filters"><label>Court<select value={draft.court} onChange={e => setDraft({ ...draft, court: e.target.value })}>{(draft.source === 'local' ? [{ id: 'scotus', label: 'U.S. Supreme Court' }] : courts).map(item => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label><label>Decided from<input type="date" required min={draft.source === 'local' ? '1980-01-01' : '1600-01-01'} max={draft.date_to || today} value={draft.date_from} onChange={e => setDraft({ ...draft, date_from: e.target.value })}/></label><label>Through<input type="date" required min={draft.date_from || (draft.source === 'local' ? '1980-01-01' : '1600-01-01')} max={draft.source === 'local' ? '2020-12-31' : today} value={draft.date_to} onChange={e => setDraft({ ...draft, date_to: e.target.value })}/></label></div><p className="small muted">These constraints stay fixed across search rounds. Start another matter to research a different scope.</p><div className="form-footer"><span>Saved locally · no model request</span><button className="primary" disabled={!!busy || !bootstrap} type="submit">Create matter →</button></div></form>
        </section> : detail ? <>
          <div className="matter-heading"><div><p className="eyebrow">RESEARCH MATTER</p><h1>{detail.matter.title}</h1></div><button className="text-button danger" disabled={!!busy} onClick={deleteMatter}>Delete matter</button></div>
          <section className="question-panel panel"><h2>Research question</h2><p>{detail.matter.question}</p>{detail.matter.facts && <details><summary>Facts and context</summary><p>{detail.matter.facts}</p></details>}<div className="scope-chips"><span>{liveSource ? 'CourtListener' : 'Local demo'}</span><span>{courtLabel(detail.matter.court)}</span><span>{detail.matter.date_from} — {detail.matter.date_to}</span><span>{detail.rounds.length} search round{detail.rounds.length === 1 ? '' : 's'}</span></div></section>
          {!liveSource && !corpusCount && <div className="alert"><strong>Import the real opinions to begin.</strong><p>No case text has been loaded. From the project directory, run <code>python scripts/import_demo_corpus.py</code>, then refresh this page. The importer uses official PDFs; it does not require an OpenAI key.</p></div>}
          <div className="research-layout"><section className="results-area"><div className="section-heading"><div><p className="eyebrow">DISCOVERY</p><h2>Case results {round && <span className="count">{round.results.length}</span>}</h2></div><button className="primary" disabled={!!busy || !searchReady} onClick={search}>{busy.includes('Searching') ? 'Searching…' : detail.rounds.length ? 'Search again →' : 'Search collection →'}</button></div>
            <p className="muted small">Feedback is optional. Each new round uses your current feedback; saved cases remain separate.</p>
            {liveSource && <div className="source-controls panel">
              <strong>External case search</strong>
              {!courtlistenerAvailable && <p className="small">CourtListener access is not configured in this running server. Complete local token setup and restart the app.</p>}
              <label className="checkbox-label"><input type="checkbox" checked={consentSource} disabled={!!busy || !courtlistenerAvailable} onChange={event => setConsentSource(event.target.checked)}/>I understand that search queries derived from this matter and feedback will be sent to CourtListener to retrieve case law.</label>
              <details><summary>Search terms (optional)</summary><label>Keywords or quoted phrases<input maxLength={1200} value={searchQuery} disabled={!!busy} onChange={event => setSearchQuery(event.target.value)} placeholder={'e.g. "automobile exception" passenger'}/></label><p className="small muted">Leave blank to use the research question and feedback. With model assistance, these terms guide the search; without it, they are the keyword query.</p></details>
              <p className="small muted">Each round uses a limited number of source requests. Cached opinions can be reused; provider rate limits may require waiting before another round.</p>
            </div>}
            <div className="model-controls"><label className="checkbox-label"><input type="checkbox" checked={useModel} disabled={!!busy || (!bootstrap?.capabilities.agent_available && !useModel)} onChange={e => setUseModel(e.target.checked)}/>Use configured cloud model</label><p className="small muted">{liveSource ? 'Off: CourtListener keyword search. On: the configured model plans searches, reads opinions, and explains results.' : 'Off: keyword retrieval runs locally. On: the configured model assists research.'}{!bootstrap?.capabilities.agent_available && ' Model access is not configured.'}</p>{useModel && <label className="checkbox-label"><input type="checkbox" checked={consentExternal} disabled={!!busy} onChange={e => setConsentExternal(e.target.checked)}/>I understand that this matter’s question, facts, feedback, and selected opinion passages will be sent to OpenAI, with API usage costs.</label>}</div>
            {detail.rounds.length > 0 && <div className="round-tools"><label>Search round<select value={round?.id ?? ''} onChange={e => { setActiveRound(e.target.value); setFilter(''); }}>{detail.rounds.map(item => <option key={item.id} value={item.id}>Round {item.number} · {item.status} · {item.results.length} results</option>)}</select></label><label>Filter displayed cases<input type="search" value={filter} onChange={e => setFilter(e.target.value)} placeholder="Case name, citation, or explanation"/></label></div>}
            {round && round.status !== 'completed' && <div className="alert error" role="alert"><strong>{round.status === 'failed' ? 'This research round failed.' : 'This research round stopped before completion.'}</strong><p>{round.stop_reason}</p>{suggestedWait !== null && <p>Suggested wait: about {suggestedWait} seconds from when this round stopped. Provider limits may still apply afterward.</p>}<p>Previous results and saved cases remain available. Review the activity below, resolve the issue, then start another round.</p></div>}
            {round && <details className="trace panel"><summary>Search activity · round {round.number} · {round.mode}</summary><p><strong>Query</strong><br/>{round.query}</p><ol>{round.actions.map((action, index) => <li key={index}><strong>{action.tool}</strong> — {action.detail}</li>)}</ol><p className="small"><strong>Stopped:</strong> {round.stop_reason}</p><p className="small muted">Feedback shown on case cards is current; this round preserves the feedback snapshot used when it ran.</p></details>}
            {!round ? <div className="empty-state"><span aria-hidden="true">⌕</span><h3>Your first search starts here.</h3><p>{liveSource ? 'Search CourtListener, then open a case to inspect retrieved opinion passages.' : 'Explore the imported collection, then open a case to inspect its source passages.'}</p></div> : results.length === 0 ? <div className="empty-state"><h3>{filter ? 'No displayed cases match this filter.' : round.status !== 'completed' ? 'No verified results published.' : 'No matching cases found in this round.'}</h3><p>{filter ? 'Try a different case name or clear the filter.' : round.status !== 'completed' ? 'See the stop reason above. An incomplete or failed round does not establish that no relevant case exists.' : 'This search did not return a suitable case within its scope and request budget. Your previous rounds and saved cases are still available.'}</p></div> : results.map(item => <CaseCard key={`${round.id}:${item.id}`} item={item} feedback={detail.feedback[item.id]} saved={detail.selections.some(saved => saved.id === item.id)} busy={!!busy} onInspect={() => setReader(item)} onSave={() => toggleSelection(item)} onFeedback={value => updateFeedback(item.id, value)}/>)}
          </section><aside className="saved-panel panel"><p className="eyebrow">YOUR COLLECTION</p><h2>Saved cases <span className="count">{detail.selections.length}</span></h2><p className="muted small">Keep useful authorities, including cases that challenge your position.</p>{detail.selections.length ? <><a className="export-button" href={`/api/matters/${detail.matter.id}/export.csv`} download>↓ Export collection · CSV</a><ul className="saved-list">{detail.selections.map(item => <li key={item.id}><button className="saved-title" onClick={() => setReader(item)}>{item.case_name}</button><span>{item.citation}</span><button className="text-button" disabled={!!busy} onClick={() => toggleSelection(item)}>Remove</button></li>)}</ul></> : <div className="saved-empty"><p>No cases saved yet.</p><p>Use “Save case” on a result. Saving never changes its relevance feedback.</p></div>}</aside></div>
        </> : !busy && !error && <div className="empty-state"><h1>Your research workspace</h1><p>Create a matter to begin.</p></div>}
      </main><footer>Casework · Local-first case research <span>Engineering prototype · legal review not completed</span></footer>
    </div>
    <dialog ref={dialog} className="source-dialog" onClose={() => setReader(null)} onClick={event => { if (event.target === dialog.current) dialog.current?.close(); }}>{reader && <article>
      <div className="section-heading"><p className="eyebrow">SOURCE INSPECTION</p><button aria-label="Close source inspection" onClick={() => dialog.current?.close()}>Close ×</button></div>
      <h2>{reader.case_name}</h2><p className="muted">{reader.citation} · {reader.decision_date}</p>
      <SourceLink url={reader.source_url}>{readerIsLive ? 'Open CourtListener opinion' : 'Open official opinion'}</SourceLink>
      <div className="interpretation"><h3>Why this result appeared</h3><p>{reader.explanation}</p><p className="small muted">{reader.explanation_kind?.startsWith('model_generated') ? 'Model-generated interpretation. Evidence references were checked against retrieved source text; legal support has not been independently validated.' : readerIsLive ? 'CourtListener search result, not model-generated legal analysis. Inspect the opinion to assess relevance.' : 'Local keyword-match explanation, not model-generated legal analysis.'}</p></div>
      {reader.summary && <details><summary>{readerIsLive ? 'Source overview' : 'Editorial case overview'}</summary><p>{reader.summary}</p><p className="small muted">{readerIsLive ? 'Navigation metadata; use the opinion text to verify legal reasoning.' : 'Original demo metadata; not a quotation or generated legal analysis.'}</p></details>}
      <h3>Extracted source passages</h3>
      <p className="small muted">{readerIsLive ? 'Passages come from a locally cached text extraction of the CourtListener opinion. Text sections are navigation aids, not official page or reporter pinpoints. Verify wording and opinion type at the source.' : 'Text is extracted from the official PDF and may contain OCR or line-break artifacts. Verify wording in the original document. PDF page numbers are not reporter pinpoints.'}</p>
      {reader.text_status === 'short_record' && <p className="alert">This source record contains little text and may be a procedural entry. It may not provide reasoning for the research question.</p>}
      {reader.passages.length ? reader.passages.map((passage, index) => { const location = passageLocation(passage); return <section className="passage" key={index}><div className="passage-meta"><SourceLink url={location.url}>{location.label}</SourceLink><span>{passage.opinion_scope}{passage.opinion_id !== undefined ? ` · Opinion ${passage.opinion_id}` : ''}</span></div><blockquote>{passage.text}</blockquote></section>; }) : <p>No source passage is available for this result.</p>}
      <p className="source-limit">Subsequent treatment not checked. Source coverage and extracted text do not establish complete current law.</p>
    </article>}</dialog>
  </div>;
}

function CaseCard({ item, feedback, saved, busy, onInspect, onSave, onFeedback }: { item: CaseResult; feedback?: Feedback; saved: boolean; busy: boolean; onInspect: () => void; onSave: () => void; onFeedback: (value: Feedback | null) => void }) {
  const [reason, setReason] = useState(feedback?.reason ?? '');
  useEffect(() => { setReason(feedback?.reason ?? ''); }, [feedback?.reason]);
  return <article className="case-card panel"><div className="case-meta"><span>{item.court_name || item.court.toUpperCase()} · {item.decision_date}</span>{item.is_new && <span className="new-tag">New to this matter</span>}</div><h3><button onClick={onInspect}>{item.case_name}</button></h3><p className="citation">{item.citation}</p><p className="explanation">{item.explanation}</p><div className="case-actions"><button className="inspect-button" onClick={onInspect}>Inspect evidence ↗</button><button aria-pressed={saved} className={saved ? 'save-button saved' : 'save-button'} disabled={busy} onClick={onSave}>{saved ? '✓ Saved' : '＋ Save case'}</button></div><div className="feedback"><span className="feedback-label">Useful for this question?</span><div className="feedback-buttons"><button aria-pressed={feedback?.relevance === 'relevant'} disabled={busy} onClick={() => onFeedback({ relevance: 'relevant', reason })}>Relevant</button><button aria-pressed={feedback?.relevance === 'not_relevant'} disabled={busy} onClick={() => onFeedback({ relevance: 'not_relevant', reason })}>Not relevant</button>{feedback && <button className="clear-feedback" disabled={busy} onClick={() => onFeedback(null)}>Clear</button>}</div>{feedback && <form className="reason-form" onSubmit={event => { event.preventDefault(); onFeedback({ relevance: feedback.relevance, reason }); }}><label htmlFor={`reason-${item.id}`}>Optional feedback reason</label><textarea id={`reason-${item.id}`} rows={2} maxLength={1500} value={reason} onChange={e => setReason(e.target.value)} placeholder="Explain the factual or legal distinction that matters…"/><button disabled={busy || reason === feedback.reason} type="submit">Save reason</button>{feedback.relevance === 'not_relevant' && <p className="small muted">Without model assistance, this vote adjusts ordering; its reason is retained for review. Interpreting negative reasons requires model-assisted research.</p>}</form>}</div></article>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
