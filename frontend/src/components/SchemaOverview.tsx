import React, { useState } from 'react';
import { 
  GitFork, 
  Layers, 
  Cpu, 
  AlertOctagon, 
  FileText, 
  ArrowRight, 
  Terminal,
  CheckCircle,
  Copy
} from 'lucide-react';
import { NodeSchemaDefinition, EdgeSchemaDefinition } from '../types';

const renderNodeIcon = (iconName: string) => {
  switch (iconName) {
    case 'AlertOctagon': return <AlertOctagon className="w-3.5 h-3.5" />;
    case 'Layers': return <Layers className="w-3.5 h-3.5" />;
    case 'Cpu': return <Cpu className="w-3.5 h-3.5" />;
    case 'GitFork': return <GitFork className="w-3.5 h-3.5" />;
    case 'FileText': return <FileText className="w-3.5 h-3.5" />;
    default: return <Layers className="w-3.5 h-3.5" />;
  }
};

const NODE_DEFINITIONS: NodeSchemaDefinition[] = [
  {
    label: ':Incident',
    iconName: 'AlertOctagon',
    color: 'text-rose-400 border-rose-500/30 bg-rose-950/30',
    description: 'Central investigation entity orchestrating telemetry, timeline, and root cause findings.',
    properties: [
      { name: 'id', type: 'STRING', example: '"inc-2026-0042"' },
      { name: 'title', type: 'STRING', example: '"Checkout latency spike"' },
      { name: 'severity', type: 'STRING', example: '"SEV-1"' },
      { name: 'status', type: 'STRING', example: '"INVESTIGATING"' },
      { name: 'started_at', type: 'INTEGER', example: '1792139000000' },
      { name: 'summary', type: 'STRING', example: '"High latency in downstream service"' },
    ],
  },
  {
    label: ':Service',
    iconName: 'Layers',
    color: 'text-teal-400 border-teal-500/30 bg-teal-950/30',
    description: 'Microservice or infrastructure component in the distributed system topology.',
    properties: [
      { name: 'id', type: 'STRING', example: '"svc-payment-api"' },
      { name: 'name', type: 'STRING', example: '"Payment API"' },
      { name: 'tier', type: 'STRING', example: '"tier-1"' },
      { name: 'team', type: 'STRING', example: '"checkout-core"' },
      { name: 'language', type: 'STRING', example: '"go"' },
      { name: 'status', type: 'STRING', example: '"DEGRADED"' },
    ],
  },
  {
    label: ':Deployment',
    iconName: 'GitFork',
    color: 'text-amber-400 border-amber-500/30 bg-amber-950/30',
    description: 'Deployment or configuration change event correlated with temporal anomaly windows.',
    properties: [
      { name: 'id', type: 'STRING', example: '"dep-84920"' },
      { name: 'version', type: 'STRING', example: '"v2.14.1"' },
      { name: 'commit_sha', type: 'STRING', example: '"7f3a91c"' },
      { name: 'timestamp', type: 'INTEGER', example: '1792138800000' },
      { name: 'status', type: 'STRING', example: '"SUCCESS"' },
      { name: 'deployed_by', type: 'STRING', example: '"github-actions"' },
    ],
  },
  {
    label: ':Alert',
    iconName: 'AlertOctagon',
    color: 'text-orange-400 border-orange-500/30 bg-orange-950/30',
    description: 'Firing metric threshold or health check anomaly attached to a specific service.',
    properties: [
      { name: 'id', type: 'STRING', example: '"alt-9012"' },
      { name: 'name', type: 'STRING', example: '"High5xxErrorRate"' },
      { name: 'severity', type: 'STRING', example: '"CRITICAL"' },
      { name: 'timestamp', type: 'INTEGER', example: '1792138950000' },
      { name: 'metric_name', type: 'STRING', example: '"http_requests_5xx"' },
      { name: 'metric_value', type: 'FLOAT', example: '14.8' },
    ],
  },
  {
    label: ':LogEvent',
    iconName: 'FileText',
    color: 'text-indigo-400 border-indigo-500/30 bg-indigo-950/30',
    description: 'Structured error log or stack trace event with distributed trace correlation.',
    properties: [
      { name: 'id', type: 'STRING', example: '"log-55102"' },
      { name: 'level', type: 'STRING', example: '"ERROR"' },
      { name: 'message', type: 'STRING', example: '"Database timeout in conn pool"' },
      { name: 'timestamp', type: 'INTEGER', example: '1792138960000' },
      { name: 'trace_id', type: 'STRING', example: '"trc-abc-123"' },
    ],
  },
];

const EDGE_DEFINITIONS: EdgeSchemaDefinition[] = [
  {
    type: 'DEPENDS_ON',
    source: ':Service',
    target: ':Service',
    description: 'Inter-service RPC/HTTP/queue dependencies with latency baselines and criticality flags.',
    properties: [
      { name: 'protocol', type: 'STRING' },
      { name: 'latency_p99_ms', type: 'FLOAT' },
      { name: 'critical', type: 'BOOLEAN' },
    ],
  },
  {
    type: 'DEPLOYED_TO',
    source: ':Deployment',
    target: ':Service',
    description: 'Maps deployment releases directly to the target operational service.',
    properties: [{ name: 'environment', type: 'STRING' }],
  },
  {
    type: 'TRIGGERED_ON',
    source: ':Alert',
    target: ':Service',
    description: 'Associates a triggered alert with the affected service node.',
  },
  {
    type: 'CORRELATED_WITH',
    source: ':Alert',
    target: ':Incident',
    description: 'Telemetry alerts associated with an incident by time window or heuristic.',
    properties: [
      { name: 'confidence', type: 'FLOAT' },
      { name: 'time_delta_sec', type: 'INTEGER' },
    ],
  },
  {
    type: 'AFFECTS',
    source: ':Incident',
    target: ':Service',
    description: 'Connects the incident to customer-facing or internal degraded services.',
  },
  {
    type: 'ROOT_CAUSE',
    source: ':Incident',
    target: ':Deployment | :Service | :Alert',
    description: 'Evidence-backed root cause relation ranked by graph traversal + LLM explanation.',
    properties: [
      { name: 'score', type: 'FLOAT' },
      { name: 'reasoning', type: 'STRING' },
      { name: 'evidence_chain', type: 'STRING' },
    ],
  },
];

const SAMPLE_CYPHER = `// CausalTrace: Upstream Deployment Change Traversal
MATCH (inc:Incident {id: $incident_id})-[:AFFECTS]->(target:Service)
MATCH (target)-[:DEPENDS_ON*0..3]->(upstream:Service)
MATCH (dep:Deployment)-[:DEPLOYED_TO]->(upstream)
WHERE dep.timestamp <= inc.started_at
  AND dep.timestamp >= (inc.started_at - 1800000)
RETURN upstream.name AS service, 
       dep.version AS version, 
       dep.timestamp AS deployed_at
ORDER BY dep.timestamp DESC;`;

export const SchemaOverview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'nodes' | 'edges' | 'cypher'>('nodes');
  const [copied, setCopied] = useState(false);

  const handleCopyCypher = () => {
    navigator.clipboard.writeText(SAMPLE_CYPHER);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="glass-card rounded-xl p-5 border border-zinc-800 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-800/80">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
            <GitFork className="w-4 h-4 text-teal-400" />
            FalkorDB Graph Schema Architecture
          </h3>
          <p className="text-xs text-zinc-400">
            Property graph model representing software topology, deployment changes, and incident evidence chains.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-1 bg-zinc-900 p-1 rounded-lg border border-zinc-800 text-xs">
          <button
            onClick={() => setActiveTab('nodes')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeTab === 'nodes'
                ? 'bg-zinc-800 text-teal-300 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Node Labels ({NODE_DEFINITIONS.length})
          </button>
          <button
            onClick={() => setActiveTab('edges')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeTab === 'edges'
                ? 'bg-zinc-800 text-teal-300 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Relationships ({EDGE_DEFINITIONS.length})
          </button>
          <button
            onClick={() => setActiveTab('cypher')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeTab === 'cypher'
                ? 'bg-zinc-800 text-teal-300 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Sample Cypher
          </button>
        </div>
      </div>

      {/* Tab 1: Nodes */}
      {activeTab === 'nodes' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {NODE_DEFINITIONS.map((node) => (
            <div
              key={node.label}
              className="bg-zinc-900/60 rounded-lg p-3.5 border border-zinc-800 hover:border-zinc-700 transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-semibold border ${node.color}`}>
                    {renderNodeIcon(node.iconName)}
                    {node.label}
                  </span>
                  <span className="text-[10px] text-zinc-400 uppercase font-mono">
                    {node.properties.length} props
                  </span>
                </div>
                <p className="text-xs text-zinc-300 mb-3 leading-relaxed">
                  {node.description}
                </p>
              </div>

              <div className="space-y-1 bg-zinc-950/70 p-2.5 rounded border border-zinc-800/80">
                <div className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider mb-1">
                  Properties
                </div>
                {node.properties.map((prop) => (
                  <div key={prop.name} className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-teal-400">{prop.name}</span>
                    <span className="text-zinc-400">{prop.type}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Edges */}
      {activeTab === 'edges' && (
        <div className="space-y-3">
          {EDGE_DEFINITIONS.map((edge) => (
            <div
              key={edge.type}
              className="bg-zinc-900/60 rounded-lg p-3.5 border border-zinc-800 hover:border-zinc-700 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded">
                    {edge.source}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-teal-400" />
                  <span className="font-mono text-xs font-semibold text-teal-300 bg-teal-950/60 border border-teal-800/40 px-2 py-0.5 rounded">
                    -[:{edge.type}]-&gt;
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-teal-400" />
                  <span className="font-mono text-xs text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded">
                    {edge.target}
                  </span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed pt-1">
                  {edge.description}
                </p>
              </div>

              {edge.properties && (
                <div className="shrink-0 flex items-center gap-1.5 flex-wrap">
                  <span className="text-[10px] text-zinc-400 uppercase font-mono">Props:</span>
                  {edge.properties.map((p) => (
                    <span key={p.name} className="px-1.5 py-0.5 bg-zinc-950 text-zinc-300 font-mono text-[10px] rounded border border-zinc-800">
                      {p.name}: <span className="text-teal-400">{p.type}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Cypher Query Patterns */}
      {activeTab === 'cypher' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-mono flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-teal-400" />
              Evidence Path Traversal Query (FalkorDB Cypher)
            </span>
            <button
              onClick={handleCopyCypher}
              className="flex items-center gap-1.5 text-xs text-zinc-300 bg-zinc-900 hover:bg-zinc-800 px-2.5 py-1 rounded border border-zinc-800 transition-colors"
            >
              {copied ? (
                <>
                  <CheckCircle className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy Cypher</span>
                </>
              )}
            </button>
          </div>
          <div className="bg-zinc-950 rounded-lg p-4 font-mono text-xs text-zinc-200 border border-zinc-800 overflow-x-auto">
            <pre className="text-zinc-300 leading-relaxed">
              <code>{SAMPLE_CYPHER}</code>
            </pre>
          </div>
          <div className="text-[11px] text-zinc-400 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
            <span>
              All graph traversals are executed natively via the FalkorDB Cypher engine with zero relational simulation.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
