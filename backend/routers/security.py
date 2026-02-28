"""Security router — STUB for CrowdStrike Falcon device health check."""

from fastapi import APIRouter
from models.schemas import SecurityCheckRequest, SecurityCheckResponse

router = APIRouter(tags=["security"])


@router.post("/security/check", response_model=SecurityCheckResponse)
async def security_check(body: SecurityCheckRequest):
    """
    STUB: Verify client endpoint health via CrowdStrike Falcon API.

    TODO: Before sensitive PII fields (SSN, DOB, etc.):
      1. Collect device signal from client (Falcon sensor / Zero Trust Assessment)
      2. Call CrowdStrike Falcon API to verify endpoint reputation
      3. If healthy → proceed with PII capture
      4. If compromised → block or require extra verification

    For MVP, always returns safe=True.
    """
    return SecurityCheckResponse(
        safe=True,
        message="STUB: CrowdStrike check passed (always returns safe in dev mode).",
    )
