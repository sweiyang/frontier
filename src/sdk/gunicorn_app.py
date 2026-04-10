"""Custom gunicorn application with worker lifecycle tracking for Prometheus metrics."""

import multiprocessing
import time

from gunicorn.app.base import BaseApplication

from core.logging import get_logger

logger = get_logger(__name__)

# Shared state for worker metrics (multiprocess-safe via Manager)
_manager = multiprocessing.Manager()
_worker_stats = _manager.dict()
_worker_stats["configured"] = 0
_worker_stats["alive"] = 0
_worker_stats["restarts"] = 0
_worker_stats["last_restart"] = 0.0


def get_worker_stats() -> dict:
    """Return a snapshot of current worker stats for the metrics endpoint."""
    return dict(_worker_stats)


class FrontierGunicornApp(BaseApplication):
    """Custom gunicorn application that loads the FastAPI app and tracks worker health."""

    def __init__(self, app_uri: str, options: dict = None):
        self.app_uri = app_uri
        self.options = options or {}
        super().__init__()

    def load_config(self):
        """Apply configuration from the options dict to gunicorn."""
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

        # Register lifecycle hooks
        self.cfg.set("on_starting", self._on_starting)
        self.cfg.set("post_worker_init", self._post_worker_init)
        self.cfg.set("child_exit", self._child_exit)
        self.cfg.set("on_exit", self._on_exit)

    def load(self):
        """Load the ASGI application."""
        # Import here to avoid circular imports
        from api.main import app

        return app

    # --- Lifecycle hooks ---

    @staticmethod
    def _on_starting(server):
        """Called just before the master process is initialized."""
        workers = server.app.cfg.settings["workers"].get()
        _worker_stats["configured"] = workers
        _worker_stats["alive"] = 0
        logger.info("Gunicorn starting with {} worker(s)", workers)

    @staticmethod
    def _post_worker_init(worker):
        """Called just after a worker has been initialized."""
        _worker_stats["alive"] = _worker_stats.get("alive", 0) + 1
        logger.info(
            "Worker {} initialized (pid: {}, alive: {})",
            worker.age,
            worker.pid,
            _worker_stats["alive"],
        )

    @staticmethod
    def _child_exit(server, worker):
        """Called when a worker process exits (crash, max_requests, or shutdown)."""
        alive = max(0, _worker_stats.get("alive", 1) - 1)
        _worker_stats["alive"] = alive
        _worker_stats["restarts"] = _worker_stats.get("restarts", 0) + 1
        _worker_stats["last_restart"] = time.time()
        logger.warning(
            "Worker exited (pid: {}, alive: {}, total restarts: {})",
            worker.pid,
            alive,
            _worker_stats["restarts"],
        )

    @staticmethod
    def _on_exit(server):
        """Called just before exiting gunicorn."""
        _worker_stats["alive"] = 0
        logger.info("Gunicorn shutting down")
