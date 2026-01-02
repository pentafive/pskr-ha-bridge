#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration module for PSKr HA Bridge.
Loads configuration from environment variables with sensible defaults.
"""

import os
import sys


def str_to_bool(value):
    """Convert string to boolean. Handles common string representations."""
    if isinstance(value, bool):
        return value
    if not value:
        return False
    return value.lower() in ('true', '1', 'yes', 'on', 't', 'y')


def str_to_int(value, default=0):
    """Convert string to integer with fallback to default."""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default


def parse_list(value):
    """Parse comma-separated string into list, stripping whitespace."""
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.split(',') if item.strip()]


# ==============================================================================
# --- Core Identity ---
# ==============================================================================

MY_CALLSIGN = os.getenv('MY_CALLSIGN', 'YOUR_CALLSIGN')

# ==============================================================================
# --- Debugging ---
# ==============================================================================

DEBUG_MODE = str_to_bool(os.getenv('DEBUG_MODE', 'False'))

# ==============================================================================
# --- MQTT Broker Configuration ---
# ==============================================================================

# PSKReporter Broker
PSK_BROKER = os.getenv('PSK_BROKER', 'mqtt.pskreporter.info')
PSK_TRANSPORT_MODE = os.getenv('PSK_TRANSPORT_MODE', 'MQTT_WS_TLS')
PSK_TLS_INSECURE = str_to_bool(os.getenv('PSK_TLS_INSECURE', 'False'))

# Home Assistant Broker
HA_MQTT_BROKER = os.getenv('HA_MQTT_BROKER', 'YOUR_MQTT_BROKER_IP')
HA_MQTT_PORT = str_to_int(os.getenv('HA_MQTT_PORT'), default=1883)
HA_MQTT_USER = os.getenv('HA_MQTT_USER') or None
HA_MQTT_PASS = os.getenv('HA_MQTT_PASS') or None

# ==============================================================================
# --- Script Operation Mode ---
# ==============================================================================

SCRIPT_DIRECTION = os.getenv('SCRIPT_DIRECTION', 'rx')
MODES_FILTER = os.getenv('MODES_FILTER', '+')

# ==============================================================================
# --- Statistics Timing ---
# ==============================================================================

STATS_INTERVAL_WINDOW_SECONDS = str_to_int(
    os.getenv('STATS_INTERVAL_WINDOW_SECONDS'),
    default=900
)
STATS_UPDATE_INTERVAL_SECONDS = str_to_int(
    os.getenv('STATS_UPDATE_INTERVAL_SECONDS'),
    default=300
)

# ==============================================================================
# --- Spot Sensor Control & Filtering ---
# ==============================================================================

ENABLE_SPOT_SENSORS = str_to_bool(os.getenv('ENABLE_SPOT_SENSORS', 'True'))
SPOT_FILTER_MIN_DISTANCE_KM = str_to_int(
    os.getenv('SPOT_FILTER_MIN_DISTANCE_KM'),
    default=0
)

# Parse comma-separated lists for callsign and country filtering
SPOT_ALLOW_CALLSIGNS = parse_list(os.getenv('SPOT_ALLOW_CALLSIGNS', ''))
SPOT_FILTERED_CALLSIGNS = parse_list(os.getenv('SPOT_FILTERED_CALLSIGNS', ''))
SPOT_ALLOW_COUNTRIES = parse_list(os.getenv('SPOT_ALLOW_COUNTRIES', ''))
SPOT_FILTERED_COUNTRIES = parse_list(os.getenv('SPOT_FILTERED_COUNTRIES', ''))

# ==============================================================================
# --- Home Assistant Integration ---
# ==============================================================================

HA_DISCOVERY_PREFIX = os.getenv('HA_DISCOVERY_PREFIX', 'homeassistant')
HA_ENTITY_BASE = os.getenv('HA_ENTITY_BASE', 'pskr')

# ==============================================================================
# --- Configuration Validation ---
# ==============================================================================

def validate_config():
    """
    Validate required configuration values and provide helpful error messages.
    Called at module import time to fail fast if misconfigured.
    """
    errors = []

    # Required fields
    if MY_CALLSIGN in ['YOUR_CALLSIGN', '', None]:
        errors.append(
            "MY_CALLSIGN is required. Set the MY_CALLSIGN environment variable "
            "to your amateur radio callsign."
        )

    if HA_MQTT_BROKER in ['YOUR_MQTT_BROKER_IP', '', None]:
        errors.append(
            "HA_MQTT_BROKER is required. Set the HA_MQTT_BROKER environment variable "
            "to your Home Assistant MQTT broker IP address or hostname."
        )

    # Validate SCRIPT_DIRECTION
    valid_directions = ['rx', 'tx', 'dual']
    if SCRIPT_DIRECTION.lower() not in valid_directions:
        errors.append(
            f"SCRIPT_DIRECTION must be one of {valid_directions}. "
            f"Got: '{SCRIPT_DIRECTION}'"
        )

    # Validate PSK_TRANSPORT_MODE
    valid_transport_modes = ['MQTT', 'MQTT_TLS', 'MQTT_WS', 'MQTT_WS_TLS']
    if PSK_TRANSPORT_MODE.upper() not in valid_transport_modes:
        errors.append(
            f"PSK_TRANSPORT_MODE must be one of {valid_transport_modes}. "
            f"Got: '{PSK_TRANSPORT_MODE}'"
        )

    # Validate port number
    if not (1 <= HA_MQTT_PORT <= 65535):
        errors.append(
            f"HA_MQTT_PORT must be between 1 and 65535. Got: {HA_MQTT_PORT}"
        )

    # Validate timing values
    if STATS_INTERVAL_WINDOW_SECONDS < 60:
        errors.append(
            f"STATS_INTERVAL_WINDOW_SECONDS should be at least 60 seconds. "
            f"Got: {STATS_INTERVAL_WINDOW_SECONDS}"
        )

    if STATS_UPDATE_INTERVAL_SECONDS < 30:
        errors.append(
            f"STATS_UPDATE_INTERVAL_SECONDS should be at least 30 seconds. "
            f"Got: {STATS_UPDATE_INTERVAL_SECONDS}"
        )

    # If there are errors, print them and exit
    if errors:
        print("=" * 80)
        print("CONFIGURATION ERRORS")
        print("=" * 80)
        for i, error in enumerate(errors, 1):
            print(f"\n{i}. {error}")
        print("\n" + "=" * 80)
        print("Please fix the configuration errors above and try again.")
        print("=" * 80)
        sys.exit(1)


# Run validation when module is imported
validate_config()

# ==============================================================================
# --- Configuration Summary ---
# ==============================================================================

def print_config_summary():
    """Print a summary of the loaded configuration for debugging."""
    print("=" * 80)
    print("CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"MY_CALLSIGN:              {MY_CALLSIGN}")
    print(f"DEBUG_MODE:               {DEBUG_MODE}")
    print(f"SCRIPT_DIRECTION:         {SCRIPT_DIRECTION.upper()}")
    print(f"PSK_BROKER:               {PSK_BROKER}")
    print(f"PSK_TRANSPORT_MODE:       {PSK_TRANSPORT_MODE}")
    print(f"HA_MQTT_BROKER:           {HA_MQTT_BROKER}:{HA_MQTT_PORT}")
    print(f"HA_MQTT_AUTH:             {'Yes' if HA_MQTT_USER else 'No'}")
    print(f"ENABLE_SPOT_SENSORS:      {ENABLE_SPOT_SENSORS}")

    if ENABLE_SPOT_SENSORS:
        print(f"SPOT_FILTER_MIN_DIST:     {SPOT_FILTER_MIN_DISTANCE_KM} km")
        print(f"SPOT_ALLOW_CALLSIGNS:     {SPOT_ALLOW_CALLSIGNS if SPOT_ALLOW_CALLSIGNS else 'Any'}")
        print(f"SPOT_FILTERED_CALLSIGNS:  {SPOT_FILTERED_CALLSIGNS if SPOT_FILTERED_CALLSIGNS else 'None'}")
        print(f"SPOT_ALLOW_COUNTRIES:     {SPOT_ALLOW_COUNTRIES if SPOT_ALLOW_COUNTRIES else 'Any'}")
        print(f"SPOT_FILTERED_COUNTRIES:  {SPOT_FILTERED_COUNTRIES if SPOT_FILTERED_COUNTRIES else 'None'}")

    print(f"STATS_WINDOW:             {STATS_INTERVAL_WINDOW_SECONDS}s ({STATS_INTERVAL_WINDOW_SECONDS//60}min)")
    print(f"STATS_UPDATE_INTERVAL:    {STATS_UPDATE_INTERVAL_SECONDS}s ({STATS_UPDATE_INTERVAL_SECONDS//60}min)")
    print("=" * 80)


# Optionally print config summary if DEBUG_MODE is enabled
if DEBUG_MODE:
    print_config_summary()
