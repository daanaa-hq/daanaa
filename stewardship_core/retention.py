"""Retention and privacy decisions without touching production data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import DataClass, RetentionClass


RETENTION_DAYS = {
    RetentionClass.TRANSIENT: 0,
    RetentionClass.RAW_MESSAGE_30D: 30,
    RetentionClass.OPERATIONAL: 365,
    RetentionClass.GOVERNANCE: None,
    RetentionClass.MANUAL_REVIEW: 90,
}


def retention_expiry(retention: RetentionClass, created_at: datetime) -> datetime | None:
    days = RETENTION_DAYS[retention]
    if days is None:
        return None
    return created_at.astimezone(timezone.utc) + timedelta(days=days)


def can_externalize(data_class: DataClass, *, founder_approved: bool = False) -> bool:
    return data_class == DataClass.PUBLIC or (data_class == DataClass.INTERNAL and founder_approved)
