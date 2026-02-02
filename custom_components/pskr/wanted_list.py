"""Parser for DXCC/Band wanted list configuration."""

from __future__ import annotations


def parse_wanted_list(value: str) -> set[tuple[str, str]]:
    """Parse comma-separated DXCC:BAND pairs into a set of tuples.

    Args:
        value: String like "339:20m,339:15m,150:40m"

    Returns:
        Set of (dxcc_code, band) tuples. Invalid entries are silently skipped.
    """
    if not value or not value.strip():
        return set()

    result: set[tuple[str, str]] = set()
    for item in value.split(","):
        item = item.strip()
        if ":" not in item:
            continue
        parts = item.split(":", 1)
        dxcc = parts[0].strip()
        band = parts[1].strip().lower()
        if dxcc and band:
            result.add((dxcc, band))
    return result


def format_wanted_list(wanted: set[tuple[str, str]]) -> str:
    """Format wanted set back to comma-separated string for display/storage.

    Args:
        wanted: Set of (dxcc_code, band) tuples.

    Returns:
        Comma-separated string like "150:40m,339:15m,339:20m" (sorted).
    """
    return ",".join(f"{dxcc}:{band}" for dxcc, band in sorted(wanted))
