"""Refund evaluation and processing API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.refund import RefundRequestResponse, RefundSubmissionPayload
from app.services.refund_service import RefundService

router = APIRouter()


@router.post(
    "/process",
    response_model=RefundRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and evaluate a refund request",
    description="Process a customer refund claim with two-phase policy evaluation and immutable audit logging.",
)
async def process_refund_request(
    payload: RefundSubmissionPayload,
    db: AsyncSession = Depends(get_db),
) -> RefundRequestResponse:
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
