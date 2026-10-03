import os
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("dnd-governance-service")

app = FastAPI(
    title="WF-006 DND Governance Service",
    version="1.0.0",
    description="Dedicated microservice for verifying Do Not Disturb (DND) and opt-out status"
)

# In-memory mock suppression registry for the POC (can be backed by DB/Redis)
SUPPRESSED_PHONES = {
    "+19999999999",
    "+919999999999",
    "9999999999",
    "+15550000000"
}
SUPPRESSED_EMAILS = {
    "dnd@example.com",
    "blocked@example.com",
    "optout@domain.com"
}


class DNDCheckRequest(BaseModel):
    Contact_ID: str = Field(..., description="Master contact ID")
    phone: Optional[str] = None
    email: Optional[str] = None
    consent_status: Optional[str] = "PENDING"
    dnd_status: Optional[bool] = False


class DNDCheckResponse(BaseModel):
    Contact_ID: str
    is_dnd: bool
    action: str  # "ALLOW" or "BLOCK"
    reason: str
    checked_at: datetime


@app.get("/health")
def health():
    return {
        "service": "wf006-dnd-service",
        "status": "healthy",
        "suppression_registry_count": len(SUPPRESSED_PHONES) + len(SUPPRESSED_EMAILS),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/check-dnd", response_model=DNDCheckResponse, status_code=status.HTTP_200_OK)
def check_dnd(req: DNDCheckRequest):
    """
    Evaluates whether a contact is blocked by Do-Not-Disturb policy.
    Checks:
    1. Direct dnd_status flag = True
    2. Explicit opt-out / consent_status == 'REVOKED'
    3. Phone matches national/internal suppression registry
    4. Email matches suppression registry
    """
    logger.info(f"Checking DND status for Contact_ID={req.Contact_ID}, phone={req.phone}, email={req.email}")

    now = datetime.now(timezone.utc)

    # Rule 1: Explicit flag in payload
    if req.dnd_status is True:
        logger.warning(f"Contact {req.Contact_ID} flagged as DND in input payload.")
        return DNDCheckResponse(
            Contact_ID=req.Contact_ID,
            is_dnd=True,
            action="BLOCK",
            reason="Payload contains explicit dnd_status=true",
            checked_at=now
        )

    # Rule 2: Consent explicitly revoked
    if req.consent_status and req.consent_status.upper() == "REVOKED":
        logger.warning(f"Contact {req.Contact_ID} has consent_status=REVOKED.")
        return DNDCheckResponse(
            Contact_ID=req.Contact_ID,
            is_dnd=True,
            action="BLOCK",
            reason="Consent status is REVOKED by user",
            checked_at=now
        )

    # Rule 3: Phone number in suppression registry
    clean_phone = req.phone.strip() if req.phone else ""
    if clean_phone and clean_phone in SUPPRESSED_PHONES:
        logger.warning(f"Contact {req.Contact_ID} phone {clean_phone} found in DND registry.")
        return DNDCheckResponse(
            Contact_ID=req.Contact_ID,
            is_dnd=True,
            action="BLOCK",
            reason=f"Phone number {clean_phone} is listed in the DND suppression registry",
            checked_at=now
        )

    # Rule 4: Email address in suppression registry
    clean_email = req.email.strip().lower() if req.email else ""
    if clean_email and clean_email in SUPPRESSED_EMAILS:
        logger.warning(f"Contact {req.Contact_ID} email {clean_email} found in suppression list.")
        return DNDCheckResponse(
            Contact_ID=req.Contact_ID,
            is_dnd=True,
            action="BLOCK",
            reason=f"Email address {clean_email} is listed in suppression registry",
            checked_at=now
        )

    # Approved: Contact allowed to continue
    logger.info(f"Contact {req.Contact_ID} cleared DND verification.")
    return DNDCheckResponse(
        Contact_ID=req.Contact_ID,
        is_dnd=False,
        action="ALLOW",
        reason="Contact is verified and not on any suppression lists",
        checked_at=now
    )
