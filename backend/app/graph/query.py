"""Graph Query Service executing native FalkorDB Cypher traversals.

Traces service topology, upstream critical/non-critical dependencies,
deployments, alerts, and log events with complete query provenance.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from app.graph.client import graph_client
from app.schemas.investigation import (
    DependencyHop,
    EvidencePath,
    CorroboratingAlert,
    CorroboratingLog,
)

logger = logging.getLogger(__name__)


class GraphQueryService:
    """Encapsulates all Cypher traversal operations for incident investigation."""

    def __init__(self):
        pass

    def _execute(self, query: str, params: Optional[Dict[str, Any]] = None, graph_name: Optional[str] = None):
        """Execute a Cypher query on the active FalkorDB graph."""
        graph = graph_client.get_graph(graph_name)
        return graph.query(query, params or {})

    def list_incidents(self) -> Tuple[List[Dict[str, Any]], str]:
        """Fetch all registered incidents."""
        cypher = """
        MATCH (i:Incident)
        RETURN i.id AS id, i.title AS title, i.severity AS severity,
               i.status AS status, i.started_at AS started_at, i.summary AS summary
        ORDER BY i.started_at DESC
        """
        res = self._execute(cypher)
        incidents = []
        for row in res.result_set:
            incidents.append({
                "id": row[0],
                "title": row[1],
                "severity": row[2],
                "status": row[3],
                "started_at": row[4],
                "summary": row[5],
            })
        return incidents, cypher.strip()

    def get_incident(self, incident_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """Retrieve core incident entity by ID."""
        cypher = """
        MATCH (i:Incident {id: $id})
        RETURN i.id AS id, i.title AS title, i.severity AS severity,
               i.status AS status, i.started_at AS started_at, i.summary AS summary
        """
        res = self._execute(cypher, {"id": incident_id})
        if not res.result_set:
            return None, cypher.strip()

        row = res.result_set[0]
        return {
            "id": row[0],
            "title": row[1],
            "severity": row[2],
            "status": row[3],
            "started_at": row[4],
            "summary": row[5],
        }, cypher.strip()

    def get_affected_services(self, incident_id: str) -> Tuple[List[Dict[str, Any]], str]:
        """Retrieve services directly marked as affected by the incident."""
        cypher = """
        MATCH (i:Incident {id: $id})-[:AFFECTS]->(s:Service)
        RETURN s.id AS id, s.name AS name, s.tier AS tier, s.team AS team, s.status AS status
        """
        res = self._execute(cypher, {"id": incident_id})
        services = []
        for row in res.result_set:
            services.append({
                "id": row[0],
                "name": row[1],
                "tier": row[2],
                "team": row[3],
                "status": row[4],
            })
        return services, cypher.strip()

    def get_all_service_names(self) -> Dict[str, str]:
        """Return a mapping of service ID to human readable name."""
        cypher = "MATCH (s:Service) RETURN s.id AS id, s.name AS name"
        res = self._execute(cypher)
        return {row[0]: row[1] for row in res.result_set}

    def traverse_upstream_paths(self, affected_service_id: str, max_depth: int = 4) -> Tuple[List[EvidencePath], str]:
        """Traverse upstream dependency chains from an affected service up to max_depth hops."""
        name_map = self.get_all_service_names()
        cypher = f"""
        MATCH path = (s:Service {{id: $sid}})-[:DEPENDS_ON*1..{max_depth}]->(target:Service)
        RETURN [node IN nodes(path) | node.id] AS chain,
               [rel IN relationships(path) | rel.critical] AS criticals,
               [rel IN relationships(path) | rel.protocol] AS protos,
               [rel IN relationships(path) | rel.latency_p99_ms] AS latencies
        """
        res = self._execute(cypher, {"sid": affected_service_id})
        paths = []

        for row in res.result_set:
            node_ids = row[0]
            critical_flags = row[1]
            protocols = row[2]
            latencies = row[3]

            hops = []
            for i in range(len(node_ids) - 1):
                hops.append(
                    DependencyHop(
                        source_service_id=node_ids[i],
                        target_service_id=node_ids[i + 1],
                        protocol=str(protocols[i]) if i < len(protocols) else "HTTP",
                        latency_p99_ms=float(latencies[i]) if i < len(latencies) and latencies[i] is not None else 0.0,
                        critical=bool(critical_flags[i]) if i < len(critical_flags) else True,
                    )
                )

            is_critical = all(h.critical for h in hops)
            service_names = [name_map.get(nid, nid) for nid in node_ids]

            paths.append(
                EvidencePath(
                    path_id=f"path-{node_ids[0]}->{node_ids[-1]}",
                    service_chain=node_ids,
                    service_names=service_names,
                    is_critical_path=is_critical,
                    hop_count=len(hops),
                    hops=hops,
                )
            )

        return paths, cypher.strip()

    def get_recent_deployments(
        self,
        service_ids: List[str],
        max_timestamp: int,
        window_ms: int = 3600000,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Find deployments to candidate services completed within the temporal window."""
        cypher = """
        MATCH (d:Deployment)-[:DEPLOYED_TO]->(s:Service)
        WHERE s.id IN $service_ids
          AND d.timestamp <= $max_ts
          AND d.timestamp >= ($max_ts - $window_ms)
        RETURN d.id AS id, d.version AS version, d.commit_sha AS commit_sha,
               d.timestamp AS timestamp, d.status AS status, d.deployed_by AS deployed_by,
               s.id AS service_id, s.name AS service_name
        ORDER BY d.timestamp DESC
        """
        res = self._execute(cypher, {
            "service_ids": service_ids,
            "max_ts": max_timestamp,
            "window_ms": window_ms,
        })

        deployments = []
        for row in res.result_set:
            deployments.append({
                "id": row[0],
                "version": row[1],
                "commit_sha": row[2],
                "timestamp": row[3],
                "status": row[4],
                "deployed_by": row[5],
                "service_id": row[6],
                "service_name": row[7],
            })
        return deployments, cypher.strip()

    def get_correlated_alerts(
        self,
        service_ids: List[str],
        incident_id: str,
        max_timestamp: Optional[int] = None,
        window_ms: int = 3600000,
    ) -> Tuple[List[CorroboratingAlert], str]:
        """Find active or correlated alerts on candidate services within the incident window."""
        cypher = """
        MATCH (a:Alert)-[:TRIGGERED_ON]->(s:Service)
        WHERE s.id IN $service_ids
          AND ($max_ts IS NULL OR (a.timestamp <= ($max_ts + 300000) AND a.timestamp >= ($max_ts - $window_ms)))
        RETURN a.id AS id, a.name AS name, a.severity AS severity,
               a.timestamp AS timestamp, a.metric_name AS metric_name,
               a.metric_value AS metric_value, s.id AS service_id
        ORDER BY a.timestamp ASC
        """
        res = self._execute(cypher, {
            "service_ids": service_ids,
            "max_ts": max_timestamp,
            "window_ms": window_ms,
        })
        alerts = []
        for row in res.result_set:
            alerts.append(
                CorroboratingAlert(
                    id=row[0],
                    name=row[1],
                    severity=row[2],
                    timestamp=row[3],
                    metric_name=row[4],
                    metric_value=float(row[5]),
                    service_id=row[6],
                )
            )
        return alerts, cypher.strip()

    def get_correlated_logs(
        self,
        service_ids: List[str],
        max_timestamp: int,
        window_ms: int = 3600000,
    ) -> Tuple[List[CorroboratingLog], str]:
        """Find error logs emitted by candidate services within the incident window."""
        cypher = """
        MATCH (l:LogEvent)-[:EMITTED_BY]->(s:Service)
        WHERE s.id IN $service_ids
          AND l.timestamp <= ($max_ts + 300000)
          AND l.timestamp >= ($max_ts - $window_ms)
        RETURN l.id AS id, l.level AS level, l.message AS message,
               l.timestamp AS timestamp, l.trace_id AS trace_id, s.id AS service_id
        ORDER BY l.timestamp DESC
        """
        res = self._execute(cypher, {
            "service_ids": service_ids,
            "max_ts": max_timestamp,
            "window_ms": window_ms,
        })
        logs = []
        for row in res.result_set:
            logs.append(
                CorroboratingLog(
                    id=row[0],
                    level=row[1],
                    message=row[2],
                    timestamp=row[3],
                    trace_id=row[4],
                    service_id=row[5],
                )
            )
        return logs, cypher.strip()


graph_query_service = GraphQueryService()
