import React from 'react';
import { HealthResponse } from '../types';
import { 
  Database, 
  Cpu, 
  Server, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle
} from 'lucide-react';

interface HealthStatusProps {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({
  health,
  loading,
  error,
  onRefresh,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
            <Server className="w-4 h-4 text-teal-400" />
            Infrastructure & Integration Readiness
          </h2>
          <p className="text-xs text-zinc-400">
            Real-time probe of FalkorDB graph connectivity, backend endpoints, and AI provider configuration.
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-700/80 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-teal-400' : ''}`} />
          {loading ? 'Probing...' : 'Re-check Status'}
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-3">
          <XCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Unable to Reach Backend Service</p>
            <p className="font-mono text-[11px] text-rose-300/80">{error}</p>
            <p className="text-zinc-400 mt-1">
              Ensure the FastAPI backend is running via <code className="text-teal-300 bg-zinc-900 px-1 py-0.5 rounded">uvicorn app.main:app --reload</code> on port 8000.
            </p>
          </div>
        </div>
      )}

      {/* Grid of 3 Diagnostic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: FastAPI Backend */}
        <div className="glass-card rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-indigo-400" />
                Backend API
              </span>
              {health ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
                  <CheckCircle2 className="w-3 h-3" />
                  Online
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                  <HelpCircle className="w-3 h-3" />
                  Unknown
                </span>
              )}
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Framework</span>
                <span className="font-mono text-zinc-200">FastAPI</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Version</span>
                <span className="font-mono text-zinc-200">{health?.version || '0.1.0'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Environment</span>
                <span className="font-mono text-zinc-200 uppercase">{health?.environment || 'development'}</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-zinc-800/60 text-[11px] text-zinc-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
            <span>Health Endpoint: <code className="text-teal-300">/api/health</code></span>
          </div>
        </div>

        {/* Card 2: FalkorDB Graph Engine */}
        <div className="glass-card rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-teal-400" />
                FalkorDB Graph
              </span>
              {health?.falkordb.connected ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
                  <CheckCircle2 className="w-3 h-3" />
                  Connected
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-950 text-amber-400 border border-amber-800">
                  <AlertTriangle className="w-3 h-3" />
                  Not Connected
                </span>
              )}
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Target Endpoint</span>
                <span className="font-mono text-zinc-200">
                  {health?.falkordb.host || 'localhost'}:{health?.falkordb.port || 6379}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Graph Name</span>
                <span className="font-mono text-zinc-200">{health?.falkordb.graph || 'causaltrace'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Query Language</span>
                <span className="font-mono text-teal-300 font-medium">Cypher</span>
              </div>
              {health?.falkordb.latency_ms !== undefined && health.falkordb.latency_ms !== null && (
                <div className="flex justify-between py-1 border-b border-zinc-800/60">
                  <span className="text-zinc-400">Ping Latency</span>
                  <span className="font-mono text-emerald-400 font-medium">{health.falkordb.latency_ms} ms</span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-zinc-800/60">
            <p className="text-[11px] text-zinc-400 leading-relaxed truncate" title={health?.falkordb.message}>
              {health?.falkordb.message || 'Run docker run -p 6379:6379 falkordb/falkordb'}
            </p>
          </div>
        </div>

        {/* Card 3: Modular AI Engine */}
        <div className="glass-card rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-violet-400" />
                AI Reasoning Engine
              </span>
              {health?.llm.has_api_key ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
                  <CheckCircle2 className="w-3 h-3" />
                  Ready
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                  Key Not Set
                </span>
              )}
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Provider</span>
                <span className="font-mono text-zinc-200 uppercase">{health?.llm.provider || 'openai'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Model</span>
                <span className="font-mono text-zinc-200">{health?.llm.model || 'gpt-4o-mini'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-400">Status</span>
                <span className="font-mono text-amber-300 font-medium capitalize">
                  {health?.llm.status || 'unconfigured'}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-zinc-800/60">
            <p className="text-[11px] text-zinc-400 leading-relaxed truncate" title={health?.llm.message}>
              {health?.llm.message || 'Configure LLM_API_KEY in backend/.env to activate'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
