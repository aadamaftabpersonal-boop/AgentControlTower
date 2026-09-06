import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

interface SessionSummary {
  intent: string | null
  outcome: string | null
}

interface SessionDetail {
  index: number
  agent: string | null
  model: string | null
  files_touched: string[]
  summary: SessionSummary | null
  error: string | null
}

interface Checkpoint {
  checkpoint_id: string
  session_id: string | null
  agent_id: string | null
  timestamp: string | null
  prompt: string | null
  message: string | null
  is_task_checkpoint: boolean
  is_logs_only: boolean
  files_touched: string[]
  sessions: SessionDetail[]
  detail_level: 'list_only' | 'enriched'
  evidence_status: 'OK' | 'INSUFFICIENT EVIDENCE'
  evidence_notes: string[]
  unavailable_fields: string[]
}

interface Agent {
  agent_id: string | null
  session_id: string
  name: string | null
  objective: string | null
  status: string
  current_activity: string | null
  current_files: string[]
  latest_checkpoint_id: string
  updated_at: string | null
}

interface LiveState {
  status: 'OK' | 'WAITING FOR AGENT ACTIVITY'
  agents: Agent[]
  checkpoints: Checkpoint[]
  notes: string[]
}

interface ReconstructionPrompt {
  checkpoint_id: string
  prompt: string
  verification_status: string
  warnings: string[]
}

type ConnectionState = 'connecting' | 'live' | 'disconnected'

function withRepo(path: string, repo: string) {
  const url = new URL(path, API_BASE)
  if (repo.trim()) url.searchParams.set('repo', repo.trim())
  return url.toString()
}

function agentLabel(agent: Agent) {
  // agent_id is only populated once enrichment resolves a real agent name.
  // A list_only session isn't an error -- it's just not enriched yet -- so
  // this reads as a state, not a broken value.
  return agent.name ?? 'Live session (agent not yet resolved)'
}

function AgentNode({
  agent,
  checkpoints,
  onSelectCheckpoint,
}: {
  agent: Agent
  checkpoints: Checkpoint[]
  onSelectCheckpoint: (checkpointId: string) => void
}) {
  const sorted = [...checkpoints].sort((a, b) => (b.timestamp ?? '').localeCompare(a.timestamp ?? ''))

  return (
    <div className="agent-node">
      <div className="agent-node-header">
        <span className={`status-dot status-${agent.status.toLowerCase()}`} />
        <h2>{agentLabel(agent)}</h2>
        <span className="status-badge">{agent.status}</span>
      </div>
      <p className="agent-objective">{agent.objective ?? '(no objective captured)'}</p>
      <dl className="agent-meta">
        <dt>Current activity</dt>
        <dd>{agent.current_activity ?? '—'}</dd>
        <dt>Session</dt>
        <dd className="mono">{agent.session_id.slice(0, 12)}…</dd>
        <dt>Last update</dt>
        <dd>{agent.updated_at ? new Date(agent.updated_at).toLocaleString() : '—'}</dd>
      </dl>

      {sorted.length > 0 && (
        <div className="checkpoint-list">
          <h3>Checkpoints ({sorted.length})</h3>
          <ul>
            {sorted.map((cp) => (
              <li key={cp.checkpoint_id}>
                <button type="button" className="checkpoint-row" onClick={() => onSelectCheckpoint(cp.checkpoint_id)}>
                  <span className={`evidence-dot evidence-${cp.evidence_status === 'OK' ? 'ok' : 'gap'}`} />
                  <span className="checkpoint-message">{cp.message ?? '(no message)'}</span>
                  <span className="checkpoint-time">
                    {cp.timestamp ? new Date(cp.timestamp).toLocaleTimeString() : '—'}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function WaitingState() {
  return (
    <div className="waiting-state">
      <div className="pulse-dot" />
      <h2>WAITING FOR AGENT ACTIVITY</h2>
      <p>No pending checkpoints yet. Start a Claude Code session in an Entire-enabled repo to see it appear here.</p>
    </div>
  )
}

function RepoTargetForm({
  onLoad,
  loading,
  activeRepoLabel,
}: {
  onLoad: (target: string) => void
  loading: boolean
  activeRepoLabel: string
}) {
  const [value, setValue] = useState('')

  return (
    <form
      className="repo-form"
      onSubmit={(e) => {
        e.preventDefault()
        onLoad(value)
      }}
    >
      <input
        type="text"
        placeholder="Local folder path or git URL — leave empty for this repo"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={loading}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Loading…' : 'Load repo'}
      </button>
      <span className="active-repo-label">Showing: {activeRepoLabel}</span>
    </form>
  )
}

function CheckpointModal({
  checkpointId,
  repo,
  onClose,
}: {
  checkpointId: string
  repo: string
  onClose: () => void
}) {
  const [detail, setDetail] = useState<Checkpoint | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [reconstruction, setReconstruction] = useState<ReconstructionPrompt | null>(null)
  const [reconstructing, setReconstructing] = useState(false)
  const [reconstructError, setReconstructError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let cancelled = false
    setDetail(null)
    setDetailError(null)
    setReconstruction(null)
    setLoading(true)

    fetch(withRepo(`/api/checkpoints/${encodeURIComponent(checkpointId)}`, repo))
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => null)
          throw new Error(body?.detail ?? `Request failed with ${res.status}`)
        }
        return res.json() as Promise<Checkpoint>
      })
      .then((data) => {
        if (!cancelled) setDetail(data)
      })
      .catch((err) => {
        if (!cancelled) setDetailError(err instanceof Error ? err.message : 'Failed to load checkpoint')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [checkpointId, repo])

  const handleReconstruct = async () => {
    setReconstructing(true)
    setReconstructError(null)
    try {
      const res = await fetch(withRepo(`/api/checkpoints/${encodeURIComponent(checkpointId)}/reconstruction-prompt`, repo))
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail ?? `Request failed with ${res.status}`)
      }
      setReconstruction((await res.json()) as ReconstructionPrompt)
    } catch (err) {
      setReconstructError(err instanceof Error ? err.message : 'Failed to generate reconstruction prompt')
    } finally {
      setReconstructing(false)
    }
  }

  const handleCopy = async () => {
    if (!reconstruction) return
    await navigator.clipboard.writeText(reconstruction.prompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Checkpoint summary</h2>
          <button type="button" className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        {loading && <p className="loading">Loading checkpoint…</p>}
        {detailError && <div className="error-banner">{detailError}</div>}

        {detail && (
          <div className="checkpoint-detail">
            <dl className="agent-meta">
              <dt>Checkpoint ID</dt>
              <dd className="mono">{detail.checkpoint_id}</dd>
              <dt>Timestamp</dt>
              <dd>{detail.timestamp ? new Date(detail.timestamp).toLocaleString() : '—'}</dd>
              <dt>Message</dt>
              <dd>{detail.message ?? '—'}</dd>
              <dt>Detail level</dt>
              <dd>{detail.detail_level}</dd>
              <dt>Evidence status</dt>
              <dd className={detail.evidence_status === 'OK' ? '' : 'evidence-warning'}>{detail.evidence_status}</dd>
            </dl>

            {detail.evidence_notes.length > 0 && (
              <>
                <h3>Evidence notes</h3>
                <ul>
                  {detail.evidence_notes.map((n) => (
                    <li key={n}>{n}</li>
                  ))}
                </ul>
              </>
            )}

            {detail.sessions.map((session) => (
              <div key={session.index} className="session-summary">
                {session.agent && <p><strong>Agent:</strong> {session.agent}</p>}
                {session.summary?.intent && <p><strong>Intent:</strong> {session.summary.intent}</p>}
                {session.summary?.outcome && <p><strong>Outcome:</strong> {session.summary.outcome}</p>}
                {session.error && <p className="evidence-warning"><strong>Session error:</strong> {session.error}</p>}
              </div>
            ))}

            {detail.files_touched.length > 0 && (
              <>
                <h3>Files touched</h3>
                <ul className="mono">
                  {detail.files_touched.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </>
            )}

            {detail.unavailable_fields.length > 0 && (
              <p className="unavailable-note">
                Not available for this checkpoint: {detail.unavailable_fields.join(', ')}
              </p>
            )}

            <div className="modal-actions">
              <button type="button" onClick={handleReconstruct} disabled={reconstructing}>
                {reconstructing ? 'Generating…' : 'Generate reconstruction prompt'}
              </button>
            </div>

            {reconstructError && <div className="error-banner">{reconstructError}</div>}

            {reconstruction && (
              <div className="reconstruction-panel">
                <div className="reconstruction-header">
                  <span className="status-badge unverified">{reconstruction.verification_status}</span>
                  {reconstruction.warnings.length > 0 && (
                    <span className="reconstruction-warnings">{reconstruction.warnings.join(' · ')}</span>
                  )}
                </div>
                <textarea readOnly value={reconstruction.prompt} rows={14} />
                <button type="button" onClick={handleCopy}>
                  {copied ? 'Copied!' : 'Copy prompt'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function App() {
  const [live, setLive] = useState<LiveState | null>(null)
  const [connection, setConnection] = useState<ConnectionState>('connecting')
  const [error, setError] = useState<string | null>(null)
  const [repo, setRepo] = useState('')
  const [repoLoading, setRepoLoading] = useState(false)
  const [repoError, setRepoError] = useState<string | null>(null)
  const [selectedCheckpointId, setSelectedCheckpointId] = useState<string | null>(null)
  const sourceRef = useRef<EventSource | null>(null)

  const handleLoadRepo = async (target: string) => {
    setRepoLoading(true)
    setRepoError(null)
    try {
      // Validate the target against a fast non-streaming route first: an
      // EventSource that fails to open (wrong content-type, 4xx) can't
      // surface the actual error body to us, so a plain fetch here is what
      // lets a bad path/URL show a real message instead of a silent
      // "disconnected" badge.
      const response = await fetch(withRepo('/api/agents', target))
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? `Request failed with ${response.status}`)
      }
      setLive(null)
      setConnection('connecting')
      setRepo(target)
    } catch (err) {
      setRepoError(err instanceof Error ? err.message : 'Failed to load repo')
    } finally {
      setRepoLoading(false)
    }
  }

  useEffect(() => {
    const source = new EventSource(withRepo('/api/events', repo))
    sourceRef.current = source

    const applyState = (raw: string) => {
      try {
        setLive(JSON.parse(raw) as LiveState)
        setConnection('live')
        setError(null)
      } catch {
        // malformed frame — keep last-known-good state, don't invent data
      }
    }

    source.addEventListener('snapshot', (event) => applyState((event as MessageEvent).data))
    source.addEventListener('update', (event) => applyState((event as MessageEvent).data))
    source.addEventListener('error', (event) => {
      const msg = (event as MessageEvent).data
      if (msg) {
        try {
          setError(JSON.parse(msg).detail ?? 'Unknown backend error')
        } catch {
          setError('Unknown backend error')
        }
      }
    })
    source.onerror = () => setConnection('disconnected')
    source.onopen = () => setConnection((prev) => (prev === 'disconnected' ? 'live' : prev))

    return () => source.close()
  }, [repo])

  const checkpointsBySession = useMemo(() => {
    const map = new Map<string, Checkpoint[]>()
    for (const cp of live?.checkpoints ?? []) {
      const key = cp.session_id ?? cp.checkpoint_id
      const list = map.get(key) ?? []
      list.push(cp)
      map.set(key, list)
    }
    return map
  }, [live])

  return (
    <div className="control-tower">
      <header>
        <h1>Agent Control Tower</h1>
        <span className={`connection-badge connection-${connection}`}>
          {connection === 'live' && '● live'}
          {connection === 'connecting' && '◐ connecting…'}
          {connection === 'disconnected' && '○ disconnected — reconnecting'}
        </span>
      </header>

      <RepoTargetForm onLoad={handleLoadRepo} loading={repoLoading} activeRepoLabel={repo.trim() || '(this repo)'} />

      {repoError && <div className="error-banner">Couldn't load that repo: {repoError}</div>}
      {error && <div className="error-banner">Backend error: {error}</div>}

      <main>
        {live === null && connection === 'connecting' && <p className="loading">Connecting to control room…</p>}
        {live && live.status === 'WAITING FOR AGENT ACTIVITY' && <WaitingState />}
        {live && live.status === 'OK' && live.agents.length === 0 && <WaitingState />}
        {live && live.status === 'OK' && live.agents.length > 0 && (
          <div className="agent-grid">
            {live.agents.map((agent) => (
              <AgentNode
                key={agent.session_id}
                agent={agent}
                checkpoints={checkpointsBySession.get(agent.session_id) ?? []}
                onSelectCheckpoint={setSelectedCheckpointId}
              />
            ))}
          </div>
        )}
      </main>

      {selectedCheckpointId && (
        <CheckpointModal checkpointId={selectedCheckpointId} repo={repo} onClose={() => setSelectedCheckpointId(null)} />
      )}
    </div>
  )
}

export default App
