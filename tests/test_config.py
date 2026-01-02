#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for config.py module.
Tests environment variable loading, type conversion, and validation.
"""

import os
import sys
import importlib


def test_scenario(name, env_vars, should_fail=False):
    """
    Test a configuration scenario.

    Args:
        name: Description of the test scenario
        env_vars: Dictionary of environment variables to set
        should_fail: Whether this scenario should fail validation
    """
    print("\n" + "=" * 80)
    print(f"TEST: {name}")
    print("=" * 80)

    # Clear any existing config module
    if 'config' in sys.modules:
        del sys.modules['config']

    # Set environment variables for this test
    original_env = {}
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(value)

    try:
        # Import config module (this triggers validation)
        import config

        if should_fail:
            print("❌ FAILED: Expected validation error but config loaded successfully")
            return False
        else:
            print("✅ PASSED: Configuration loaded successfully")

            # Print some key values
            print(f"   MY_CALLSIGN: {config.MY_CALLSIGN}")
            print(f"   HA_MQTT_BROKER: {config.HA_MQTT_BROKER}")
            print(f"   SCRIPT_DIRECTION: {config.SCRIPT_DIRECTION}")
            print(f"   DEBUG_MODE: {config.DEBUG_MODE} (type: {type(config.DEBUG_MODE).__name__})")
            print(f"   HA_MQTT_PORT: {config.HA_MQTT_PORT} (type: {type(config.HA_MQTT_PORT).__name__})")
            print(f"   ENABLE_SPOT_SENSORS: {config.ENABLE_SPOT_SENSORS} (type: {type(config.ENABLE_SPOT_SENSORS).__name__})")
            print(f"   SPOT_ALLOW_CALLSIGNS: {config.SPOT_ALLOW_CALLSIGNS} (type: {type(config.SPOT_ALLOW_CALLSIGNS).__name__})")
            return True

    except SystemExit as e:
        if should_fail:
            print("✅ PASSED: Configuration validation failed as expected")
            return True
        else:
            print("❌ FAILED: Unexpected validation error")
            return False

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main():
    """Run all configuration tests."""
    print("\n" + "=" * 80)
    print("PSKr HA Bridge - Configuration Module Test Suite")
    print("=" * 80)

    results = []

    # Test 1: Minimal valid configuration
    results.append(test_scenario(
        "Minimal Valid Configuration",
        {
            'MY_CALLSIGN': 'W1AW',
            'HA_MQTT_BROKER': '192.168.1.100'
        },
        should_fail=False
    ))

    # Test 2: Full configuration with all options
    results.append(test_scenario(
        "Full Configuration",
        {
            'MY_CALLSIGN': 'K2ABC',
            'HA_MQTT_BROKER': 'homeassistant.local',
            'HA_MQTT_PORT': '1883',
            'HA_MQTT_USER': 'mqtt_user',
            'HA_MQTT_PASS': 'mqtt_pass',
            'SCRIPT_DIRECTION': 'dual',
            'DEBUG_MODE': 'true',
            'ENABLE_SPOT_SENSORS': 'yes',
            'SPOT_FILTER_MIN_DISTANCE_KM': '1000',
            'SPOT_ALLOW_CALLSIGNS': 'W1AW, K1ABC, N2DEF',
            'SPOT_FILTERED_COUNTRIES': '291, 100',
            'PSK_TRANSPORT_MODE': 'MQTT_TLS',
            'STATS_INTERVAL_WINDOW_SECONDS': '600',
            'STATS_UPDATE_INTERVAL_SECONDS': '120'
        },
        should_fail=False
    ))

    # Test 3: Missing MY_CALLSIGN (should fail)
    results.append(test_scenario(
        "Missing MY_CALLSIGN (should fail)",
        {
            'HA_MQTT_BROKER': '192.168.1.100'
        },
        should_fail=True
    ))

    # Test 4: Missing HA_MQTT_BROKER (should fail)
    results.append(test_scenario(
        "Missing HA_MQTT_BROKER (should fail)",
        {
            'MY_CALLSIGN': 'W1AW'
        },
        should_fail=True
    ))

    # Test 5: Invalid SCRIPT_DIRECTION (should fail)
    results.append(test_scenario(
        "Invalid SCRIPT_DIRECTION (should fail)",
        {
            'MY_CALLSIGN': 'W1AW',
            'HA_MQTT_BROKER': '192.168.1.100',
            'SCRIPT_DIRECTION': 'invalid'
        },
        should_fail=True
    ))

    # Test 6: Invalid PSK_TRANSPORT_MODE (should fail)
    results.append(test_scenario(
        "Invalid PSK_TRANSPORT_MODE (should fail)",
        {
            'MY_CALLSIGN': 'W1AW',
            'HA_MQTT_BROKER': '192.168.1.100',
            'PSK_TRANSPORT_MODE': 'INVALID_MODE'
        },
        should_fail=True
    ))

    # Test 7: Invalid port number (should fail)
    results.append(test_scenario(
        "Invalid Port Number (should fail)",
        {
            'MY_CALLSIGN': 'W1AW',
            'HA_MQTT_BROKER': '192.168.1.100',
            'HA_MQTT_PORT': '99999'
        },
        should_fail=True
    ))

    # Test 8: Boolean conversion variations
    results.append(test_scenario(
        "Boolean Conversion Tests",
        {
            'MY_CALLSIGN': 'W1AW',
            'HA_MQTT_BROKER': '192.168.1.100',
            'DEBUG_MODE': '1',
            'ENABLE_SPOT_SENSORS': 'on',
            'PSK_TLS_INSECURE': 'false'
        },
        should_fail=False
    ))

    # Test 9: Empty list parsing
    results.append(test_scenario(
        "Empty List Parsing",
        {
            'MY_CALLSIGN': 'W1AW',
            'HA_MQTT_BROKER': '192.168.1.100',
            'SPOT_ALLOW_CALLSIGNS': '',
            'SPOT_FILTERED_COUNTRIES': ''
        },
        should_fail=False
    ))

    # Test 10: List with extra whitespace
    results.append(test_scenario(
        "List Parsing with Whitespace",
        {
            'MY_CALLSIGN': 'W1AW',
            'HA_MQTT_BROKER': '192.168.1.100',
            'SPOT_ALLOW_CALLSIGNS': '  W1AW  ,  K1ABC  ,  N2DEF  ',
            'SPOT_FILTERED_COUNTRIES': ' 291 , 100 , 339 '
        },
        should_fail=False
    ))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
