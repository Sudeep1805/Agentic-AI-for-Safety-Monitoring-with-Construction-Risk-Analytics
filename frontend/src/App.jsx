import { useCallback, useEffect, useRef, useState } from 'react'
import { clearAuthToken, fetchImage, projectRequest, request, saveAuthToken } from './api'

const MAX_BYTES = 10 * 1024 * 1024
const supportedTypes = ['image/jpeg', 'image/png', 'image/webp']
const formatBytes = (size) => size >= 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(size / 1024))} KB`
const formatDate = (value) => new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const navItems = [
  ['overview', 'Overview', '▦'], ['projects', 'Projects', '⌂'], ['risks', 'Site Risks', '△'],
  ['incidents', 'Safety Incidents', '！'], ['compliance', 'Compliance', '✓'], ['insurance', 'Insurance', '◇'],
  ['agents', 'AI Agents', '✦'], ['alerts', 'Alerts', '♢'],
]
const projectDefaults = { name: '', code: '', description: '', construction_type: 'Residential', project_manager: '', site_address: '', city: '', state: '', pin_code: '', status: 'Planning', start_date: '', expected_completion_date: '', budget: '', number_of_workers: '', safety_officer: '', safety_notes: '' }
const projectFields = [
  ['name', 'Project Name', 'required'], ['code', 'Project Code', ''], ['description', 'Description', 'textarea'],
  ['construction_type', 'Construction Type', 'select:Residential|Commercial|Industrial|Road/Highway|Infrastructure|Other'], ['project_manager', 'Project Manager', ''],
  ['site_address', 'Site Address', 'required'], ['city', 'City', 'required'], ['state', 'State', 'required'], ['pin_code', 'PIN Code', ''],
  ['status', 'Status', 'select:Planning|Active|On Hold|Completed'], ['start_date', 'Start Date', 'date'], ['expected_completion_date', 'Expected Completion Date', 'date'],
  ['budget', 'Budget (INR)', 'number'], ['number_of_workers', 'Number of Workers', 'number'], ['safety_officer', 'Site Safety Officer', ''], ['safety_notes', 'Safety Notes', 'textarea'],
]
const demoProjects = [
  { name: 'Greenfield Residential Construction', location: 'Coimbatore, Tamil Nadu', status: 'Active' },
  { name: 'Smart Highway Infrastructure', location: 'Salem, Tamil Nadu', status: 'Active' },
  { name: 'Industrial Warehouse Development', location: 'Hosur, Tamil Nadu', status: 'Planning' },
]

function UploadIcon() { return <span aria-hidden="true" className="upload-glyph">↑</span> }

function AuthenticatedImage({ path, alt, className }) {
  const [src, setSrc] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    let objectUrl = ''
    setSrc('')
    setError('')
    fetchImage(path).then((next) => {
      objectUrl = next
      if (active) setSrc(next)
    }).catch((failure) => {
      if (active) setError(failure.message)
    })
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [path])

  if (error) return <div className="image-placeholder error-message" role="img" aria-label={`${alt} unavailable`}>{error}</div>
  return src ? <img className={className} src={src} alt={alt} /> : <div className={`image-placeholder ${className || ''}`} role="img" aria-label={`Loading ${alt}`} />
}

function AnalysisSummary({ item, compact = false }) {
  if (item.analysis_status === 'unavailable') {
    return <div className="analysis-unavailable" role="status"><strong>Analysis unavailable</strong><span>{item.analysis_message}</span></div>
  }

  return <div className={`analysis-summary ${compact ? 'compact' : ''}`} aria-label="Analysis results">
    <div className="analysis-status"><strong>Analysis completed</strong><span>{item.analysis_message}</span></div>
    <div className="analysis-metrics">
      <div><span>Risk score</span><strong>{item.risk_score ?? '—'}/100</strong></div>
      <div><span>Risk level</span><strong>{item.risk_level || '—'}</strong></div>
      <div><span>Detections</span><strong>{item.detections?.length ?? 0}</strong></div>
      <div><span>Hazards</span><strong>{item.hazard_count ?? 0}</strong></div>
    </div>
    {item.detections?.length ? <div className="detection-list"><h4>Detected objects</h4>{item.detections.map((detection, index) => <div className="detection-row" key={`${detection.class_id}-${index}`}><span>{detection.class_name}</span><strong>{(detection.confidence * 100).toFixed(1)}%</strong></div>)}</div> : <p className="zero-hazard">No configured hazards detected in this image.</p>}
    {item.hazards?.length ? <div className="hazard-list"><h4>Hazard explanations</h4>{item.hazards.map((hazard, index) => <div className="hazard-row" key={`${hazard.hazard}-${index}`}><strong>{hazard.hazard}</strong><span>{(hazard.confidence * 100).toFixed(1)}% confidence · {hazard.description}</span></div>)}</div> : null}
  </div>
}

function ProjectForm({ initial, onCancel, onSave, busy, error }) {
  const [values, setValues] = useState({ ...projectDefaults, ...initial })
  const [validation, setValidation] = useState('')
  function submit(event) {
    event.preventDefault()
    if (!values.name.trim() || !values.site_address.trim() || !values.city.trim() || !values.state.trim()) {
      setValidation('Project name, site address, city, and state are required.')
      return
    }
    if ((values.budget && Number(values.budget) < 0) || (values.number_of_workers && (!Number.isInteger(Number(values.number_of_workers)) || Number(values.number_of_workers) < 0))) {
      setValidation('Budget and number of workers must be non-negative numbers.')
      return
    }
    if (values.start_date && values.expected_completion_date && values.expected_completion_date < values.start_date) {
      setValidation('Expected completion date cannot be before the start date.')
      return
    }
    setValidation('')
    onSave({ ...values, budget: values.budget === '' ? null : Number(values.budget), number_of_workers: values.number_of_workers === '' ? null : Number(values.number_of_workers), code: values.code.trim() || null })
  }
  const update = (name, value) => setValues((current) => ({ ...current, [name]: value }))
  return <div className="project-modal-backdrop" role="presentation"><section className="project-modal panel" role="dialog" aria-modal="true" aria-labelledby="project-form-title">
    <div className="panel-header"><div><p className="eyebrow">SITE PORTFOLIO</p><h2 id="project-form-title">{initial ? 'Edit project' : 'Add project'}</h2></div><button type="button" className="text-button" onClick={onCancel}>Close</button></div>
    <form className="project-form" onSubmit={submit}><p className="form-section-title">Project information</p>
      {projectFields.map(([name, label, kind]) => <label key={name} className={`project-field ${kind === 'textarea' ? 'wide' : ''}`}>{label}{kind === 'required' && <span> *</span>}{kind === 'textarea' ? <textarea rows={3} value={values[name]} onChange={(e) => update(name, e.target.value)} /> : kind?.startsWith('select:') ? <select value={values[name]} onChange={(e) => update(name, e.target.value)}>{kind.slice(7).split('|').map((option) => <option key={option}>{option}</option>)}</select> : <input type={kind === 'date' ? 'date' : kind === 'number' ? 'number' : 'text'} min={kind === 'number' ? '0' : undefined} step={name === 'budget' ? '0.01' : undefined} value={values[name]} onChange={(e) => update(name, e.target.value)} />}</label>)}
      {(validation || error) && <div className="error-message" role="alert">{validation || error}</div>}
      <div className="project-form-actions"><button type="button" className="text-button" onClick={onCancel}>Cancel</button><button type="submit" className="primary-button compact" disabled={busy}>{busy ? 'Saving…' : 'Save Project'}</button></div>
    </form>
  </section></div>
}

function ProjectsPage({ user }) {
  const [savedProjects, setSavedProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!user) { setSavedProjects([]); return }
    projectRequest('').then((result) => setSavedProjects(result.items || [])).catch((failure) => setError(failure.message))
  }, [user])
  const save = async (values) => {
    setBusy(true); setError('')
    try {
      const result = await projectRequest(editing ? `/${editing.id}` : '', { method: editing ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) })
      setSavedProjects((current) => editing ? current.map((item) => item.id === result.id ? result : item) : [result, ...current])
      setFormOpen(false); setEditing(null); setSelectedProject(result)
    } catch (failure) { setError(failure.message) } finally { setBusy(false) }
  }
  async function remove(project) {
    if (!window.confirm(`Delete ${project.name}?`)) return
    setError('')
    try { await projectRequest(`/${project.id}`, { method: 'DELETE' }); setSavedProjects((current) => current.filter((item) => item.id !== project.id)); setSelectedProject(null) }
    catch (failure) { setError(failure.message) }
  }
  const rows = [...savedProjects, ...demoProjects.map((project) => ({ ...project, demo: true }))]
  return <section className="projects-page"><div className="page-heading projects-heading"><div><p className="eyebrow">SITE PORTFOLIO</p><h1>Projects</h1><p className="intro">Manage construction sites and active operations.</p></div><button className="primary-button compact" type="button" onClick={() => { setEditing(null); setError(''); setFormOpen(true) }}>+ Add Project</button></div>
    {error && !formOpen && <div className="error-message" role="alert">{error}</div>}
    <div className="projects-card panel"><div className="projects-table-wrap"><table className="projects-table"><thead><tr><th>NAME</th><th>LOCATION</th><th>STATUS</th><th>ACTIONS</th></tr></thead><tbody>{rows.length ? rows.map((project) => <tr key={project.id || project.name} onClick={() => setSelectedProject(project)}><td><button type="button" className="project-link">{project.name}</button>{project.demo && <small className="demo-label">Frontend demo</small>}</td><td>{project.location || `${project.city}, ${project.state}`}</td><td><span className={`project-status ${project.status.toLowerCase().replace(' ', '-')}`}>{project.status}</span></td><td>{project.demo ? <span className="muted small">Demo record</span> : <><button type="button" className="text-button" onClick={(e) => { e.stopPropagation(); setEditing(project); setFormOpen(true) }}>Edit</button><button type="button" className="text-button danger-button" onClick={(e) => { e.stopPropagation(); remove(project) }}>Delete</button></>}</td></tr>) : <tr><td colSpan="4"><div className="empty-state">No projects saved yet.</div></td></tr>}</tbody></table></div></div>
    {selectedProject && <div className="project-details panel"><div className="field-row"><div><p className="eyebrow">PROJECT DETAILS</p><h2>{selectedProject.name}</h2></div><button type="button" className="text-button" onClick={() => setSelectedProject(null)}>Close</button></div><p>{selectedProject.location || `${selectedProject.city}, ${selectedProject.state}`}</p>{selectedProject.demo ? <p className="muted">This is an illustrative frontend demo record and is not saved in MySQL.</p> : <div className="project-detail-grid">{projectFields.map(([name, label]) => selectedProject[name] != null && selectedProject[name] !== '' && <div key={name}><span>{label}</span><strong>{String(selectedProject[name])}</strong></div>)}</div>}</div>}
    {formOpen && <ProjectForm initial={editing} onCancel={() => { setFormOpen(false); setEditing(null) }} onSave={save} busy={busy} error={error} />}
  </section>
}

export default function App() {
  const [page, setPage] = useState(window.location.hash.slice(1) || 'overview')
  const [user, setUser] = useState(null)
  const [authMode, setAuthMode] = useState('login')
  const [authForm, setAuthForm] = useState({ email: '', password: '', full_name: '' })
  const [authMessage, setAuthMessage] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [file, setFile] = useState(null); const [preview, setPreview] = useState('')
  const [context, setContext] = useState(''); const [busy, setBusy] = useState(false)
  const [error, setError] = useState(''); const [saved, setSaved] = useState(null)
  const [history, setHistory] = useState([]); const [total, setTotal] = useState(0)
  const [historyError, setHistoryError] = useState(''); const [historyLoading, setHistoryLoading] = useState(true)
  const [connection, setConnection] = useState('checking'); const [dragging, setDragging] = useState(false)
  const [selected, setSelected] = useState(null); const fileInput = useRef(null)

  const navigate = (next) => { window.location.hash = next; setPage(next) }
  const refresh = useCallback(async () => {
    setHistoryLoading(true); setHistoryError('')
    const [health, uploads] = await Promise.allSettled([request('/health/ready'), request('/api/uploads')])
    setConnection(health.status === 'fulfilled' ? 'ready' : 'unavailable')
    if (uploads.status === 'fulfilled') { setHistory(uploads.value.items); setTotal(uploads.value.total) }
    else setHistoryError(uploads.reason.message)
    setHistoryLoading(false)
  }, [])
  useEffect(() => { const onHash = () => setPage(window.location.hash.slice(1) || 'overview'); window.addEventListener('hashchange', onHash); return () => window.removeEventListener('hashchange', onHash) }, [])
  useEffect(() => { refresh(); request('/api/auth/me').then((profile) => { if (profile?.email && profile?.full_name) setUser(profile) }).catch(() => {}) }, [refresh])
  useEffect(() => { if (!file) { setPreview(''); return }; const url = URL.createObjectURL(file); setPreview(url); return () => URL.revokeObjectURL(url) }, [file])

  function selectFile(next) {
    if (busy) return; setError(''); setSaved(null); setFile(null); if (!next) return
    if (!supportedTypes.includes(next.type) || !/\.(jpe?g|png|webp)$/i.test(next.name)) return setError('Choose a JPEG, PNG or WebP photograph.')
    if (!next.size || next.size > MAX_BYTES) return setError('Choose a non-empty image no larger than 10 MB.')
    setFile(next)
  }
  async function upload(event) {
    event.preventDefault(); if (!file || busy) return; setBusy(true); setError(''); setSaved(null)
    const form = new FormData(); form.append('file', file); if (context.trim()) form.append('site_context', context.trim())
    try { const result = await request('/api/uploads', { method: 'POST', body: form }); setSaved(result); setSelected(result); setFile(null); setContext(''); if (fileInput.current) fileInput.current.value = ''; await refresh() }
    catch (failure) { setError(failure.message) } finally { setBusy(false) }
  }
  async function submitAuth(event) {
    event.preventDefault(); setAuthBusy(true); setAuthMessage('')
    try { const result = await request(`/api/auth/${authMode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(authForm) }); saveAuthToken(result.access_token); setUser(result.user); setAuthForm({ email: '', password: '', full_name: '' }); setAuthMessage(`Welcome, ${result.user.full_name}.`) }
    catch (failure) { setAuthMessage(failure.message) } finally { setAuthBusy(false) }
  }
  async function signOut() { await request('/api/auth/logout', { method: 'POST' }).catch(() => {}); clearAuthToken(); setUser(null); navigate('overview') }

  const UploadPanel = () => <section className="panel upload-panel" aria-labelledby="upload-title">
    <div className="panel-header"><div><p className="eyebrow">NEW OBSERVATION</p><h2 id="upload-title">Upload a site image</h2></div><span className="tiny-tag">STILL PHOTOGRAPHS</span></div>
    <form onSubmit={upload} className="panel-body" aria-busy={busy}>
      <div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={(e) => { e.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(e) => { e.preventDefault(); setDragging(false); selectFile(e.dataTransfer.files[0]) }}>
        {preview ? <img className="preview" src={preview} alt="Selected construction site photograph" /> : <><span className="upload-icon"><UploadIcon /></span><p className="drop-title">Bring your site into view</p><p className="muted">Drop a photograph here, or browse your files.</p></>}
        <label className="choose-button"><input ref={fileInput} className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" aria-label="Choose site photograph" disabled={busy} onChange={(e) => selectFile(e.target.files[0])} />{file ? 'Change photograph' : 'Choose photograph'}</label><p className="muted small">JPEG, PNG or WebP · Up to 10 MB</p>
      </div>
      {file && <div className="file-info"><span>{file.name}</span><span>{formatBytes(file.size)}</span><button type="button" onClick={() => selectFile(null)}>Remove</button></div>}
      <div className="field-row"><label className="field-label" htmlFor="site-context">Site context <span>(optional)</span></label><span className="muted small">{context.length}/2,000</span></div>
      <textarea id="site-context" placeholder="Describe relevant details you know." maxLength={2000} value={context} disabled={busy} onChange={(e) => setContext(e.target.value)} rows={4} />
      {error && <div className="error-message" role="alert">{error}</div>}{saved && <div className="success-message" role="status"><strong>Upload saved successfully.</strong><AnalysisSummary item={saved} compact /></div>}
      <button className="primary-button" type="submit" disabled={!file || busy}>{busy ? 'Saving photograph…' : <><UploadIcon /> Save observation</>}</button>
    </form>
  </section>

  const History = () => <section className="panel history-panel" aria-labelledby="history-title"><div className="panel-header"><div><p className="eyebrow">OBSERVATION LOG</p><h2 id="history-title">Recent uploads <span className="count">{historyError ? '—' : total}</span></h2></div><button type="button" className="text-button" onClick={refresh} disabled={historyLoading}>{historyLoading ? 'Loading…' : 'Refresh history'}</button></div>
    {historyError ? <div className="panel-body"><div className="error-message" role="alert">{historyError}</div></div> : historyLoading && !history.length ? <p className="empty-state">Loading saved observations…</p> : !history.length ? <div className="empty-state"><span>□</span><h3>Your observation log starts here</h3><p>Saved photographs and their upload details will appear here.</p></div> : <div className="history-grid">{history.map((item) => <button type="button" key={item.id} className={`history-card ${selected?.id === item.id ? 'selected' : ''}`} onClick={() => setSelected(item)}><AuthenticatedImage path={item.image_url} alt={`Uploaded photograph: ${item.original_filename}`} /><div><strong>{item.original_filename}</strong><p>{formatDate(item.created_at)}</p><span>{item.width} × {item.height} · {formatBytes(item.size_bytes)}</span><small>{item.analysis_status === 'completed' ? `Analyzed · ${item.risk_level} risk` : 'Analysis unavailable'}</small></div></button>)}</div>}
    {selected && <div className="record-detail"><div className="field-row"><h3>Saved observation details</h3><button className="text-button" type="button" onClick={() => setSelected(null)}>Close details</button></div><div className="record-preview"><AuthenticatedImage path={selected.image_url} alt={`Uploaded photograph: ${selected.original_filename}`} /></div><p><strong>{selected.original_filename}</strong> · {formatDate(selected.created_at)}</p><p className="mt-2">{selected.site_context || 'No site context provided.'}</p><AnalysisSummary item={selected} /></div>}
  </section>

  function Placeholder({ title }) { return <section className="placeholder panel"><span className="placeholder-icon">✦</span><p className="eyebrow">COMING SOON</p><h2>{title}</h2><p className="muted">This workspace module is planned for a future release. No data is fabricated in this MVP.</p></section> }
  function Overview() { return <><span className="sr-only">Your observation log starts here</span><div className="page-heading"><div><p className="eyebrow">WORKSPACE OVERVIEW</p><h1>Good morning{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}.</h1><p className="intro">A clear view of your construction safety observations.</p></div><button className="primary-button compact" onClick={() => navigate('risks')}><UploadIcon /> New observation</button></div><div className="scope-note overview-note">{history.length ? <AnalysisSummary item={history[0]} compact /> : <p><strong>No analysis yet.</strong> Upload a site image to run YOLO detection.</p>}</div><div className="metric-grid"><div className="metric-card"><span>Total observations</span><strong>{total}</strong><small>All saved site images</small></div><div className="metric-card"><span>Completed analyses</span><strong>{history.filter((item) => item.analysis_status === 'completed').length}</strong><small>YOLO results available</small></div><div className="metric-card"><span>Site risks</span><strong>{history.reduce((sum, item) => sum + (item.hazard_count || 0), 0)}</strong><small>Detected hazards</small></div><div className="metric-card"><span>Open alerts</span><strong>—</strong><small>Coming soon</small></div></div><div className="dashboard-grid"><section className="panel quick-panel"><div className="panel-header"><div><p className="eyebrow">QUICK ACTIONS</p><h2>Keep your record current</h2></div></div><div className="quick-actions"><button onClick={() => navigate('risks')}><span>＋</span>Upload observation</button><button onClick={() => navigate('projects')}><span>⌂</span>Create project <small>Coming soon</small></button><button onClick={() => navigate('compliance')}><span>✓</span>Review compliance <small>Coming soon</small></button></div></section><section className="panel recent-panel"><div className="panel-header"><div><p className="eyebrow">LATEST ACTIVITY</p><h2>Recent observations</h2></div><button className="text-button" onClick={() => navigate('risks')}>View all</button></div>{history.slice(0, 3).map((item) => <button className="activity-row" key={item.id} onClick={() => { setSelected(item); navigate('risks') }}><span className="activity-dot" /><span><strong>{item.original_filename}</strong><small>{formatDate(item.created_at)}</small></span><b>{item.analysis_status === 'completed' ? `${item.risk_level} risk` : 'Unavailable'}</b></button>)}{historyError && <p className="panel-body"><span className="error-message" role="alert">{historyError}</span></p>}{!history.length && <p className="empty-state">Your observation log starts here</p>}</section></div><div className="overview-upload">{UploadPanel()}</div></> }

  const content = page === 'overview' ? <Overview /> : page === 'projects' ? <ProjectsPage user={user} /> : page === 'risks' ?  <><div className="page-heading"><div><p className="eyebrow">SITE RISKS</p><h1>Site observations</h1><p className="intro">Upload evidence and review the latest YOLO analysis.</p></div></div><div className="scope-note">{history.length ? <AnalysisSummary item={history[0]} compact /> : <p><strong>No analysis yet.</strong> Upload a site image to run YOLO detection.</p>}</div><div className="content-grid">{UploadPanel()}<History /></div></> : page === 'profile' ? <section className="panel profile-panel"><div className="panel-header"><div><p className="eyebrow">MY PROFILE</p><h2>Account details</h2></div></div><div className="panel-body">{user ? <><p className="profile-name">{user.full_name}</p><p className="profile-email">{user.email}</p><p className="muted mt-2">Authenticated workspace member.</p></> : <form className="auth-form" onSubmit={submitAuth}>{authMode === 'signup' && <input aria-label="Full name" placeholder="Full name" required value={authForm.full_name} onChange={(e) => setAuthForm({ ...authForm, full_name: e.target.value })} />}<input aria-label="Email" type="email" placeholder="Email" required value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })} /><input aria-label="Password" type="password" placeholder="Password (8+ characters)" minLength="8" required value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} /><button className="primary-button" disabled={authBusy}>{authBusy ? 'Working…' : authMode === 'login' ? 'Sign in' : 'Create account'}</button><button type="button" className="text-button" onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>{authMode === 'login' ? 'Need an account? Sign up' : 'Already registered? Sign in'}</button>{authMessage && <p role="alert">{authMessage}</p>}</form>}</div></section> : page === 'settings' ? <Placeholder title="Workspace settings" /> : <Placeholder title={navItems.find(([key]) => key === page)?.[1] || 'Workspace module'} />

  return <div className="app-shell"><aside className="sidebar"><a className="side-brand" href="#overview"><span className="brand-mark">S<span>R</span></span><span>CONSTRUCTION<br /><b>SAFETY WORKSPACE</b></span></a><nav aria-label="Main navigation"><p className="nav-label">WORKSPACE</p>{navItems.map(([key, label, icon]) => <a key={key} href={`#${key}`} className={page === key ? 'active' : ''} onClick={() => setPage(key)}><i>{icon}</i>{label}{['incidents', 'alerts'].includes(key) && <small>SOON</small>}</a>)}<p className="nav-label nav-spacer">ACCOUNT</p><a href="#profile" className={page === 'profile' ? 'active' : ''}><i>◎</i>My Profile</a><a href="#settings" className={page === 'settings' ? 'active' : ''}><i>⚙</i>Settings</a></nav><button className="side-signout" onClick={signOut}>↪ Sign Out</button></aside><main className="workspace"><header className="workspace-header"><div className="mobile-brand">SAFETY WORKSPACE</div><div className="connection"><i />{connection === 'ready' ? 'System connected' : connection === 'checking' ? 'Checking connection' : 'Setup required'}</div><div className="user-chip" onClick={() => navigate('profile')}><span>{user?.full_name?.[0]?.toUpperCase() || '?'}</span>{user ? user.full_name : 'Guest'}</div></header><div className="workspace-content">{content}</div></main></div>
}
