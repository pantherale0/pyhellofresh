"""Tests for delivery-week selection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pyhellofresh.errors import HelloFreshError
from pyhellofresh.models import PastDeliveryItem
from pyhellofresh.weeks import select_latest_delivery_week, shift_iso_week

NOW = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)


def _week(
    week: str,
    cutoff: str | None = None,
    status: str | None = "RUNNING",
    delivery: str | None = None,
) -> PastDeliveryItem:
    return PastDeliveryItem(
        week=week,
        cutoff_date=cutoff,
        delivery_date=delivery,
        status=status,
    )


def test_shift_iso_week():
    assert shift_iso_week("2026-W40", 0) == "2026-W40"
    assert shift_iso_week("2026-W40", 1) == "2026-W41"
    assert shift_iso_week("2026-W40", -1) == "2026-W39"
    assert shift_iso_week("2020-W53", 1) == "2021-W01"


def test_shift_iso_week_rejects_bad_id():
    with pytest.raises(HelloFreshError):
        shift_iso_week("week-40", 1)


def test_latest_delivery_week_is_newest_passed_cutoff():
    weeks = [
        _week("2026-W39", "2026-09-18T23:59:59+00:00", "DELIVERED"),
        _week("2026-W40", "2026-09-25T23:59:59+00:00", "RUNNING"),
        _week("2026-W41", "2026-10-02T23:59:59+00:00", "RUNNING"),
    ]
    assert select_latest_delivery_week(weeks, NOW) == "2026-W40"


def test_latest_delivery_week_skips_paused():
    weeks = [
        _week("2026-W40", "2026-09-25T23:59:59+00:00", "RUNNING"),
        _week("2026-W42", "2026-09-20T23:59:59+00:00", "PAUSED"),
    ]
    assert select_latest_delivery_week(weeks, NOW) == "2026-W40"


def test_latest_delivery_week_uses_delivery_date_without_cutoff():
    weeks = [
        _week("2026-W39", delivery="2026-09-23T00:00:00+00:00", status="DELIVERED"),
        _week("2026-W40", delivery="2026-09-30T00:00:00+00:00", status="RUNNING"),
        _week("2026-W41", delivery="2026-10-07T00:00:00+00:00", status="RUNNING"),
    ]
    assert select_latest_delivery_week(weeks, NOW) == "2026-W40"


def test_latest_delivery_week_requires_a_week():
    with pytest.raises(HelloFreshError):
        select_latest_delivery_week([], NOW)
