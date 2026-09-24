"""Security service for input sanitization, prompt injection detection, and incident audit logging."""

import html
import re
import uuid
from typing import ClassVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security import SecurityLog


class SecurityService:
    """Service providing perimeter input sanitization and heuristic prompt injection classification."""

    # Curated regex pattern catalog for adversarial prompt injection and jailbreaks
    INJECTION_PATTERNS: ClassVar[dict[str, str]] = {
        "ignore_instructions": r"(?i)\b(ignore|disregard|forget|skip)\s+(all\s+)?(previous|prior|above|existing|system)\s+(instructions|directives|prompts|rules|commands)\b",
        "system_prompt_extraction": r"(?i)\b(output|reveal|repeat|display|print|show)\s+(the\s+)?(system\s+prompt|initial\s+instructions|system\s+instructions|secret\s+key)\b",
        "developer_mode": r"(?i)\b(you\s+are\s+now\s+(in\s+)?|enable\s+|activate\s+|switch\s+to\s+)(developer|maintenance|god|jailbreak|unrestricted|dan|superadmin)\s+mode\b",
        "roleplay_jailbreak": r"(?i)\b(act\s+as|pretend\s+you\s+are|roleplay\s+as)\s+(an\s+unrestricted|a\s+hacked|an\s+override|a\s+store\s+manager|an\s+admin)\b",
        "policy_override_directive": r"(?i)\b(override|bypass|ignore|circumvent)\s+(all\s+)?(refund\s+)?(policies|policy|rules|safeguards|limits)\b",
        "forced_decision": r"(?i)\b(always\s+respond\s+with\s+approved|force\s+approval|you\s+must\s+approve\s+this|mandatory\s+approval\s+required)\b",
        "fake_system_delimiter": r"(?i)(</?customer_claim_text>|</?system>|</?instruction>|\[system\]|\[instruction\]|system:)",
        "policy_manipulation": r"(?i)\b(policy\s+deadline\s+is\s+extended|return\s+window\s+is\s+now\s+365|rules\s+no\s+longer\s+apply)\b",
        "assistant_override": r"(?i)\b(assistant:\s*approved|new\s+system\s+directive|assistant\s+response:\s*approved)\b",
    }

    # Compiled patterns for optimal matching performance
    _COMPILED_PATTERNS: ClassVar[list[tuple[str, re.Pattern]]] = [
        (name, re.compile(pattern)) for name, pattern in INJECTION_PATTERNS.items()
    ]

    # Pattern for stripping HTML, script, and dangerous markup tags
    HTML_TAG_PATTERN: ClassVar[re.Pattern] = re.compile(r"<[^>]+>")

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Strip HTML tags, unescape HTML entities, and normalize whitespace."""
        if not text:
            return ""
        # 1. Remove dangerous script and HTML tags
        cleaned = cls.HTML_TAG_PATTERN.sub("", text)
        # 2. Unescape common HTML entities
        cleaned = html.unescape(cleaned)
        # 3. Strip null bytes and non-printable control characters (preserve normal newlines and tabs)
        cleaned = "".join(ch for ch in cleaned if ch == "\n" or ch == "\t" or ch >= " ")
        # 4. Strip leading/trailing whitespace
        return cleaned.strip()

    @classmethod
    def detect_prompt_injection(cls, text: str) -> tuple[bool, str | None]:
        """Scan input text against prompt injection heuristic catalog.

        Returns (is_injection, matched_pattern_name).
        """
        if not text:
            return False, None

        # Check each compiled regular expression pattern
        for pattern_name, compiled_regex in cls._COMPILED_PATTERNS:
            if compiled_regex.search(text):
                return True, pattern_name

        return False, None

    @classmethod
    async def record_security_event(
        cls,
        db: AsyncSession,
        event_type: str,
        endpoint: str,
        severity: str = "high",
        matched_pattern: str | None = None,
        payload_preview: str | None = None,
        customer_email: str | None = None,
        order_number: str | None = None,
        source_ip: str | None = None,
    ) -> SecurityLog:
        """Persist a security incident record to the security_logs table."""
        # Truncate payload preview to max 500 characters
        truncated_preview = payload_preview[:500] if payload_preview else None

        log_entry = SecurityLog(
            id=uuid.uuid4(),
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            endpoint=endpoint,
            matched_pattern=matched_pattern,
            payload_preview=truncated_preview,
            customer_email=customer_email,
            order_number=order_number,
        )

        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry

    @classmethod
    async def list_security_logs(
        cls,
        db: AsyncSession,
        event_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SecurityLog], int]:
        """Query security logs with optional event_type/severity filtering and pagination."""
        query = select(SecurityLog)
        count_query = select(func.count(SecurityLog.id))

        if event_type:
            query = query.where(SecurityLog.event_type == event_type)
            count_query = count_query.where(SecurityLog.event_type == event_type)
        if severity:
            query = query.where(SecurityLog.severity == severity)
            count_query = count_query.where(SecurityLog.severity == severity)

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        query = query.order_by(SecurityLog.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(query)
        logs = list(res.scalars().all())

        return logs, total
