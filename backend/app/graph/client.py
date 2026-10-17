import time
import logging
from typing import Optional
from app.core.config import settings
from app.schemas.health import FalkorDBHealth

logger = logging.getLogger(__name__)


class FalkorDBClientManager:
    """Manages real connections to FalkorDB without mock fallback."""

    def __init__(self):
        self._driver = None
        self._graph = None

    def get_client(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize and return a real FalkorDB driver."""
        import falkordb
        h = host or settings.FALKORDB_HOST
        p = port if port is not None else settings.FALKORDB_PORT
        u = username if username is not None else settings.FALKORDB_USERNAME
        pwd = password if password is not None else settings.FALKORDB_PASSWORD

        return falkordb.FalkorDB(
            host=h,
            port=p,
            username=u if u else None,
            password=pwd if pwd else None,
        )

    def _get_driver(self):
        """Lazy-initialize singleton FalkorDB driver for the default app settings."""
        if self._driver is None:
            try:
                self._driver = self.get_client()
            except ImportError:
                logger.warning("falkordb package is not installed.")
                self._driver = None
            except Exception as e:
                logger.warning("Failed to initialize FalkorDB driver: %s", str(e))
                self._driver = None
        return self._driver

    def check_connection(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        graph_name: Optional[str] = None,
    ) -> FalkorDBHealth:
        """Probe real FalkorDB connectivity without inventing success.

        Executes a real Cypher query 'RETURN 1 AS ping' on the selected graph.
        Returns an honest status showing whether FalkorDB is reachable on the
        configured host and port.
        """
        target_host = host or settings.FALKORDB_HOST
        target_port = port if port is not None else settings.FALKORDB_PORT
        target_graph = graph_name or settings.FALKORDB_GRAPH

        try:
            # If default settings, reuse singleton driver; otherwise create client for target endpoint
            if host is None and port is None:
                driver = self._get_driver()
            else:
                driver = self.get_client(host=target_host, port=target_port)

            if driver is None:
                return FalkorDBHealth(
                    configured=bool(target_host),
                    connected=False,
                    host=target_host,
                    port=target_port,
                    graph=target_graph,
                    message="FalkorDB driver not initialized or package missing.",
                    latency_ms=None,
                )

            # Query the target graph to test genuine connectivity and measure latency
            t0 = time.perf_counter()
            graph = driver.select_graph(target_graph)
            res = graph.query("RETURN 1 AS ping")
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)

            return FalkorDBHealth(
                configured=True,
                connected=True,
                host=target_host,
                port=target_port,
                graph=target_graph,
                message="Connected to FalkorDB graph successfully.",
                latency_ms=latency_ms,
            )
        except Exception as exc:
            # Real error reported faithfully; no mock fallback
            return FalkorDBHealth(
                configured=True,
                connected=False,
                host=target_host,
                port=target_port,
                graph=target_graph,
                message=f"FalkorDB unreachable at {target_host}:{target_port}: {type(exc).__name__} ({str(exc)})",
                latency_ms=None,
            )

    def get_graph(self, graph_name: Optional[str] = None):
        """Retrieve target graph object if connected, or raise ConnectionError."""
        driver = self._get_driver()
        if driver is None:
            raise ConnectionError("FalkorDB client is not initialized.")
        target = graph_name or settings.FALKORDB_GRAPH
        return driver.select_graph(target)


# Singleton instance
graph_client = FalkorDBClientManager()
