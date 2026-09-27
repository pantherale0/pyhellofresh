"""ISO week helpers for HelloFresh delivery schedules."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .errors import HelloFreshError
from .models import PastDeliveryItem

_SKIPPED_STATUSES = {"PAUSED", "CANCELLED", "CANCELED", "DONATED"}


def shift_iso_week(week: str, offset: int) -> str:
    """Move an ISO week id by ``offset`` weeks.

    Args:
        week: Week id such as ``2026-W40``.
        offset: Number of weeks to add. Negative values move backward.

    Returns:
        The shifted week id.

    Raises:
        HelloFreshError: If ``week`` is not an ISO week id.
    """
    monday = _week_monday(week)
    shifted = monday + timedelta(weeks=offset)
    iso = shifted.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def current_iso_week(moment: datetime) -> str:
    """Return the ISO week id that contains ``moment``."""
    iso = moment.date().isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def select_latest_delivery_week(
    weeks: list[PastDeliveryItem],
    now: datetime,
) -> str:
    """Pick the newest delivery week whose cutoff has already passed.

    That week is the locked box: it is arriving now or has just been delivered.
    Later weeks in the schedule are still open for selection. Paused, cancelled,
    and donated weeks are ignored while another delivery remains.

    Args:
        weeks: Delivery weeks from the customer schedule.
        now: Instant used to decide which cutoffs have passed.

    Returns:
        ISO week id of the latest locked delivery.

    Raises:
        HelloFreshError: If the schedule has no usable delivery week.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    candidates = [item for item in weeks if _is_iso_week(item.week)]
    if not candidates:
        raise HelloFreshError("No delivery weeks were returned.")

    active = [
        item
        for item in candidates
        if (item.status or "").upper() not in _SKIPPED_STATUSES
    ]
    pool = active or candidates

    locked = [
        item
        for item in pool
        if (cutoff := _parse_api_datetime(item.cutoff_date)) is not None
        and cutoff <= now
    ]
    if locked:
        return max(locked, key=_week_sort_key).week

    dated: list[tuple[datetime, PastDeliveryItem]] = []
    for item in pool:
        delivery = _parse_api_datetime(item.delivery_date)
        if delivery is not None:
            dated.append((delivery, item))
    if dated:
        window_end = now + timedelta(days=7)
        in_window = [(when, item) for when, item in dated if when <= window_end]
        chosen = in_window or dated
        return max(chosen, key=lambda pair: _week_sort_key(pair[1]))[1].week

    return max(pool, key=_week_sort_key).week


def _is_iso_week(week: str) -> bool:
    try:
        _week_monday(week)
    except HelloFreshError:
        return False
    return True


def _week_monday(week: str) -> datetime:
    parts = week.split("-W")
    if len(parts) != 2:
        raise HelloFreshError(f"Invalid delivery week '{week}'.")
    try:
        year = int(parts[0])
        week_num = int(parts[1])
        return datetime.fromisocalendar(year, week_num, 1)
    except ValueError as err:
        raise HelloFreshError(f"Invalid delivery week '{week}'.") from err


def _week_sort_key(item: PastDeliveryItem) -> tuple[int, int]:
    year, week = (int(part) for part in item.week.split("-W"))
    return year, week


def _parse_api_datetime(value: str | None) -> datetime | None:
    """Parse a HelloFresh timestamp, including offsets without a colon."""
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    if len(text) >= 5 and text[-5] in "+-" and text[-3] != ":":
        text = f"{text[:-2]}:{text[-2:]}"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
