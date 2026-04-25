from fastapi import APIRouter, Depends

from app.dependencies import get_bloom_report_service
from app.models.api import BloomReportResponse
from app.services.bloom_report_service import BloomReportService

router = APIRouter(prefix="/api/bloom-report", tags=["bloom-report"])


@router.get("/weekly", response_model=BloomReportResponse)
def get_weekly_bloom_report(
    service: BloomReportService = Depends(get_bloom_report_service),
) -> BloomReportResponse:
    return service.get_weekly_report()