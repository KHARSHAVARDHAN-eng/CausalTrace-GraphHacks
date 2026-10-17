import React, { useState, useEffect } from 'react';
import { 
  IncidentSummary, 
  IncidentInvestigationResponse 
} from '../types';
import { fetchIncidents, fetchInvestigation, seedIncidentGraph } from '../services/api';
import { CausalGraphVisualizer } from './CausalGraphVisualizer';
import { 
  GitBranch, 
  Terminal, 
  AlertTriangle, 
  RefreshCw, 
  Layers, 
  Zap, 
  Database,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sparkles,
  Radio
} from 'lucide-react';

export const InvestigationWorkbench: React.FC = () => {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('');
  const [investigation, setInvestigation] = useState<IncidentInvestigationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [seeding, setSeeding] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showCypherProvenance, setShowCypherProvenance] = useState<boolean>(false);
  const [scenarioFilter, setScenarioFilter] = useState<'ALL' | 'EDGE_CASES' | 'HIGH_SEV'>('ALL');

  // Load available incidents on mount
  const loadIncidents = async () => {
    try {
      const data = await fetchIncidents();
      setIncidents(data);
      if (data.length > 0) {
        const urlParams = new URLSearchParams(window.location.search);
        const urlIncident = urlParams.get('incident') || urlParams.get('incident_id');
        if (urlIncident && data.some(i => i.id === urlIncident)) {
          setSelectedIncidentId(urlIncident);
        } else if (!selectedIncidentId) {
          setSelectedIncidentId(data[0].id);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch incidents';
      setError(msg);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, []);

  // Run investigation whenever selected incident changes
  const runInvestigation = async (incidentId: string) => {
    if (!incidentId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInvestigation(incidentId);
      setInvestigation(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Investigation failed';
      setError(msg);
      setInvestigation(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedIncidentId) {
      runInvestigation(selectedIncidentId);
    }
  }, [selectedIncidentId]);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await seedIncidentGraph();
      await loadIncidents();
      if (selectedIncidentId) {
        await runInvestigation(selectedIncidentId);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to seed graph';
      setError(msg);
    } finally {
      setSeeding(false);
    }
  };

  // Filter incidents for quick evaluation demo selection
  const isEdgeCase = (id: string) => (
    id.includes('abstain') || 
    id.includes('dns') || 
    id.includes('competing') || 
    id.includes('deep-chain') ||
    id.includes('cloud')
  );

  const edgeCaseCount = incidents.filter(i => isEdgeCase(i.id)).length;
  const highSevCount = incidents.filter(i => i.severity === 'SEV-1' || i.severity === 'CRITICAL').length;

  const filteredIncidents = incidents.filter(inc => {
    if (scenarioFilter === 'HIGH_SEV') return inc.severity === 'SEV-1' || inc.severity === 'CRITICAL';
    if (scenarioFilter === 'EDGE_CASES') return isEdgeCase(inc.id);
    return true;
  }).sort((a, b) => {
    if (scenarioFilter === 'EDGE_CASES') {
      if (a.id.includes('abstain')) return -1;
      if (b.id.includes('abstain')) return 1;
    }
    return 0;
  });

  useEffect(() => {
    if (filteredIncidents.length > 0 && !filteredIncidents.some(i => i.id === selectedIncidentId)) {
      setSelectedIncidentId(filteredIncidents[0].id);
    }
  }, [scenarioFilter, incidents]);

  const handleFilterClick = (filter: 'ALL' | 'EDGE_CASES' | 'HIGH_SEV') => {
    setScenarioFilter(filter);
    const subset = incidents.filter(inc => {
      if (filter === 'HIGH_SEV') return inc.severity === 'SEV-1' || inc.severity === 'CRITICAL';
      if (filter === 'EDGE_CASES') return isEdgeCase(inc.id);
      return true;
    }).sort((a, b) => {
      if (filter === 'EDGE_CASES') {
        if (a.id.includes('abstain')) return -1;
        if (b.id.includes('abstain')) return 1;
      }
      return 0;
    });
    if (subset.length > 0) {
      setSelectedIncidentId(subset[0].id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Workbench Header & Scenario Bar */}
      <div className="glass-card rounded-2xl p-5 border border-zinc-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-950/80 text-rose-400 border border-rose-800">
                LIVE INVESTIGATION WORKBENCH
              </span>
              <span className="text-xs text-zinc-400">• Native FalkorDB Cypher Engine</span>
            </div>
            <h2 className="text-xl font-bold text-white mt-1">
              Active Incident Causal Tracing
            </h2>
            <p className="text-xs text-zinc-400">
              Traversing dependency paths, temporal deployment markers, and distributed trace telemetry.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => runInvestigation(selectedIncidentId)}
              disabled={loading || !selectedIncidentId}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-teal-600 hover:bg-teal-500 text-white transition-colors disabled:opacity-50 shadow-sm shadow-teal-500/20"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Tracing Paths...' : 'Re-investigate'}
            </button>

            <button
              onClick={handleSeed}
              disabled={seeding}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-700 transition-colors disabled:opacity-50"
              title="Reset or re-seed the synthetic incident graph in FalkorDB"
            >
              <Database className="w-3.5 h-3.5 text-teal-400" />
              {seeding ? 'Seeding...' : 'Reset Graph'}
            </button>
          </div>
        </div>

        {/* Quick Filter & Selector Row */}
        <div className="pt-3 border-t border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-mono text-zinc-400 uppercase">Scenarios:</span>
            <button
              onClick={() => handleFilterClick('ALL')}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                scenarioFilter === 'ALL'
                  ? 'bg-zinc-800 text-teal-300 border border-zinc-600'
                  : 'bg-zinc-950 text-zinc-400 hover:text-zinc-200 border border-zinc-900'
              }`}
            >
              All Scenarios ({incidents.length})
            </button>
            <button
              onClick={() => handleFilterClick('EDGE_CASES')}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                scenarioFilter === 'EDGE_CASES'
                  ? 'bg-amber-950/80 text-amber-300 border border-amber-800'
                  : 'bg-zinc-950 text-zinc-400 hover:text-zinc-200 border border-zinc-900'
              }`}
            >
              Hard Edge Cases ({edgeCaseCount})
            </button>
            <button
              onClick={() => handleFilterClick('HIGH_SEV')}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                scenarioFilter === 'HIGH_SEV'
                  ? 'bg-rose-950/80 text-rose-300 border border-rose-800'
                  : 'bg-zinc-950 text-zinc-400 hover:text-zinc-200 border border-zinc-900'
              }`}
            >
              High Severity SEV-1 ({highSevCount})
            </button>
          </div>

          {filteredIncidents.length > 0 && (
            <div className="w-full sm:w-auto">
              <select
                value={selectedIncidentId}
                onChange={(e) => setSelectedIncidentId(e.target.value)}
                className="w-full sm:w-80 bg-zinc-900 border border-zinc-700 text-xs text-zinc-200 rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-teal-500 truncate"
              >
                {filteredIncidents.map((inc) => (
                  <option key={inc.id} value={inc.id}>
                    {inc.id} — {inc.title.substring(0, 32)}...
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Incident Summary Metadata Banner */}
        {investigation && !loading && (
          <div className="bg-zinc-950/80 rounded-xl p-4 border border-zinc-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-zinc-400 font-semibold">{investigation.incident_id}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  investigation.severity === 'CRITICAL'
                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                    : 'bg-amber-950 text-amber-300 border border-amber-800'
                }`}>
                  {investigation.severity}
                </span>
                {!investigation.has_sufficient_evidence && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/80 text-amber-300 border border-amber-600">
                    EXPLICIT ABSTENTION
                  </span>
                )}
              </div>
              <p className="font-medium text-white text-sm">{investigation.title}</p>
            </div>

            <div className="flex items-center gap-6 text-zinc-400">
              <div>
                <span className="text-[10px] uppercase block text-zinc-500">Affected Service</span>
                <span className="font-mono text-zinc-200">{investigation.affected_services.join(', ')}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase block text-zinc-500">Blast Radius</span>
                <span className="font-mono text-teal-400">{investigation.blast_radius_services.length} services</span>
              </div>
              <div>
                <span className="text-[10px] uppercase block text-zinc-500">Traversed Paths</span>
                <span className="font-mono text-zinc-200">{investigation.evidence_paths.length} paths</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ERROR STATE */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/80 text-xs text-rose-300 space-y-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
            <div className="space-y-1">
              <p className="font-bold text-rose-200 text-sm">FalkorDB Investigation Query Failed</p>
              <p className="font-mono text-[11px] text-rose-300/80">{error}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 pt-2 border-t border-rose-900/40">
            <button
              onClick={() => runInvestigation(selectedIncidentId)}
              className="px-3 py-1.5 rounded bg-rose-900/60 hover:bg-rose-800/80 text-rose-200 font-semibold text-xs transition-colors"
            >
              Retry Investigation
            </button>
            <button
              onClick={handleSeed}
              className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-300 font-semibold text-xs border border-zinc-700 transition-colors"
            >
              Re-seed FalkorDB Graph
            </button>
          </div>
        </div>
      )}

      {/* LOADING SKELETON STATE */}
      {loading && (
        <div className="space-y-4">
          <div className="glass-card rounded-2xl p-6 border border-zinc-800 space-y-4 animate-pulse">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 text-teal-400 animate-spin" />
              <div className="space-y-1">
                <div className="h-4 w-48 bg-zinc-800 rounded" />
                <div className="h-3 w-80 bg-zinc-900 rounded" />
              </div>
            </div>
            <div className="h-40 bg-zinc-950/80 rounded-xl border border-zinc-900 flex items-center justify-center">
              <span className="text-xs font-mono text-teal-400 animate-pulse">
                Traversing FalkorDB dependency graph & matching temporal telemetry windows...
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div className="h-32 bg-zinc-900/50 rounded-xl border border-zinc-800 animate-pulse" />
              <div className="h-32 bg-zinc-900/30 rounded-xl border border-zinc-800 animate-pulse" />
            </div>
            <div className="h-64 bg-zinc-900/30 rounded-xl border border-zinc-800 animate-pulse" />
          </div>
        </div>
      )}

      {/* EMPTY STATE (No Investigation Results) */}
      {!loading && !error && investigation && investigation.hypotheses.length === 0 && (
        <div className="glass-card rounded-2xl p-8 border border-zinc-800 text-center space-y-3">
          <Radio className="w-10 h-10 text-zinc-500 mx-auto animate-pulse" />
          <h3 className="text-base font-bold text-white">No Causal Hypotheses Discovered</h3>
          <p className="text-xs text-zinc-400 max-w-md mx-auto">
            The graph traversal did not find any deployments or alerts matching the temporal window for this incident.
          </p>
          <button
            onClick={handleSeed}
            className="mt-2 px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold"
          >
            Re-seed Synthetic Incidents
          </button>
        </div>
      )}

      {/* SUCCESS STATE — FULL INVESTIGATION DASHBOARD */}
      {!loading && !error && investigation && investigation.hypotheses.length > 0 && (
        <div className="space-y-6">
          {/* 1. Topological Graph Visualization */}
          <CausalGraphVisualizer
            evidencePaths={investigation.evidence_paths}
            hypotheses={investigation.hypotheses}
            affectedServices={investigation.affected_services}
            activeAlerts={investigation.active_alerts}
          />

          {/* 2. Decisive Explanation Card: "Why Rank #1 Was Selected" */}
          {investigation.top_hypothesis_justification && (
            <div className="glass-card rounded-2xl p-5 border border-teal-500/40 bg-teal-950/20 space-y-3 shadow-lg shadow-teal-500/5">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-teal-500 text-black flex items-center justify-center font-bold text-xs">
                    #1
                  </div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-teal-300" />
                    Decisive Causal Synthesis: Why Rank #1 Outranks Alternatives
                  </h3>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-900/60 text-teal-300 border border-teal-700">
                  Relative Confidence: {investigation.hypotheses[0].relative_confidence_pct}%
                </span>
              </div>

              <p className="text-xs text-zinc-200 leading-relaxed font-sans">
                {investigation.top_hypothesis_justification}
              </p>

              {/* Quick Discriminator Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-teal-900/40 text-[11px] font-mono">
                <div className="bg-zinc-950/60 p-2 rounded border border-teal-900/40">
                  <span className="text-[9px] uppercase text-zinc-500 block">Candidate Culprit</span>
                  <span className="text-teal-300 font-bold truncate block">{investigation.hypotheses[0].entity_id}</span>
                </div>
                <div className="bg-zinc-950/60 p-2 rounded border border-teal-900/40">
                  <span className="text-[9px] uppercase text-zinc-500 block">Target Service</span>
                  <span className="text-zinc-200 truncate block">{investigation.hypotheses[0].service_name}</span>
                </div>
                <div className="bg-zinc-950/60 p-2 rounded border border-teal-900/40">
                  <span className="text-[9px] uppercase text-zinc-500 block">Lead Time</span>
                  <span className="text-zinc-200 block">{Math.abs(investigation.hypotheses[0].time_delta_sec)}s before onset</span>
                </div>
                <div className="bg-zinc-950/60 p-2 rounded border border-teal-900/40">
                  <span className="text-[9px] uppercase text-zinc-500 block">Telemetry Match</span>
                  <span className="text-emerald-400 block font-semibold">
                    {investigation.hypotheses[0].corroborating_alerts.length} Alerts • {investigation.hypotheses[0].corroborating_logs.length} Logs
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 3. Main Grid: Ranked Hypotheses & Provenance Sidebar */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Columns: Ranked Root Cause Hypotheses */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Zap className="w-4 h-4 text-teal-400" />
                  Ranked Root-Cause Hypotheses ({investigation.hypotheses.length})
                </h3>
                <span className="text-xs text-zinc-400 font-mono">
                  Evidence-Weighted Ranking
                </span>
              </div>

              <div className="space-y-4">
                {investigation.hypotheses.map((hyp) => (
                  <div
                    key={hyp.hypothesis_id}
                    className={`rounded-2xl p-5 border transition-all ${
                      hyp.rank === 1
                        ? 'bg-zinc-900/90 border-teal-500/50 shadow-lg shadow-teal-500/5'
                        : hyp.is_distractor_or_competing
                        ? 'bg-zinc-900/50 border-amber-500/30'
                        : 'bg-zinc-900/30 border-zinc-800'
                    }`}
                  >
                    {/* Hypothesis Card Header */}
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                            hyp.rank === 1
                              ? 'bg-teal-500 text-black font-extrabold shadow-sm'
                              : 'bg-zinc-800 text-zinc-300'
                          }`}
                        >
                          #{hyp.rank}
                        </span>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="font-bold text-white text-sm font-mono">
                              {hyp.entity_id}
                            </h4>
                            <span className="text-xs text-zinc-400">on</span>
                            <span className="text-xs font-semibold text-zinc-200">
                              {hyp.service_name}
                            </span>
                          </div>
                          <span className="text-[11px] text-zinc-400">
                            {hyp.entity_type} • {Math.abs(hyp.time_delta_sec)}s before incident onset
                          </span>
                        </div>
                      </div>

                      {/* Score & Normalized Confidence */}
                      <div className="text-right shrink-0">
                        <div className="flex items-center gap-1.5 justify-end">
                          <span className="font-mono text-sm font-bold text-teal-300">
                            Score: {(hyp.score * 100).toFixed(1)}%
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                              hyp.confidence_level === 'HIGH'
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                : 'bg-amber-950 text-amber-400 border border-amber-800'
                            }`}
                          >
                            {hyp.confidence_level}
                          </span>
                        </div>
                        <div className="text-[10px] font-mono text-zinc-400 mt-0.5">
                          Relative Confidence: <strong className="text-zinc-200">{hyp.relative_confidence_pct}%</strong>
                        </div>
                        <div className="w-28 h-1.5 bg-zinc-800 rounded-full mt-1 overflow-hidden ml-auto">
                          <div
                            className={`h-full rounded-full ${
                              hyp.rank === 1 ? 'bg-teal-400' : 'bg-zinc-500'
                            }`}
                            style={{ width: `${Math.round(hyp.score * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Distractor Alert Callout */}
                    {hyp.is_distractor_or_competing && (
                      <div className="mb-3 p-3 rounded-xl bg-amber-950/30 border border-amber-600/40 text-xs text-amber-300 space-y-1">
                        <div className="flex items-center gap-1.5 font-semibold text-amber-200">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                          <span>Demoted Distractor / Asynchronous Branch Detected</span>
                        </div>
                        <p className="text-[11px] text-amber-300/90 leading-relaxed">
                          {hyp.distractor_reasoning}
                        </p>
                      </div>
                    )}

                    {/* Reasoning description */}
                    <p className="text-xs text-zinc-300 leading-relaxed mb-4">
                      {hyp.reasoning}
                    </p>

                    {/* Evidence Path pill */}
                    {hyp.evidence_path && (
                      <div className="mb-4 p-2.5 rounded-lg bg-zinc-950/70 border border-zinc-800/80 text-[11px] flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-1.5 text-zinc-400">
                          <GitBranch className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                          <span>Dependency Path:</span>
                          <span className="font-mono text-zinc-200">
                            {hyp.evidence_path.service_names.join(' → ')}
                          </span>
                        </div>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-medium ${
                            hyp.evidence_path.is_critical_path
                              ? 'bg-teal-950 text-teal-400 border border-teal-800'
                              : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                          }`}
                        >
                          {hyp.evidence_path.is_critical_path ? 'Critical Synchronous Path' : 'Non-Critical Branch'}
                        </span>
                      </div>
                    )}

                    {/* TRI-PANE EVIDENCE BREAKDOWN: Supporting, Contradictory, Missing */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4 pt-3 border-t border-zinc-800/60 text-xs">
                      {/* Supporting Evidence */}
                      <div className="bg-zinc-950/50 p-3 rounded-xl border border-emerald-900/30 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                          <span>Supporting Evidence ({hyp.supporting_evidence.length})</span>
                        </div>
                        <ul className="space-y-1 text-[11px] text-zinc-300">
                          {hyp.supporting_evidence.map((item, idx) => (
                            <li key={idx} className="flex items-start gap-1 leading-tight">
                              <span className="text-emerald-500 font-bold shrink-0">+</span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Contradictory Evidence */}
                      <div className="bg-zinc-950/50 p-3 rounded-xl border border-rose-900/30 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-rose-400 font-semibold text-[11px]">
                          <XCircle className="w-3.5 h-3.5 shrink-0" />
                          <span>Contradicting Evidence ({hyp.contradictory_evidence.length})</span>
                        </div>
                        {hyp.contradictory_evidence.length > 0 ? (
                          <ul className="space-y-1 text-[11px] text-zinc-300">
                            {hyp.contradictory_evidence.map((item, idx) => (
                              <li key={idx} className="flex items-start gap-1 leading-tight">
                                <span className="text-rose-500 font-bold shrink-0">-</span>
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span className="text-zinc-500 text-[11px] block italic">
                            No contradicting telemetry observed
                          </span>
                        )}
                      </div>

                      {/* Missing Evidence / Observability Gaps */}
                      <div className="bg-zinc-950/50 p-3 rounded-xl border border-indigo-900/30 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-indigo-400 font-semibold text-[11px]">
                          <HelpCircle className="w-3.5 h-3.5 shrink-0" />
                          <span>Missing Evidence ({hyp.missing_evidence.length})</span>
                        </div>
                        {hyp.missing_evidence.length > 0 ? (
                          <ul className="space-y-1 text-[11px] text-zinc-400">
                            {hyp.missing_evidence.map((item, idx) => (
                              <li key={idx} className="flex items-start gap-1 leading-tight">
                                <span className="text-indigo-400 font-bold shrink-0">?</span>
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span className="text-zinc-500 text-[11px] block italic">
                            Complete telemetry coverage
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Telemetry Detail Rows (Alerts & Error Logs) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs pt-2 border-t border-zinc-800/60">
                      <div>
                        <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">
                          Corroborating Alerts ({hyp.corroborating_alerts.length})
                        </span>
                        {hyp.corroborating_alerts.length > 0 ? (
                          <div className="space-y-1">
                            {hyp.corroborating_alerts.map((alt) => (
                              <div
                                key={alt.id}
                                className="font-mono text-[11px] text-zinc-300 flex items-center gap-1.5"
                              >
                                <span
                                  className={`w-1.5 h-1.5 rounded-full ${
                                    alt.severity === 'CRITICAL' ? 'bg-rose-400' : 'bg-amber-400'
                                  }`}
                                />
                                <span className="font-semibold text-zinc-200">{alt.name}</span>
                                <span className="text-zinc-500">
                                  ({alt.metric_name}={alt.metric_value})
                                </span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-zinc-500 text-[11px]">No firing alerts on service</span>
                        )}
                      </div>

                      <div>
                        <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">
                          Error Logs & Trace Evidence ({hyp.corroborating_logs.length})
                        </span>
                        {hyp.corroborating_logs.length > 0 ? (
                          <div className="space-y-1">
                            {hyp.corroborating_logs.map((log) => (
                              <div
                                key={log.id}
                                className="font-mono text-[11px] text-zinc-300 truncate"
                                title={log.message}
                              >
                                <span
                                  className={`px-1 rounded text-[9px] font-bold mr-1 ${
                                    log.level === 'FATAL'
                                      ? 'bg-rose-950 text-rose-400'
                                      : 'bg-amber-950 text-amber-400'
                                  }`}
                                >
                                  {log.level}
                                </span>
                                <span>{log.message}</span>
                                {log.trace_id && (
                                  <span className="text-teal-400 ml-1 text-[10px]">[{log.trace_id}]</span>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-zinc-500 text-[11px]">No error logs within window</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column: Epistemic Uncertainty & Cypher Audit Trail */}
            <div className="space-y-4">
              {/* Epistemic Uncertainty & Causality Limits */}
              <div className="glass-card rounded-2xl p-4 border border-amber-500/30 bg-amber-950/10 space-y-3">
                <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs">
                  <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Epistemic Uncertainty & Causality Limits</span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed">
                  {investigation.uncertainty.statement}
                </p>

                <div className="space-y-1.5 pt-2 border-t border-amber-900/30">
                  <span className="text-[10px] font-mono uppercase text-amber-300 tracking-wider">
                    Evidence Gaps / Unverified Factors:
                  </span>
                  <ul className="list-disc list-inside text-[11px] text-zinc-400 space-y-1">
                    {investigation.uncertainty.insufficient_evidence_flags.map((flag, idx) => (
                      <li key={idx} className="leading-tight">{flag}</li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-amber-900/30">
                  <span className="text-[10px] font-mono uppercase text-teal-300 tracking-wider">
                    Recommended Verification Actions:
                  </span>
                  <ul className="list-disc list-inside text-[11px] text-zinc-300 space-y-1">
                    {investigation.uncertainty.recommended_verification_steps.map((step, idx) => (
                      <li key={idx} className="leading-tight">{step}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Traversed Paths Visualizer List */}
              <div className="glass-card rounded-2xl p-4 border border-zinc-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-teal-400" />
                    Traversed Dependency Paths
                  </span>
                  <span className="text-[10px] font-mono text-zinc-400">
                    {investigation.evidence_paths.length} Chains
                  </span>
                </div>

                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {investigation.evidence_paths.map((p) => (
                    <div
                      key={p.path_id}
                      className="p-2.5 rounded-lg bg-zinc-950/70 border border-zinc-800/80 text-[11px] space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-zinc-300 font-medium">
                          {p.service_chain[0]} → {p.service_chain[p.service_chain.length - 1]}
                        </span>
                        <span
                          className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                            p.is_critical_path
                              ? 'text-teal-400 bg-teal-950/80 border border-teal-800'
                              : 'text-zinc-400 bg-zinc-900 border border-zinc-700'
                          }`}
                        >
                          {p.is_critical_path ? 'Critical' : 'Soft'}
                        </span>
                      </div>
                      <div className="font-mono text-[10px] text-zinc-400">
                        {p.service_names.join(' → ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cypher Query Provenance Accordion */}
              <div className="glass-card rounded-2xl p-4 border border-zinc-800 space-y-2">
                <button
                  onClick={() => setShowCypherProvenance(!showCypherProvenance)}
                  className="w-full flex items-center justify-between text-xs font-semibold text-zinc-300 hover:text-white transition-colors"
                >
                  <span className="flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-teal-400" />
                    Cypher Query Provenance ({investigation.cypher_query_provenance.length})
                  </span>
                  {showCypherProvenance ? (
                    <ChevronUp className="w-4 h-4 text-zinc-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-zinc-400" />
                  )}
                </button>

                {showCypherProvenance && (
                  <div className="space-y-2 pt-2 border-t border-zinc-800/80 max-h-80 overflow-y-auto">
                    {investigation.cypher_query_provenance.map((query, idx) => (
                      <div key={idx} className="bg-zinc-950 p-2.5 rounded font-mono text-[10px] text-teal-300 overflow-x-auto border border-zinc-800/80">
                        <pre><code>{query}</code></pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
