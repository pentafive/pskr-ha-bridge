"""Tests for activity heatmap counter logic."""

import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone


# --- Standalone heatmap builder (mirrors coordinator logic without HA deps) ---

HF_BANDS = ["160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m"]
HEATMAP_WINDOW_HOURS = 24


def build_activity_heatmap(hourly_counts: dict) -> dict[int, dict[str, int]]:
    """Build 24h heatmap from hourly_counts, pruning stale entries."""
    utc_now = datetime.now(timezone.utc)
    cutoff = utc_now - timedelta(hours=HEATMAP_WINDOW_HOURS)

    # Prune old
    stale_keys = [
        k for k in list(hourly_counts.keys())
        if datetime.strptime(k, "%Y-%m-%d-%H").replace(tzinfo=timezone.utc) < cutoff
    ]
    for k in stale_keys:
        del hourly_counts[k]

    # Build matrix
    heatmap: dict[int, dict[str, int]] = {}
    for hour in range(24):
        heatmap[hour] = dict.fromkeys(HF_BANDS, 0)

    for key, band_counts in hourly_counts.items():
        hour = int(key.split("-")[-1])
        for band, count in band_counts.items():
            if band in heatmap[hour]:
                heatmap[hour][band] += count

    return heatmap


class TestHeatmapStructure:
    """Test the heatmap output structure."""

    def test_empty_counters_produce_full_matrix(self):
        """Empty counters should still produce all 24 hours with all bands zeroed."""
        heatmap = build_activity_heatmap({})
        assert len(heatmap) == 24
        for hour in range(24):
            assert hour in heatmap
            assert len(heatmap[hour]) == len(HF_BANDS)
            for band in HF_BANDS:
                assert heatmap[hour][band] == 0

    def test_all_hours_present(self):
        """All 24 hours (0-23) should be present regardless of data."""
        now = datetime.now(timezone.utc)
        key = now.strftime("%Y-%m-%d-%H")
        counters = {key: defaultdict(int, {"20m": 5})}
        heatmap = build_activity_heatmap(counters)
        assert set(heatmap.keys()) == set(range(24))

    def test_all_bands_present_per_hour(self):
        """Each hour should have entries for all HF_BANDS."""
        heatmap = build_activity_heatmap({})
        for hour in range(24):
            assert set(heatmap[hour].keys()) == set(HF_BANDS)


class TestHeatmapCounting:
    """Test increment and aggregation logic."""

    def test_single_band_single_hour(self):
        """A single band entry should appear in the correct hour."""
        now = datetime.now(timezone.utc)
        key = now.strftime("%Y-%m-%d-%H")
        counters = {key: defaultdict(int, {"20m": 42})}
        heatmap = build_activity_heatmap(counters)
        assert heatmap[now.hour]["20m"] == 42

    def test_multiple_bands_same_hour(self):
        """Multiple bands in the same hour should all appear."""
        now = datetime.now(timezone.utc)
        key = now.strftime("%Y-%m-%d-%H")
        counters = {key: defaultdict(int, {"20m": 10, "40m": 20, "80m": 5})}
        heatmap = build_activity_heatmap(counters)
        assert heatmap[now.hour]["20m"] == 10
        assert heatmap[now.hour]["40m"] == 20
        assert heatmap[now.hour]["80m"] == 5

    def test_same_hour_different_days_aggregates(self):
        """Same hour on consecutive days within window should aggregate."""
        now = datetime.now(timezone.utc)
        # Today's entry at current hour
        key_today = now.strftime("%Y-%m-%d-%H")
        # Yesterday's entry at same hour (only if within 24h window)
        yesterday = now - timedelta(hours=23)
        key_yesterday = yesterday.strftime("%Y-%m-%d-%H")

        counters = {
            key_today: defaultdict(int, {"20m": 10}),
            key_yesterday: defaultdict(int, {"20m": 7}),
        }

        heatmap = build_activity_heatmap(counters)
        # If yesterday's hour == today's hour, they aggregate.
        # Otherwise they appear in different hour slots.
        if now.hour == yesterday.hour:
            assert heatmap[now.hour]["20m"] == 17
        else:
            assert heatmap[now.hour]["20m"] == 10
            assert heatmap[yesterday.hour]["20m"] == 7

    def test_unknown_band_excluded(self):
        """Bands not in HF_BANDS should be excluded from heatmap."""
        now = datetime.now(timezone.utc)
        key = now.strftime("%Y-%m-%d-%H")
        counters = {key: defaultdict(int, {"20m": 5, "INVALID": 99})}
        heatmap = build_activity_heatmap(counters)
        assert heatmap[now.hour]["20m"] == 5
        assert "INVALID" not in heatmap[now.hour]


class TestHeatmapPruning:
    """Test that entries older than 24h are pruned."""

    def test_old_entries_pruned(self):
        """Entries older than 24h should be removed from counters dict."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=25)
        key_old = old.strftime("%Y-%m-%d-%H")
        key_new = now.strftime("%Y-%m-%d-%H")

        counters = {
            key_old: defaultdict(int, {"20m": 100}),
            key_new: defaultdict(int, {"20m": 5}),
        }
        heatmap = build_activity_heatmap(counters)

        # Old key should be pruned from counters
        assert key_old not in counters
        # New key should remain
        assert key_new in counters

        # Heatmap should only contain new data
        assert heatmap[now.hour]["20m"] == 5

    def test_boundary_entry_kept(self):
        """Entry exactly 23h old should be kept."""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(hours=23)
        key = recent.strftime("%Y-%m-%d-%H")

        counters = {key: defaultdict(int, {"40m": 15})}
        heatmap = build_activity_heatmap(counters)

        # Should NOT be pruned
        assert key in counters
        assert heatmap[recent.hour]["40m"] == 15

    def test_multiple_stale_entries_pruned(self):
        """Multiple old entries should all be pruned."""
        now = datetime.now(timezone.utc)
        counters = {}
        for hours_ago in range(30, 50):
            old = now - timedelta(hours=hours_ago)
            key = old.strftime("%Y-%m-%d-%H")
            counters[key] = defaultdict(int, {"20m": 1})

        fresh_key = now.strftime("%Y-%m-%d-%H")
        counters[fresh_key] = defaultdict(int, {"20m": 99})

        build_activity_heatmap(counters)

        # Only fresh entry should remain
        assert len(counters) == 1
        assert fresh_key in counters


class TestHeatmapTotalSpots:
    """Test the total spots calculation used as sensor state value."""

    def test_total_from_heatmap(self):
        """Total spots should be sum of all values in heatmap."""
        now = datetime.now(timezone.utc)
        key = now.strftime("%Y-%m-%d-%H")
        counters = {key: defaultdict(int, {"20m": 10, "40m": 20})}
        heatmap = build_activity_heatmap(counters)

        total = sum(sum(bands.values()) for bands in heatmap.values())
        assert total == 30

    def test_empty_total_is_zero(self):
        """Empty heatmap should total to 0."""
        heatmap = build_activity_heatmap({})
        total = sum(sum(bands.values()) for bands in heatmap.values())
        assert total == 0
