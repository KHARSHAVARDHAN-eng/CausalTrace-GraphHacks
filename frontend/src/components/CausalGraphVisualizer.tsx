import React, { useState } from 'react';
import { 
  EvidencePath, 
  RootCauseHypothesis, 
  CorroboratingAlert 
} from '../types';
import { 
  Layers, 
  Zap, 
  AlertTriangle, 
  ArrowRight, 
  Cpu, 
  FileCode,
  Radio
} from 'lucide-react';

interface CausalGraphVisualizerProps {
  evidencePaths: EvidencePath[];
  hypotheses: RootCauseHypothesis[];
  affectedServices: string[];
  activeAlerts: CorroboratingAlert[];
}

export const CausalGraphVisualizer: React.FC<CausalGraphVisualizerProps> = ({
  evidencePaths,
  hypotheses,
  affectedServices,
  activeAlerts,
}) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const topHypothesis = hypotheses[0];
  const distractorHypothesis = hypotheses.find(h => h.is_distractor_or_competing);
  const symptomCount = affectedServices.length;

  return (
    <div className="glass-card rounded-2xl p-5 border border-zinc-800 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-teal-950/80 border border-teal-800 flex items-center justify-center text-teal-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              FalkorDB Causal Topology Map
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-teal-950 text-teal-300 border border-teal-800">
                Property Graph
              </span>
            </h3>
            <p className="text-[11px] text-zinc-400">
              Interactive visualization of traversed dependency chains for {symptomCount} affected symptom service{symptomCount > 1 ? 's' : ''} and candidate nodes.
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-[10px] font-mono text-zinc-400 flex-wrap">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 ring-2 ring-rose-500/20" /> Symptom Service
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-400 ring-2 ring-teal-400/20" /> Root Cause Culprit
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Competing Distractor
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-teal-500" /> Critical Sync Hop
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-zinc-600 border-t border-dashed" /> Async Soft Hop
          </span>
        </div>
      </div>

      {/* Visual Canvas Layout */}
      <div className="relative bg-zinc-950/90 rounded-xl p-6 border border-zinc-900 overflow-x-auto min-h-[240px] flex items-center justify-center">
        {/* Background Grid Accent */}
        <div 
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.15) 1px, transparent 0)`,
            backgroundSize: '24px 24px'
          }}
        />

        {evidencePaths.length === 0 ? (
          <div className="text-center space-y-2 py-8">
            <Radio className="w-8 h-8 text-zinc-600 mx-auto animate-pulse" />
            <p className="text-xs text-zinc-400">No upstream dependency hops registered for this incident.</p>
            <p className="text-[11px] text-zinc-500">Incident represents an isolated single-service or uninstrumented event.</p>
          </div>
        ) : (
          <div className="relative z-10 flex flex-col gap-6 w-full max-w-4xl py-2">
            {/* Primary Causal Path (Rank #1) */}
            {topHypothesis?.evidence_path && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] text-teal-400 font-mono">
                  <span className="flex items-center gap-1.5 font-semibold">
                    <Zap className="w-3.5 h-3.5" />
                    PRIMARY CAUSAL CHAIN (Rank #1: {topHypothesis.entity_id})
                  </span>
                  <span className="text-zinc-500">
                    {topHypothesis.evidence_path.hop_count} network hops • {topHypothesis.relative_confidence_pct}% relative confidence
                  </span>
                </div>

                <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap justify-between bg-zinc-900/60 p-4 rounded-xl border border-teal-500/30">
                  {topHypothesis.evidence_path.service_chain.map((serviceId, idx) => {
                    const isSymptom = idx === 0;
                    const isRoot = idx === topHypothesis.evidence_path!.service_chain.length - 1;
                    const serviceName = topHypothesis.evidence_path!.service_names[idx] || serviceId;
                    const hop = topHypothesis.evidence_path!.hops[idx];
                    const svcAlerts = activeAlerts.filter(a => a.service_id === serviceId);

                    return (
                      <React.Fragment key={serviceId}>
                        {/* Service Node Card */}
                        <div 
                          onClick={() => setSelectedNode(serviceId)}
                          className={`relative cursor-pointer transition-all p-3 rounded-xl border text-xs min-w-[170px] ${
                            isRoot
                              ? 'bg-teal-950/50 border-teal-400 ring-2 ring-teal-500/20 shadow-lg shadow-teal-500/10'
                              : isSymptom
                              ? 'bg-rose-950/40 border-rose-500/80 ring-2 ring-rose-500/20'
                              : 'bg-zinc-900 border-zinc-700 hover:border-zinc-500'
                          }`}
                        >
                          {/* Role Badge */}
                          <div className="flex items-center justify-between mb-1">
                            <span 
                              className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded uppercase ${
                                isRoot
                                  ? 'bg-teal-900 text-teal-300 border border-teal-700'
                                  : isSymptom
                                  ? 'bg-rose-900 text-rose-300 border border-rose-700'
                                  : 'bg-zinc-800 text-zinc-300'
                              }`}
                            >
                              {isRoot ? 'ROOT CAUSE CULPRIT' : isSymptom ? 'SYMPTOM SERVICE' : `HOP ${idx}`}
                            </span>
                            {isRoot && <Zap className="w-3.5 h-3.5 text-teal-300 animate-pulse" />}
                          </div>

                          <div className="font-bold text-white truncate text-xs" title={serviceName}>
                            {serviceName}
                          </div>
                          <div className="font-mono text-[10px] text-zinc-400 truncate">
                            {serviceId}
                          </div>

                          {/* Deployment Pill if Root */}
                          {isRoot && (
                            <div className="mt-2 pt-1.5 border-t border-teal-900/60 font-mono text-[10px] text-teal-200 flex items-center gap-1">
                              <FileCode className="w-3 h-3 text-teal-400" />
                              <span>{topHypothesis.entity_id}</span>
                            </div>
                          )}

                          {/* Corroborating Alerts Counter */}
                          {svcAlerts.length > 0 && (
                            <div className="mt-1.5 flex items-center gap-1 text-[10px] font-mono text-rose-300">
                              <AlertTriangle className="w-3 h-3 text-rose-400" />
                              <span>{svcAlerts.length} alert{svcAlerts.length > 1 ? 's' : ''}</span>
                            </div>
                          )}
                        </div>

                        {/* Connecting Hop Edge */}
                        {idx < topHypothesis.evidence_path!.service_chain.length - 1 && (
                          <div className="flex flex-col items-center justify-center px-1 text-center min-w-[70px]">
                            <span className="text-[9px] font-mono text-teal-400 bg-teal-950/80 px-1 rounded border border-teal-900 mb-0.5">
                              {hop?.protocol || 'gRPC'}
                            </span>
                            <div className="w-full flex items-center justify-center">
                              <div className="h-0.5 w-full bg-teal-400/80" />
                              <ArrowRight className="w-3.5 h-3.5 text-teal-400 shrink-0 -ml-1" />
                            </div>
                            <span className="text-[9px] font-mono text-zinc-500 mt-0.5">
                              {hop?.latency_p99_ms ? `${hop.latency_p99_ms}ms` : 'sync'}
                            </span>
                          </div>
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Competing Distractor Branch (if present) */}
            {distractorHypothesis && distractorHypothesis.evidence_path && (
              <div className="space-y-2 opacity-80 hover:opacity-100 transition-opacity">
                <div className="flex items-center justify-between text-[11px] text-amber-400 font-mono">
                  <span className="flex items-center gap-1.5 font-semibold">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    COMPETING ASYNCHRONOUS BRANCH (Demoted Distractor: {distractorHypothesis.entity_id})
                  </span>
                  <span className="text-zinc-500">
                    Non-Critical Path • {distractorHypothesis.relative_confidence_pct}% relative confidence
                  </span>
                </div>

                <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap justify-between bg-zinc-900/40 p-4 rounded-xl border border-amber-600/30">
                  {distractorHypothesis.evidence_path.service_chain.map((serviceId, idx) => {
                    const isSymptom = idx === 0;
                    const isDistractorTarget = idx === distractorHypothesis.evidence_path!.service_chain.length - 1;
                    const serviceName = distractorHypothesis.evidence_path!.service_names[idx] || serviceId;
                    const hop = distractorHypothesis.evidence_path!.hops[idx];

                    return (
                      <React.Fragment key={serviceId}>
                        <div 
                          onClick={() => setSelectedNode(serviceId)}
                          className={`p-3 rounded-xl border text-xs min-w-[170px] cursor-pointer ${
                            isDistractorTarget
                              ? 'bg-amber-950/30 border-amber-500/60'
                              : isSymptom
                              ? 'bg-rose-950/30 border-rose-500/50'
                              : 'bg-zinc-900/80 border-zinc-800'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded uppercase bg-amber-950 text-amber-300 border border-amber-800">
                              {isDistractorTarget ? 'COMPETING CANDIDATE' : isSymptom ? 'SYMPTOM' : 'SOFT HOP'}
                            </span>
                          </div>
                          <div className="font-bold text-zinc-200 truncate">{serviceName}</div>
                          <div className="font-mono text-[10px] text-zinc-400 truncate">{serviceId}</div>
                          {isDistractorTarget && (
                            <div className="mt-2 pt-1 border-t border-amber-900/50 font-mono text-[10px] text-amber-300/80 flex items-center gap-1">
                              <FileCode className="w-3 h-3 text-amber-400" />
                              <span>{distractorHypothesis.entity_id}</span>
                            </div>
                          )}
                        </div>

                        {idx < distractorHypothesis.evidence_path!.service_chain.length - 1 && (
                          <div className="flex flex-col items-center justify-center px-1 text-center min-w-[70px]">
                            <span className="text-[9px] font-mono text-amber-400/80 bg-zinc-900 px-1 rounded border border-amber-900/50 mb-0.5">
                              {hop?.protocol || 'HTTP'} (Async)
                            </span>
                            <div className="w-full flex items-center justify-center">
                              <div className="h-0.5 w-full bg-amber-500/50 border-t border-dashed border-amber-500" />
                              <ArrowRight className="w-3.5 h-3.5 text-amber-500/70 shrink-0 -ml-1" />
                            </div>
                            <span className="text-[9px] font-mono text-zinc-500 mt-0.5">soft</span>
                          </div>
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="p-3 bg-zinc-900/90 rounded-xl border border-zinc-700/80 text-xs flex items-center justify-between gap-4 animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-teal-400" />
            <div>
              <span className="font-bold text-white font-mono">{selectedNode}</span>
              <span className="text-zinc-400 ml-2">
                {topHypothesis?.evidence_path?.service_names[
                  topHypothesis.evidence_path.service_chain.indexOf(selectedNode)
                ] || 'Microservice Node'}
              </span>
            </div>
          </div>
          <button 
            onClick={() => setSelectedNode(null)}
            className="text-[11px] font-mono text-zinc-400 hover:text-white px-2 py-1 rounded bg-zinc-800"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
