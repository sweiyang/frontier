import uvicorn

from core.logging import setup_logging, get_logger

logger = get_logger(__name__)


def serve(host="0.0.0.0", port=8000):
    """
    Serve the Conduit backend and frontend.
    """
    setup_logging()
    logger.info("Starting Conduit server on %s:%s", host, port)
    try:
        uvicorn.run("api.main:app", host=host, port=port, reload=True)
    except Exception as e:
        logger.error("Failed to start server", exc_info=True)
