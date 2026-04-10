"""Prometheus metrics: /metrics."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from core.db import db_project
from core.logging import get_logger
from core.metrics.metrics import (
    format_metrics_from_usage_data,
    format_monthly_metrics,
    format_worker_metrics,
    get_metrics_content_type,
)

logger = get_logger(__name__)

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes usage tracking metrics in Prometheus format.
    This endpoint is public (no authentication required) for Prometheus scraping.
    """
    try:
        all_projects_usage = await run_in_threadpool(db_project.get_all_projects_usage)
        monthly_usage = await run_in_threadpool(db_project.get_platform_monthly_usage)
        metrics_text = format_metrics_from_usage_data(all_projects_usage)
        metrics_text += "\n" + format_monthly_metrics(monthly_usage)
        worker_text = format_worker_metrics()
        if worker_text:
            metrics_text += "\n" + worker_text
        return Response(
            content=metrics_text,
            media_type=get_metrics_content_type(),
        )
    except Exception as e:
        logger.opt(exception=True).error("Failed to collect metrics")
        error_text = f"# ERROR: Failed to collect metrics: {str(e)}\n"
        return Response(
            content=error_text,
            media_type="text/plain",
            status_code=500,
        )
