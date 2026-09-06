import { useEffect, useRef, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

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

interface AgentRegistryResult {
  status: 'OK' | 'WAITING FOR AGENT ACTIVITY'
  agents: Agent[]
  notes: string[]
}

type ConnectionState = 'connecting' | 'live' | 'disconnected'

function eventsUrl(repo: string) {
  const url = new URL('/api/events', API_BASE)
  if (repo.trim()) url.searchParams.set('repo', repo.trim())
  return url.toString()
}

function agentsUrl(repo: string) {
  const url = new URL('/api/agents', API_BASE)
  if (repo.trim()) url.searchParams.set('repo', repo.trim())
  return url.toString()
}

function AgentNode({ agent }: { agent: Agent }) {
  return (
    <div className="agent-node">
      <div className="agent-node-header">
        <span className={`status-dot status-${agent.status.toLowerCase()}`} />
        <h2>{agent.name ?? 'Unknown agent'}</h2>
        <span className="status-badge">{agent.status}</span>
      </div>
      <p className="agent-objective">{agent.objective ?? '(no objective captured)'}</p>
      <dl className="agent-meta">
        <dt>Current activity</dt>
        <dd>{agent.current_activity ?? '—'}</dd>
        <dt>Latest checkpoint</dt>
        <dd className="mono">{agent.latest_checkpoint_id.slice(0, 12)}…</dd>
        <dt>Session</dt>
        <dd className="mono">{agent.session_id.slice(0, 12)}…</dd>
        <dt>Last update</dt>
        <dd>{agent.updated_at ? new Date(agent.updated_at).toLocaleString() : '—'}</dd>
      </dl>
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

function App() {
  const [registry, setRegistry] = useState<AgentRegistryResult | null>(null)
  const [connection, setConnection] = useState<ConnectionState>('connecting')
  const [error, setError] = useState<string | null>(null)
  const [repo, setRepo] = useState('')
  const [repoLoading, setRepoLoading] = useState(false)
  const [repoError, setRepoError] = useState<string | null>(null)
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
      const response = await fetch(agentsUrl(target))
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? `Request failed with ${response.status}`)
      }
      setRegistry(null)
      setConnection('connecting')
      setRepo(target)
    } catch (err) {
      setRepoError(err instanceof Error ? err.message : 'Failed to load repo')
    } finally {
      setRepoLoading(false)
    }
  }

  useEffect(() => {
    const source = new EventSource(eventsUrl(repo))
    sourceRef.current = source

    const applyRegistry = (raw: string) => {
      try {
        setRegistry(JSON.parse(raw) as AgentRegistryResult)
        setConnection('live')
        setError(null)
      } catch {
        // malformed frame — keep last-known-good state, don't invent data
      }
    }

    source.addEventListener('snapshot', (event) => applyRegistry((event as MessageEvent).data))
    source.addEventListener('update', (event) => applyRegistry((event as MessageEvent).data))
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
        {registry === null && connection === 'connecting' && <p className="loading">Connecting to control room…</p>}
        {registry && registry.status === 'WAITING FOR AGENT ACTIVITY' && <WaitingState />}
        {registry && registry.status === 'OK' && registry.agents.length === 0 && <WaitingState />}
        {registry && registry.status === 'OK' && registry.agents.length > 0 && (
          <div className="agent-grid">
            {registry.agents.map((agent) => (
              <AgentNode key={agent.session_id} agent={agent} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
