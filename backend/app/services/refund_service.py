"""Refund service handling refund lifecycle, policy evaluation, and AI integration."""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.engine import AIDecisionEngine, AIProviderError
from app.ai.validators import enforce_policy_guardrails
from app.models.order import Order
from app.models.refund_item import RefundItem
from app.models.refund_request import RefundRequest
from app.schemas.refund import RefundSubmissionPayload
from app.services.audit_service import AuditService
from app.services.customer_service import CustomerService
from app.services.policy_service import PolicyService

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

    async def process_refund(self, payload: RefundSubmissionPayload) -> RefundRequest:
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
            raise ValueError(
                f"Order '{payload.order_number}' does not belong to customer '{payload.customer_email}'."
            )

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

        # 4. Quantity and Prior Claim Check
        quantity = payload.quantity if payload.quantity > 0 else 1
        refund_amount = payload.amount if payload.amount > 0 else (order_item.price * quantity)

        prior_refund_stmt = select(RefundItem).where(RefundItem.order_item_id == order_item.id)
        prior_refund = (await self.db.execute(prior_refund_stmt)).scalar_one_or_none()
        if prior_refund:
            raise ValueError(
                f"A refund request has already been submitted or processed for item '{payload.item_id}' (FLAG_DUPLICATE_CLAIM)."
            )
        has_prior_refund_for_item = False

        days_since_delivery = None
        if order.delivery_date:
            days_since_delivery = max(0, (datetime.utcnow() - order.delivery_date).days)

        # 5. Phase 1: Deterministic Policy Evaluation
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

        final_decision = rule_result.preliminary_decision
        final_confidence = (
            0.95 if rule_result.is_approved else (1.0 if rule_result.is_denied else 0.5)
        )
        final_reasoning = "; ".join(rule_result.reasons)
        llm_audit_data = {}

        # 6. Phase 2: AI Contextual Evaluation with Fallback
        ai_engine = AIDecisionEngine()
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

            validated_ai = enforce_policy_guardrails(
                preliminary_decision=rule_result.preliminary_decision,
                ai_decision=ai_res,
                rule_reasons=rule_result.reasons,
            )
            final_decision = validated_ai["decision"]
            final_confidence = validated_ai["confidence_score"]
            final_reasoning = validated_ai["explanation"]
            llm_audit_data = validated_ai

        except AIProviderError as ai_err:
            logger.info("ai_evaluation_fallback_active", reason=str(ai_err))
            if rule_result.is_denied:
                final_decision = "Denied"
                final_confidence = 1.0
                final_reasoning = f"Policy rule check: {'; '.join(rule_result.reasons)}"
            elif rule_result.is_escalated:
                final_decision = "Escalated"
                final_confidence = 0.5
                final_reasoning = f"Policy escalation check: {'; '.join(rule_result.reasons)}"
            else:
                # Ambiguous/subjective claim without AI decision is escalated to human support
                final_decision = "Escalated"
                final_confidence = 0.5
                final_reasoning = (
                    "Automated AI evaluation is temporarily unavailable. "
                    "Your claim has been routed to human support for expedited review."
                )

            llm_audit_data = {
                "fallback": True,
                "reason": str(ai_err),
                "deterministic_decision": rule_result.preliminary_decision,
            }

        # 7. Persist RefundRequest
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
        )
        self.db.add(refund_req)
        await self.db.flush()

        # 8. Persist RefundItem
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

        # 9. Persist AuditLog
        audit_service = AuditService(self.db)
        await audit_service.log_event(
            action="refund_evaluated",
            actor="system",
            refund_request_id=refund_req.id,
            details={
                "decision": final_decision,
                "confidence_score": final_confidence,
                "reason": final_reasoning,
                "matched_rules": rule_result.matched_rules,
                "triggered_red_flags": rule_result.triggered_red_flags,
            },
        )

        # 10. Recalculate customer metrics if approved
        if final_decision == "Approved":
            await customer_service.recalculate_customer_metrics(customer.id)

        await self.db.commit()
        await self.db.refresh(refund_req)

        # Reload with relationships
        return await self.get_refund_request(refund_req.id)  # type: ignore[return-value]
