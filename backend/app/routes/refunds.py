"""Refund evaluation and processing API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.refund import RefundRequestResponse, RefundSubmissionPayload
from app.services.refund_service import RefundService
from app.services.security_service import SecurityService

router = APIRouter()


@router.post(
    "",
    response_model=RefundRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and evaluate a refund request",
    description="Process a customer refund claim with perimeter validation, sanitization, and two-phase policy evaluation.",
)
@router.post(
    "/process",
    response_model=RefundRequestResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def process_refund_request(
    payload: RefundSubmissionPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RefundRequestResponse:
    # 1. Capture client IP address for security logging
    client_ip = request.client.host if request.client else None
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    endpoint_path = str(request.url.path)
    raw_explanation = payload.customer_explanation

    # 2. Check for suspicious XSS or script payloads
    if "<script" in raw_explanation.lower():
        await SecurityService.record_security_event(
            db=db,
            event_type="xss_payload_detected",
            severity="high",
            endpoint=endpoint_path,
            matched_pattern="script_tag_detected",
            payload_preview=raw_explanation,
            customer_email=payload.customer_email,
            order_number=payload.order_number,
            source_ip=client_ip,
        )

    # 3. Check for adversarial prompt injection phrases
    is_injection, matched_pattern = SecurityService.detect_prompt_injection(raw_explanation)
    if not is_injection:
        # Also check category and order number for injection markers
        is_injection, matched_pattern = SecurityService.detect_prompt_injection(
            payload.reason_category
        )

    if is_injection:
        await SecurityService.record_security_event(
            db=db,
            event_type="prompt_injection_attempt",
            severity="high",
            endpoint=endpoint_path,
            matched_pattern=matched_pattern,
            payload_preview=raw_explanation,
            customer_email=payload.customer_email,
            order_number=payload.order_number,
            source_ip=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request could not be processed due to invalid or unsupported content. Please rephrase your request.",
        )

    # 4. Sanitize explanation by removing dangerous HTML and stripping non-printable characters
    sanitized_explanation = SecurityService.sanitize_input(raw_explanation)
    if len(sanitized_explanation) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Customer explanation must contain at least 10 characters of valid text.",
        )

    # Pass sanitized text forward to business service and AI layer
    payload.customer_explanation = sanitized_explanation

    refund_service = RefundService(db)
    try:
        refund_record = await refund_service.process_refund(payload)
    except ValueError as val_err:
        error_msg = str(val_err)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
            ) from val_err
        if (
            "already been submitted" in error_msg.lower()
            or "flag_duplicate_claim" in error_msg.lower()
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_msg) from val_err
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg) from val_err

    return RefundRequestResponse.model_validate(refund_record)


@router.get(
    "/{id}",
    response_model=RefundRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get refund request detail",
    description="Retrieve full details, policy checks, and status of an evaluated refund request.",
)
async def get_refund_request_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RefundRequestResponse:
    refund_service = RefundService(db)
    refund_record = await refund_service.get_refund_request(id)
    if not refund_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Refund request with ID '{id}' not found.",
        )
    return RefundRequestResponse.model_validate(refund_record)
