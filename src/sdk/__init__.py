import uvicorn

from core.logging import setup_logging, get_logger

logger = get_logger(__name__)


def serve(host="0.0.0.0", port=8000):
    """
    Serve the Frontier backend and frontend.
    """
    setup_logging()
    logger.info("Starting Frontier server on {}:{}", host, port)
    try:
        uvicorn.run("api.main:app", host=host, port=port, reload=True)
    except Exception as e:
        logger.opt(exception=True).error("Failed to start server")
