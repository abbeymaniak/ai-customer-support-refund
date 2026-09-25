"""Refund service handling refund lifecycle, policy evaluation, and AI integration."""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.engine import AIDecisionEngine
from app.ai.validators import enforce_policy_guardrails
from app.models.order import Order
from app.models.refund_item import RefundItem
from app.models.refund_request import RefundRequest
from app.schemas.refund import RefundSubmissionPayload
from app.services.anomaly_service import AnomalyService
from app.services.audit_service import AuditService
from app.services.customer_service import CustomerService
from app.services.policy_service import PolicyService
from app.services.security_service import SecurityService

logger = structlog.get_logger()


class RefundService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_refund_request(self, refund_id: uuid.UUID) -> RefundRequest | None:
        """Fetch refund request detail by UUID with related items and logs."""
        stmt = (
            select(RefundRequest)
            .where(RefundRequest.id == refund_id)
            .options(
                selectinload(RefundRequest.refund_items),
                selectinload(RefundRequest.audit_logs),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def process_refund(
        self,
        payload: RefundSubmissionPayload,
        client_ip: str | None = None,
    ) -> RefundRequest:
        """Execute two-phase refund evaluation, persist record, and log audit event."""
        # 1. Lookup Customer
        customer_service = CustomerService(self.db)
        customer = await customer_service.get_customer_by_email(
            payload.customer_email.strip().lower()
        )
        if not customer:
            raise ValueError(f"Customer with email '{payload.customer_email}' not found.")

        # 2. Lookup Order
        order_stmt = (
            select(Order)
            .where(Order.order_number == payload.order_number.strip())
            .options(selectinload(Order.order_items))
        )
        order = (await self.db.execute(order_stmt)).scalar_one_or_none()
        if not order:
            raise ValueError(f"Order '{payload.order_number}' not found.")
        if order.customer_id != customer.id:
            raise ValueError(f"Order '{payload.order_number}' not found.")

        # 3. Lookup Order Item
        order_item = None
        for item in order.order_items:
            if item.id == payload.item_id:
                order_item = item
                break
        if not order_item:
            raise ValueError(
                f"Item '{payload.item_id}' not found in order '{payload.order_number}'."
            )

        # 4. Quantity and Amounts
        quantity = payload.quantity if payload.quantity > 0 else 1
        refund_amount = payload.amount if payload.amount > 0 else (order_item.price * quantity)

        days_since_delivery = None
        if order.delivery_date:
            days_since_delivery = max(0, (datetime.utcnow() - order.delivery_date).days)

        # 5. Anomaly Detection and Risk Scoring (AC-2, AC-3, AC-4)
        risk_score, anomaly_flags = await AnomalyService.evaluate_anomalies(
            db=self.db,
            customer_id=customer.id,
            order_id=order.id,
            item_id=str(order_item.id),
            amount=refund_amount,
            customer_email=customer.email,
            order_number=order.order_number,
            source_ip=client_ip,
        )

        has_prior_refund_for_item = "conflicting_claim_detected" in anomaly_flags

        # 6. Phase 1: Deterministic Policy Evaluation
        policy_service = PolicyService()
        rule_result = policy_service.evaluate_rules(
            days_since_delivery=days_since_delivery,
            total_refund_amount=refund_amount,
            is_final_sale=order_item.is_final_sale,
            category=order_item.category,
            reason=payload.reason_category,
            item_condition=payload.item_condition,
            customer_return_rate=customer.return_rate,
            customer_refunds_count=customer.refunds_count,
            has_prior_refund_for_item=has_prior_refund_for_item,
        )

        error_context = None
        final_decision = rule_result.preliminary_decision
        final_confidence = (
            0.95 if rule_result.is_approved else (1.0 if rule_result.is_denied else 0.5)
        )
        final_reasoning = "; ".join(rule_result.reasons)
        llm_audit_data = {}

        # 7. Phase 2: AI Contextual Evaluation with Fallback and Guardrails (AC-5, AC-6)
        ai_engine = AIDecisionEngine(self.db)
        try:
            ai_res = await ai_engine.evaluate_refund_request(
                customer_info={
                    "email": customer.email,
                    "total_spent": customer.total_spent,
                    "orders_count": customer.orders_count,
                    "refunds_count": customer.refunds_count,
                    "return_rate": customer.return_rate,
                    "risk_score": customer.risk_score,
                },
                order_info={
                    "order_number": order.order_number,
                    "days_since_delivery": days_since_delivery,
                    "item_name": order_item.product_name,
                    "item_price": order_item.price,
                    "is_final_sale": order_item.is_final_sale,
                    "category": order_item.category,
                },
                request_info={
                    "requested_amount": refund_amount,
                    "reason": payload.reason_category,
                    "condition": payload.item_condition,
                    "explanation": payload.customer_explanation,
                },
                policy_info={
                    "matched_rules": rule_result.matched_rules,
                    "triggered_red_flags": rule_result.triggered_red_flags,
                    "policy_summary": policy_service.format_for_prompt(),
                },
            )

            # Post-evaluation deterministic guardrail interceptor (AC-6)
            guardrail_decision, guardrail_reason, was_overridden = (
                policy_service.enforce_guardrails(
                    ai_decision=ai_res.get("decision", "Escalated"),
                    is_final_sale=order_item.is_final_sale,
                    days_since_delivery=days_since_delivery,
                    reason=payload.reason_category,
                    category=order_item.category,
                )
            )

            if was_overridden:
                final_decision = "Denied"
                final_confidence = 1.0
                final_reasoning = (
                    guardrail_reason
                    or "Non-negotiable policy guardrail enforced: Request is denied."
                )
                llm_audit_data = {
                    "decision": "Denied",
                    "confidence_score": 1.0,
                    "explanation": final_reasoning,
                    "guardrails_triggered": ["OVERRIDE_HARD_DENIAL"],
                    "telemetry": ai_res.get("telemetry", {}),
                }
                rule_result.matched_rules.append("RULE_GUARDRAIL_OVERRIDE")
                await SecurityService.record_security_event(
                    db=self.db,
                    event_type="policy_guardrail_breach_prevented",
                    endpoint="/api/refunds",
                    severity="high",
                    matched_pattern="hard_policy_guardrail_override",
                    payload_preview="AI approved claim on ineligible item. Overridden to Denied.",
                    customer_email=customer.email,
                    order_number=order.order_number,
                    source_ip=client_ip,
                )
            elif anomaly_flags:
                final_decision = "Escalated"
                final_confidence = 0.5
                final_reasoning = f"Claim flagged for human supervisor review due to detected anomalies: {', '.join(anomaly_flags)}."
                llm_audit_data = {
                    "decision": "Escalated",
                    "confidence_score": 0.5,
                    "explanation": final_reasoning,
                    "anomaly_flags": anomaly_flags,
                    "guardrails_triggered": ["ANOMALY_ESCALATION"],
                    "telemetry": ai_res.get("telemetry", {}),
                }
            else:
                validated_ai = enforce_policy_guardrails(
                    preliminary_decision=rule_result.preliminary_decision,
                    ai_decision=ai_res,
                    rule_reasons=rule_result.reasons,
                    customer_risk_score=customer.risk_score,
                    customer_return_rate=customer.return_rate,
                )
                final_decision = validated_ai["decision"]
                final_confidence = validated_ai["confidence_score"]
                final_reasoning = validated_ai["explanation"]
                llm_audit_data = {
                    "decision": validated_ai["decision"],
                    "confidence_score": validated_ai["confidence_score"],
                    "explanation": validated_ai["explanation"],
                    "policy_citations": validated_ai.get("policy_citations", []),
                    "matched_rules": validated_ai.get("matched_rules", []),
                    "audit_notes": validated_ai.get("audit_notes", ""),
                    "suggested_action": validated_ai.get("suggested_action", "process_refund"),
                    "guardrails_triggered": validated_ai.get("guardrails_triggered", []),
                    "telemetry": ai_res.get("telemetry", {}),
                }

        except Exception as ai_err:
            logger.warning("ai_evaluation_outage_fallback_active", error=str(ai_err))
            error_context = {
                "error_type": type(ai_err).__name__,
                "message": str(ai_err),
                "timestamp": datetime.utcnow().isoformat(),
            }
            await SecurityService.record_security_event(
                db=self.db,
                event_type="ai_service_outage",
                endpoint="/api/refunds",
                severity="medium",
                matched_pattern="ai_provider_error",
                payload_preview=str(ai_err)[:300],
                customer_email=customer.email,
                order_number=order.order_number,
                source_ip=client_ip,
            )
            if rule_result.is_denied:
                final_decision = "Denied"
                final_confidence = 1.0
                final_reasoning = f"Policy rule check: {'; '.join(rule_result.reasons)}"
            elif anomaly_flags:
                final_decision = "Escalated"
                final_confidence = 0.5
                final_reasoning = f"Claim flagged for human supervisor review due to detected anomalies: {', '.join(anomaly_flags)}."
            else:
                final_decision = "Escalated"
                final_confidence = 0.5
                final_reasoning = (
                    "Automated AI evaluation is temporarily unavailable. "
                    "Your claim has been routed to human support for expedited review."
                )
            llm_audit_data = {
                "fallback": True,
                "error": str(ai_err),
                "deterministic_decision": rule_result.preliminary_decision,
            }

        # 8. Persist RefundRequest
        refund_req = RefundRequest(
            id=uuid.uuid4(),
            request_number=f"REF-{uuid.uuid4().hex[:10].upper()}",
            customer_id=customer.id,
            order_id=order.id,
            item_id=str(order_item.id),
            item_name=order_item.product_name,
            amount=refund_amount,
            total_refund_amount=refund_amount,
            currency=order.currency,
            reason_category=payload.reason_category,
            customer_explanation=payload.customer_explanation,
            status=final_decision.lower(),
            decision=final_decision,
            decision_reason=final_reasoning,
            confidence_score=final_confidence,
            policy_checks={
                "matched_rules": rule_result.matched_rules,
                "triggered_red_flags": rule_result.triggered_red_flags,
                "reasons": rule_result.reasons,
                "citations": rule_result.citations,
            },
            llm_audit_data=llm_audit_data,
            ai_decision=final_decision,
            ai_confidence=final_confidence,
            ai_reasoning=final_reasoning,
            risk_score=risk_score,
            anomaly_flags=anomaly_flags,
            error_context=error_context,
        )
        self.db.add(refund_req)
        await self.db.flush()

        # 9. Persist RefundItem
        refund_item = RefundItem(
            id=uuid.uuid4(),
            refund_request_id=refund_req.id,
            order_item_id=order_item.id,
            quantity=quantity,
            refund_amount=refund_amount,
            item_condition=payload.item_condition,
        )
        self.db.add(refund_item)
        await self.db.flush()

        # 10. Persist AuditLog
        audit_service = AuditService(self.db)
        await audit_service.log_event(
            action="refund_evaluated",
            actor="system",
            refund_request_id=refund_req.id,
            details={
                "decision": final_decision,
                "confidence_score": final_confidence,
                "reason": final_reasoning,
                "risk_score": risk_score,
                "anomaly_flags": anomaly_flags,
                "error_context": error_context,
                "matched_rules": rule_result.matched_rules,
                "triggered_red_flags": rule_result.triggered_red_flags,
                "guardrails_triggered": llm_audit_data.get("guardrails_triggered", []),
                "llm_provider": llm_audit_data.get("telemetry", {}).get("provider")
                or ("fallback" if llm_audit_data.get("fallback") else "mock"),
            },
        )

        # 10. Recalculate customer metrics if approved
        if final_decision == "Approved":
            await customer_service.recalculate_customer_metrics(customer.id)

        await self.db.commit()
        await self.db.refresh(refund_req)

        # Reload with relationships
        return await self.get_refund_request(refund_req.id)  # type: ignore[return-value]
