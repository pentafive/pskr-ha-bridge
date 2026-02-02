"""Tests for wanted list parser."""

import importlib.util
import os
import sys

# Import wanted_list directly to avoid homeassistant dependency in __init__.py
_module_path = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "pskr", "wanted_list.py"
)
_spec = importlib.util.spec_from_file_location("wanted_list", _module_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

parse_wanted_list = _module.parse_wanted_list
format_wanted_list = _module.format_wanted_list


class TestParseWantedList:
    def test_empty_string(self):
        assert parse_wanted_list("") == set()

    def test_whitespace_only(self):
        assert parse_wanted_list("   ") == set()

    def test_single_pair(self):
        assert parse_wanted_list("339:20m") == {("339", "20m")}

    def test_multiple_pairs(self):
        result = parse_wanted_list("339:20m,339:15m,150:40m")
        assert result == {("339", "20m"), ("339", "15m"), ("150", "40m")}

    def test_whitespace_handling(self):
        result = parse_wanted_list(" 339 : 20m , 150 : 40m ")
        assert result == {("339", "20m"), ("150", "40m")}

    def test_invalid_entries_skipped(self):
        result = parse_wanted_list("339:20m,invalid,150:40m,:,:")
        assert result == {("339", "20m"), ("150", "40m")}

    def test_empty_parts_skipped(self):
        result = parse_wanted_list("339:20m,,,,150:40m")
        assert result == {("339", "20m"), ("150", "40m")}

    def test_duplicate_handling(self):
        result = parse_wanted_list("339:20m,339:20m,339:20m")
        assert len(result) == 1
        assert result == {("339", "20m")}

    def test_case_normalization_band(self):
        result = parse_wanted_list("339:20M,150:6M")
        assert result == {("339", "20m"), ("150", "6m")}

    def test_trailing_comma(self):
        result = parse_wanted_list("339:20m,")
        assert result == {("339", "20m")}

    def test_missing_dxcc(self):
        result = parse_wanted_list(":20m")
        assert result == set()

    def test_missing_band(self):
        result = parse_wanted_list("339:")
        assert result == set()


class TestFormatWantedList:
    def test_round_trip(self):
        original = "150:40m,339:15m,339:20m"
        parsed = parse_wanted_list(original)
        formatted = format_wanted_list(parsed)
        assert parse_wanted_list(formatted) == parsed

    def test_empty(self):
        assert format_wanted_list(set()) == ""

    def test_sorted_output(self):
        wanted = {("339", "20m"), ("150", "40m"), ("100", "10m")}
        formatted = format_wanted_list(wanted)
        assert formatted == "100:10m,150:40m,339:20m"
