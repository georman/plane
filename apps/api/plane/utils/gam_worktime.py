# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: working-hours arithmetic for SLAs and reminders.
# Working time is Monday-Friday 09:00-17:00 Greek time (public holidays not excluded).

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Athens")
DAY_START = time(9, 0)
DAY_END = time(17, 0)


def _local(dt):
    return dt.astimezone(TZ)


def _is_workday(d):
    return d.weekday() < 5


def _clamp_to_work(dt):
    """Move a local datetime forward to the next moment that is inside working hours."""
    while True:
        if not _is_workday(dt.date()) or dt.time() >= DAY_END:
            dt = datetime.combine(dt.date() + timedelta(days=1), DAY_START, TZ)
            continue
        if dt.time() < DAY_START:
            dt = datetime.combine(dt.date(), DAY_START, TZ)
        return dt


def add_working_hours(start, hours):
    """start (aware) + N working hours -> aware UTC-comparable datetime."""
    remaining = timedelta(hours=hours)
    dt = _clamp_to_work(_local(start))
    while True:
        day_end = datetime.combine(dt.date(), DAY_END, TZ)
        available = day_end - dt
        if remaining <= available:
            return dt + remaining
        remaining -= available
        dt = _clamp_to_work(day_end)


def working_seconds_between(start, end):
    if end <= start:
        return 0
    total = 0.0
    dt = _clamp_to_work(_local(start))
    end = _local(end)
    while dt < end:
        day_end = datetime.combine(dt.date(), DAY_END, TZ)
        total += (min(day_end, end) - dt).total_seconds()
        dt = _clamp_to_work(day_end)
    return total


def working_days_between(start, end):
    """Whole working days elapsed (8 working hours each)."""
    return int(working_seconds_between(start, end) // (8 * 3600))


def is_working_time(dt):
    local = _local(dt)
    return _is_workday(local.date()) and DAY_START <= local.time() < DAY_END
