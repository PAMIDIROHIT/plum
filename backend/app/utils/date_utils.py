# =====================================================================
# Utilities - Date and Time Helpers
# =====================================================================

from datetime import datetime, date, timedelta
from typing import Optional


def parse_date(date_str: str, formats: list = None) -> Optional[datetime]:
    """
    Parses a date string into a datetime object supporting multiple formats.
    Returns None if parsing fails.
    """
    if not date_str:
        return None
    default_formats = [
        "%Y-%m-%d",      # ISO 8601
        "%d/%m/%Y",      # Indian standard
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y/%m/%d",
        "%m/%d/%Y",      # US format
    ]
    for fmt in (formats or default_formats):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def normalize_date(date_str: str) -> Optional[str]:
    """
    Parses and normalizes a date string to YYYY-MM-DD format.
    Returns None if the date cannot be parsed.
    """
    dt = parse_date(date_str)
    return dt.strftime("%Y-%m-%d") if dt else None


def days_between(date1_str: str, date2_str: str) -> Optional[int]:
    """
    Returns the number of days between two date strings (date2 - date1).
    Returns None if either date is unparseable.
    """
    d1 = parse_date(date1_str)
    d2 = parse_date(date2_str)
    if d1 is None or d2 is None:
        return None
    return (d2 - d1).days


def days_since(date_str: str) -> Optional[int]:
    """
    Returns the number of days since the given date up to today.
    Returns None if the date is unparseable.
    """
    d = parse_date(date_str)
    if d is None:
        return None
    return (datetime.now() - d).days


def add_days(date_str: str, days: int) -> Optional[str]:
    """
    Returns a new date string that is `days` days after the given date.
    """
    d = parse_date(date_str)
    if d is None:
        return None
    return (d + timedelta(days=days)).strftime("%Y-%m-%d")


def same_policy_year(date1_str: str, date2_str: str) -> bool:
    """
    Returns True if both dates fall in the same calendar year.
    """
    d1 = parse_date(date1_str)
    d2 = parse_date(date2_str)
    if d1 is None or d2 is None:
        return False
    return d1.year == d2.year


def is_within_submission_window(treatment_date_str: str, window_days: int = 30) -> bool:
    """
    Returns True if the treatment date is within the allowed submission window from today.
    """
    elapsed = days_since(treatment_date_str)
    if elapsed is None:
        return True  # Cannot determine — don't penalize
    return elapsed <= window_days


def format_date_human(date_str: str) -> str:
    """
    Formats a YYYY-MM-DD string to a human-readable form like '01 Nov 2024'.
    """
    d = parse_date(date_str)
    if d is None:
        return date_str
    return d.strftime("%d %b %Y")
