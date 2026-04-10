import uvicorn

from core.config import get_config
from core.logging import get_logger, setup_logging

logger = get_logger(__name__)


def serve(host="0.0.0.0", port=8000):
    """
    Serve the Frontier backend and frontend.

    Dev mode (server.reload: true):  uvicorn with hot-reload, single worker.
    Production mode:                 gunicorn with UvicornWorker, heartbeat, respawning.
    """
    setup_logging()
    logger.info("Starting Frontier server on {}:{}", host, port)

    cfg = get_config()

    try:
        if cfg.server_reload:
            logger.info("Dev mode: uvicorn with hot-reload")
            uvicorn.run("api.main:app", host=host, port=port, reload=True)
        else:
            _serve_gunicorn(host, port, cfg)
    except Exception:
        logger.opt(exception=True).error("Failed to start server")


def _serve_gunicorn(host: str, port: int, cfg):
    """Launch gunicorn with UvicornWorker and config-driven settings."""
    from sdk.gunicorn_app import FrontierGunicornApp

    options = {
        "bind": f"{host}:{port}",
        "workers": cfg.server_workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "timeout": cfg.server_timeout,
        "graceful_timeout": cfg.server_graceful_timeout,
        "keepalive": cfg.server_keep_alive,
        "max_requests": cfg.server_max_requests,
        "max_requests_jitter": cfg.server_max_requests_jitter,
        "backlog": cfg.server_backlog,
        "accesslog": "-" if cfg.server_access_log else None,
        "errorlog": "-",
    }

    logger.info(
        "Production mode: gunicorn with {} worker(s), timeout={}s, max_requests={}",
        cfg.server_workers,
        cfg.server_timeout,
        cfg.server_max_requests,
    )

    app = FrontierGunicornApp("api.main:app", options)
    app.run()
