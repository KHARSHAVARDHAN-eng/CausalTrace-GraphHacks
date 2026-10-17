import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { HealthStatus } from './components/HealthStatus';
import { SchemaOverview } from './components/SchemaOverview';
import { InvestigationWorkbench } from './components/InvestigationWorkbench';
import { fetchHealth } from './services/api';
import { HealthResponse } from './types';
import { 
  Terminal, 
  Sparkles, 
  Layers, 
  ExternalLink,
  Database
} from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown communication error';
      setError(msg);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const systemStatus = error
    ? 'offline'
    : health
    ? health.status
    : 'initializing';

  return (
    <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100">
      <Header systemStatus={systemStatus} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Hero Banner / Project Mission */}
        <section className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-gradient-to-b from-zinc-900/80 via-zinc-900/40 to-zinc-950 p-6 md:p-8">
          <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-3 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-teal-950/80 text-teal-300 border border-teal-800/80">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                Graph Hacks Hackathon • Milestone 2: Causal Incident Investigation
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
                Causal Root-Cause Investigation via FalkorDB
              </h1>
              <p className="text-sm text-zinc-300 leading-relaxed">
                CausalTrace reconstructs distributed incident context by traversing service topologies, 
                recent deployments, correlated alerts, and logs in <strong>FalkorDB</strong>. By combining Cypher path 
                analytics with modular LLM reasoning, it isolates the probable root-cause path without guesswork.
              </p>
            </div>

            {/* Quick Architecture Badges */}
            <div className="flex flex-col gap-2 shrink-0 bg-zinc-950/80 p-4 rounded-xl border border-zinc-800 text-xs">
              <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                Architecture Blueprint
              </span>
              <div className="flex items-center gap-2 text-zinc-300">
                <Database className="w-4 h-4 text-teal-400" />
                <span>Primary Graph: <strong>FalkorDB (Cypher)</strong></span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <Sparkles className="w-4 h-4 text-violet-400" />
                <span>AI Reasoning: <strong>Modular LLM Interface</strong></span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>API Contract: <strong>FastAPI + Pydantic</strong></span>
              </div>
            </div>
          </div>
        </section>

        {/* Live Diagnostics: FalkorDB, Backend & LLM status */}
        <section>
          <HealthStatus
            health={health}
            loading={loading}
            error={error}
            onRefresh={loadHealth}
          />
        </section>

        {/* Real-Time Incident Investigation Workbench */}
        <section>
          <InvestigationWorkbench />
        </section>

        {/* Proposed Graph Schema Component */}
        <section>
          <SchemaOverview />
        </section>

        {/* Quick Local Setup Walkthrough */}
        <section className="glass-card rounded-xl p-5 border border-zinc-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-teal-400" />
              Quickstart: Launching Local FalkorDB & Backend
            </h3>
            <span className="text-xs text-zinc-400 font-mono">2-minute setup</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-zinc-900/70 p-4 rounded-lg border border-zinc-800 space-y-2">
              <div className="font-semibold text-teal-300 flex items-center gap-1.5">
                <span>1. Run FalkorDB (Docker)</span>
              </div>
              <p className="text-zinc-400">
                Launch a native FalkorDB container with the graph module enabled:
              </p>
              <pre className="bg-zinc-950 p-2.5 rounded font-mono text-[11px] text-zinc-300 overflow-x-auto border border-zinc-800/80">
                <code>docker run -p 6379:6379 -it --rm falkordb/falkordb</code>
              </pre>
            </div>

            <div className="bg-zinc-900/70 p-4 rounded-lg border border-zinc-800 space-y-2">
              <div className="font-semibold text-teal-300 flex items-center gap-1.5">
                <span>2. Start Backend & Probe Health</span>
              </div>
              <p className="text-zinc-400">
                Activate the virtualenv and start the FastAPI uvicorn daemon:
              </p>
              <pre className="bg-zinc-950 p-2.5 rounded font-mono text-[11px] text-zinc-300 overflow-x-auto border border-zinc-800/80">
                <code>source backend/.venv/bin/activate<br />uvicorn app.main:app --app-dir backend --reload --port 8000</code>
              </pre>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 py-6 px-6 text-center text-xs text-zinc-400 bg-zinc-950">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© 2026 CausalTrace — Built for Graph Hacks with FalkorDB & FastAPI.</p>
          <div className="flex items-center gap-4 text-zinc-400">
            <a
              href="https://github.com/FalkorDB/FalkorDB"
              target="_blank"
              rel="noreferrer"
              className="hover:text-teal-300 transition-colors flex items-center gap-1"
            >
              FalkorDB Docs
              <ExternalLink className="w-3 h-3" />
            </a>
            <span>•</span>
            <span>Version 0.1.0 (Scaffold)</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
