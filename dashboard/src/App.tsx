import React, { useCallback, useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import {
  fetchIncident,
  fetchIncidentGraph,
  fetchIncidents,
  runAnalysis,
} from './api/client';
import type {
  GraphData,
  GraphNode,
  IncidentDetail,
  IncidentSummary,
  RootCause,
} from './types';

const NODE_COLORS: Record<GraphNode['role'], string> = {
  root_cause: '#f85149',
  affected: '#d29922',
  healthy: '#6e7681',
};

function formatTimestamp(value: string | number): string {
  if (!value) return '—';
  if (typeof value === 'number') {
    return new Date(value * 1000).toLocaleString();
  }
  const parsed = Date.parse(value);
  if (!Number.isNaN(parsed)) {
    return new Date(parsed).toLocaleString();
  }
  return value;
}

function formatAnomalyTime(epoch: number | null | undefined): string {
  if (epoch == null) return '—';
  return new Date(epoch * 1000).toLocaleTimeString();
}

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div className="h-2 w-full rounded-full bg-gh-border overflow-hidden">
      <div
        className="h-full rounded-full bg-gradient-to-r from-gh-accent to-emerald-400 transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

function UploadModal({
  open,
  onClose,
  onSubmitted,
}: {
  open: boolean;
  onClose: () => void;
  onSubmitted: (id: string) => void;
}) {
  const [logPaths, setLogPaths] = useState(
    'tests/sample_logs/orders.log\ntests/sample_logs/payment.log',
  );
  const [metricsPath, setMetricsPath] = useState('tests/sample_logs/prom.json');
  const [since, setSince] = useState('2024-01-01T02:11:00');
  const [explain, setExplain] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const paths = logPaths
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    if (paths.length === 0) {
      setError('Enter at least one log file path.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const result = await runAnalysis({
        log_paths: paths,
        metrics_path: metricsPath.trim() || undefined,
        since: since.trim() || undefined,
        explain,
      });
      onSubmitted(result.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-lg rounded-lg border border-gh-border bg-gh-panel shadow-2xl">
        <div className="flex items-center justify-between border-b border-gh-border px-5 py-4">
          <h2 className="text-lg font-semibold text-white">Run New Analysis</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gh-muted hover:text-white"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4 px-5 py-4">
          <label className="block">
            <span className="mb-1 block text-sm text-gh-muted">
              Log file paths (one per line, relative to project root)
            </span>
            <textarea
              rows={3}
              value={logPaths}
              onChange={(e) => setLogPaths(e.target.value)}
              className="w-full rounded border border-gh-border bg-gh-bg px-3 py-2 font-mono text-sm"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm text-gh-muted">
              Metrics file path (JSON or CSV)
            </span>
            <input
              type="text"
              value={metricsPath}
              onChange={(e) => setMetricsPath(e.target.value)}
              className="w-full rounded border border-gh-border bg-gh-bg px-3 py-2 font-mono text-sm"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm text-gh-muted">
              Incident window start (optional)
            </span>
            <input
              type="text"
              placeholder="02:11 or 2024-01-01T02:11:00"
              value={since}
              onChange={(e) => setSince(e.target.value)}
              className="w-full rounded border border-gh-border bg-gh-bg px-3 py-2 text-sm"
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-gh-muted">
            <input
              type="checkbox"
              checked={explain}
              onChange={(e) => setExplain(e.target.checked)}
              className="rounded border-gh-border"
            />
            Generate AI explanation (requires ANTHROPIC_API_KEY)
          </label>
          {error && (
            <p className="rounded border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-300">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-gh-border px-4 py-2 text-sm text-gh-muted hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded bg-gh-accent px-4 py-2 text-sm font-medium text-gh-bg disabled:opacity-50"
            >
              {submitting ? 'Analyzing…' : 'Run Analysis'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RootCauseCard({ cause }: { cause: RootCause }) {
  const logCount = cause.evidence?.log_errors_before ?? 0;
  const anomalyAt = cause.evidence?.anomaly_at;

  return (
    <div className="rounded-lg border border-gh-border bg-gh-bg/60 p-4">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div>
          <span className="text-xs font-medium text-gh-muted">#{cause.rank}</span>
          <h3 className="text-base font-semibold text-white">{cause.service}</h3>
          <p className="text-xs text-gh-muted">{cause.metric}</p>
        </div>
        <span className="text-lg font-bold text-gh-accent">{cause.confidence_pct}%</span>
      </div>
      <ConfidenceBar value={cause.confidence_pct} />
      <dl className="mt-3 space-y-1 text-xs text-gh-muted">
        <div className="flex justify-between">
          <dt>Error logs before incident</dt>
          <dd className="text-white">{logCount}</dd>
        </div>
        <div className="flex justify-between">
          <dt>Anomaly timestamp</dt>
          <dd className="text-white">{formatAnomalyTime(anomalyAt)}</dd>
        </div>
      </dl>
    </div>
  );
}

function App() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const graphContainerRef = useRef<HTMLDivElement>(null);
  const [graphSize, setGraphSize] = useState({ width: 600, height: 400 });

  const loadIncidents = useCallback(async (selectLatest?: string) => {
    setListLoading(true);
    setError(null);
    try {
      const data = await fetchIncidents();
      setIncidents(data);
      if (selectLatest) {
        setSelectedId(selectLatest);
      } else {
        setSelectedId((current) => current ?? (data[0]?.id ?? null));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load incidents');
    } finally {
      setListLoading(false);
    }
  }, []);

  const loadIncidentDetail = useCallback(async (id: string) => {
    setDetailLoading(true);
    setError(null);
    try {
      const [detail, graph] = await Promise.all([
        fetchIncident(id),
        fetchIncidentGraph(id),
      ]);
      setIncident(detail);
      setGraphData(graph);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load incident');
      setIncident(null);
      setGraphData({ nodes: [], links: [] });
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  useEffect(() => {
    if (selectedId) {
      loadIncidentDetail(selectedId);
    }
  }, [selectedId, loadIncidentDetail]);

  useEffect(() => {
    const element = graphContainerRef.current;
    if (!element) return undefined;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setGraphSize({
          width: entry.contentRect.width,
          height: Math.max(280, entry.contentRect.height),
        });
      }
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const handleAnalysisComplete = async (id: string) => {
    await loadIncidents(id);
  };

  return (
    <div className="min-h-screen bg-gh-bg text-[#e6edf3]">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-gh-border bg-gh-panel px-4 py-3 sm:px-6">
        <h1 className="text-xl font-bold tracking-tight text-white">RCA-CLI Dashboard</h1>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="rounded-md bg-gh-accent px-4 py-2 text-sm font-semibold text-gh-bg hover:opacity-90"
        >
          Run New Analysis
        </button>
      </header>

      {error && (
        <div className="mx-4 mt-3 rounded border border-red-900/50 bg-red-950/40 px-4 py-2 text-sm text-red-300 sm:mx-6">
          {error}
        </div>
      )}

      <main className="flex flex-col gap-3 p-3 sm:p-4 lg:h-[calc(100vh-3.5rem)] lg:flex-row lg:gap-0 lg:p-0">
        {/* Left: Incident History */}
        <aside className="flex max-h-64 flex-col rounded-lg border border-gh-border bg-gh-panel lg:max-h-none lg:w-[25%] lg:rounded-none lg:border-b-0 lg:border-l-0 lg:border-t-0">
          <div className="border-b border-gh-border px-4 py-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gh-muted">
              Incident History
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {listLoading ? (
              <p className="px-4 py-6 text-sm text-gh-muted">Loading incidents…</p>
            ) : incidents.length === 0 ? (
              <p className="px-4 py-6 text-sm text-gh-muted">
                No incidents yet. Run an analysis to get started.
              </p>
            ) : (
              <ul>
                {incidents.map((item) => {
                  const active = item.id === selectedId;
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        onClick={() => setSelectedId(item.id)}
                        className={`w-full border-b border-gh-border px-4 py-3 text-left transition-colors ${
                          active
                            ? 'bg-gh-bg border-l-2 border-l-gh-accent'
                            : 'hover:bg-gh-bg/50'
                        }`}
                      >
                        <p className="text-xs text-gh-muted">
                          {formatTimestamp(item.timestamp)}
                        </p>
                        <p className="mt-1 font-medium text-white">{item.top_root_cause}</p>
                        <p className="text-sm text-gh-accent">{item.confidence_pct}% confidence</p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </aside>

        {/* Center: Causal Graph */}
        <section className="flex min-h-[320px] flex-col rounded-lg border border-gh-border bg-gh-panel lg:min-h-0 lg:w-[45%] lg:rounded-none lg:border-b-0 lg:border-t-0">
          <div className="border-b border-gh-border px-4 py-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gh-muted">
              Causal Graph
            </h2>
          </div>
          <div ref={graphContainerRef} className="relative flex-1 bg-[#0d1117]">
            {detailLoading ? (
              <div className="flex h-full items-center justify-center text-sm text-gh-muted">
                Loading graph…
              </div>
            ) : graphData.nodes.length === 0 ? (
              <div className="flex h-full items-center justify-center px-6 text-center text-sm text-gh-muted">
                {selectedId
                  ? 'No causal relationships detected for this incident.'
                  : 'Select an incident to view its causal graph.'}
              </div>
            ) : (
              <ForceGraph2D
                graphData={graphData}
                width={graphSize.width}
                height={graphSize.height}
                backgroundColor="#0d1117"
                nodeLabel="name"
                nodeColor={(node) => NODE_COLORS[(node as GraphNode).role] ?? NODE_COLORS.healthy}
                nodeRelSize={8}
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                linkWidth={(link) => 1 + (link.confidence ?? 0) * 6}
                linkColor={() => '#484f58'}
                cooldownTicks={80}
              />
            )}
          </div>
          <div className="flex flex-wrap gap-4 border-t border-gh-border px-4 py-2 text-xs text-gh-muted">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#f85149]" />
              Root cause
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#d29922]" />
              Affected
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#6e7681]" />
              Healthy
            </span>
          </div>
        </section>

        {/* Right: Root Cause Report */}
        <aside className="flex max-h-[28rem] flex-col rounded-lg border border-gh-border bg-gh-panel lg:max-h-none lg:w-[30%] lg:rounded-none lg:border-b-0 lg:border-r-0 lg:border-t-0">
          <div className="border-b border-gh-border px-4 py-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gh-muted">
              Root Cause Report
            </h2>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {detailLoading ? (
              <p className="text-sm text-gh-muted">Loading report…</p>
            ) : !incident ? (
              <p className="text-sm text-gh-muted">
                Select an incident to view ranked root causes.
              </p>
            ) : (
              <>
                {incident.root_causes.map((cause) => (
                  <RootCauseCard key={`${cause.rank}-${cause.service}`} cause={cause} />
                ))}
                {incident.llm_explanation && (
                  <div className="rounded-lg border border-emerald-900/40 bg-emerald-950/30 p-4">
                    <h3 className="mb-2 text-sm font-semibold text-emerald-300">
                      AI Explanation
                    </h3>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-emerald-100/90">
                      {incident.llm_explanation}
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </aside>
      </main>

      <UploadModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmitted={handleAnalysisComplete}
      />
    </div>
  );
}

export default App;
