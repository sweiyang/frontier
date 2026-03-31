import uvicorn

from core.logging import get_logger, setup_logging

logger = get_logger(__name__)


def serve(host="0.0.0.0", port=8000):
    """
    Serve the Frontier backend and frontend.
    """
    setup_logging()
    logger.info("Starting Frontier server on {}:{}", host, port)
    try:
        uvicorn.run("api.main:app", host=host, port=port, reload=True)
    except Exception:
        logger.opt(exception=True).error("Failed to start server")
