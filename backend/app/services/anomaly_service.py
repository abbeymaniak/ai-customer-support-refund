"""Anomaly detection service for refund fraud velocity, value clusters, and duplicate claims."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import ClassVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refund_request import RefundRequest
from app.services.security_service import SecurityService


class AnomalyService:
    """Service evaluating customer refund anomalies and risk scoring."""

    # Anomaly detection thresholds
    VELOCITY_24H_THRESHOLD: ClassVar[int] = 3
    HIGH_VALUE_ITEM_THRESHOLD: ClassVar[float] = 200.0
    HIGH_VALUE_7D_SUM_THRESHOLD: ClassVar[float] = 500.0
    CONFLICTING_CLAIM_WINDOW_DAYS: ClassVar[int] = 30

    @classmethod
    async def evaluate_anomalies(
        cls,
        db: AsyncSession,
        customer_id: uuid.UUID,
        order_id: uuid.UUID,
        item_id: str | None,
        amount: float,
        customer_email: str | None = None,
        order_number: str | None = None,
        source_ip: str | None = None,
    ) -> tuple[float, list[str]]:
        """Evaluate refund request against velocity, high value cluster, and conflict rules.

        Returns (risk_score, anomaly_flags).
        """
        anomaly_flags: list[str] = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Velocity Check (requests in rolling 24 hours)
        cutoff_24h = now - timedelta(hours=24)
        stmt_velocity = select(func.count(RefundRequest.id)).where(
            RefundRequest.customer_id == customer_id,
            RefundRequest.created_at >= cutoff_24h,
        )
        velocity_count = (await db.execute(stmt_velocity)).scalar() or 0

        # Existing count + 1 (the current incoming request) >= threshold
        if (velocity_count + 1) >= cls.VELOCITY_24H_THRESHOLD:
            anomaly_flags.append("velocity_limit_exceeded")
            await SecurityService.record_security_event(
                db=db,
                event_type="velocity_limit_exceeded",
                endpoint="/api/refunds",
                severity="high",
                matched_pattern="velocity_threshold_breached",
                payload_preview=f"Customer submitted {velocity_count + 1} requests within 24 hours.",
                customer_email=customer_email,
                order_number=order_number,
                source_ip=source_ip,
            )

        # 2. High Value Cluster Check (individual item or 7-day cumulative sum)
        is_high_value = False
        high_value_reason = ""

        if amount > cls.HIGH_VALUE_ITEM_THRESHOLD:
            is_high_value = True
            high_value_reason = f"Single item amount ${amount:.2f} exceeds ${cls.HIGH_VALUE_ITEM_THRESHOLD:.2f} threshold."

        cutoff_7d = now - timedelta(days=7)
        stmt_7d_sum = select(func.coalesce(func.sum(RefundRequest.amount), 0.0)).where(
            RefundRequest.customer_id == customer_id,
            RefundRequest.created_at >= cutoff_7d,
            RefundRequest.decision != "denied",
        )
        past_7d_sum = float((await db.execute(stmt_7d_sum)).scalar() or 0.0)

        if (past_7d_sum + amount) > cls.HIGH_VALUE_7D_SUM_THRESHOLD:
            is_high_value = True
            high_value_reason = (
                f"Cumulative 7-day refund sum ${(past_7d_sum + amount):.2f} "
                f"exceeds ${cls.HIGH_VALUE_7D_SUM_THRESHOLD:.2f} limit."
            )

        if is_high_value:
            anomaly_flags.append("high_value_cluster")
            await SecurityService.record_security_event(
                db=db,
                event_type="high_value_cluster",
                endpoint="/api/refunds",
                severity="high",
                matched_pattern="high_value_cluster_detected",
                payload_preview=high_value_reason,
                customer_email=customer_email,
                order_number=order_number,
                source_ip=source_ip,
            )

        # 3. Conflicting Claim Check (duplicate item refund within 30 days)
        if item_id:
            cutoff_30d = now - timedelta(days=cls.CONFLICTING_CLAIM_WINDOW_DAYS)
            item_uuid = None
            try:
                item_uuid = uuid.UUID(str(item_id))
            except ValueError:
                pass

            from app.models.refund_item import RefundItem
            from sqlalchemy import or_

            conditions = [RefundRequest.item_id == str(item_id)]
            if item_uuid:
                conditions.append(RefundItem.order_item_id == item_uuid)

            stmt_conflict = (
                select(func.count(RefundRequest.id))
                .outerjoin(RefundItem, RefundRequest.id == RefundItem.refund_request_id)
                .where(
                    or_(*conditions),
                    RefundRequest.created_at >= cutoff_30d,
                    RefundRequest.decision != "denied",
                )
            )
            conflict_count = (await db.execute(stmt_conflict)).scalar() or 0

            if conflict_count > 0:
                anomaly_flags.append("conflicting_claim_detected")
                await SecurityService.record_security_event(
                    db=db,
                    event_type="conflicting_claim_detected",
                    endpoint="/api/refunds",
                    severity="high",
                    matched_pattern="duplicate_order_item_claim",
                    payload_preview=f"Item {item_id} already has an active or approved refund claim within {cls.CONFLICTING_CLAIM_WINDOW_DAYS} days.",
                    customer_email=customer_email,
                    order_number=order_number,
                    source_ip=source_ip,
                )

        # 4. Composite Risk Score Calculation
        risk_score = 0.0
        if "velocity_limit_exceeded" in anomaly_flags:
            risk_score += 0.4
        if "high_value_cluster" in anomaly_flags:
            risk_score += 0.3
        if "conflicting_claim_detected" in anomaly_flags:
            risk_score += 0.3

        composite_risk = min(1.0, round(risk_score, 2))
        return composite_risk, anomaly_flags
