# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.6] - 2025-04-13

Initial commit to GitHub. This version includes the core functionality for bridging PSKReporter data to Home Assistant with several configuration options and features developed during initial testing.

### Features

* **Core Functionality:** Connects to PSKReporter.info MQTT feed, processes spots, calculates statistics, and publishes sensors to a local Home Assistant MQTT broker using Auto Discovery.
* **Direction Modes:** Supports monitoring spots Received (`rx`), Transmitted (`tx`), or `dual`, configured via `SCRIPT_DIRECTION`.
* **Connection Flexibility:** Supports connecting to PSKReporter via `MQTT` (1883), `MQTT_TLS` (1884), `MQTT_WS` (1885), or `MQTT_WS_TLS` (1886) via `PSK_TRANSPORT_MODE`. Includes `PSK_TLS_INSECURE` option.
* **Home Assistant Integration:**
    * Creates three distinct HA Devices in DUAL mode (`PSKr Spots ({CALLSIGN})`, `PSKr Stats RX ({CALLSIGN})`, `PSKr Stats TX ({CALLSIGN})`). Creates two devices in RX/TX mode.
    * Uses `pskr_` base for entity IDs/topics.
    * MQTT Auto Discovery used for all sensors.
* **Spot Sensors:**
    * (Optional via `ENABLE_SPOT_SENSORS`) Creates sensors per Sender->Receiver pair.
    * State = SNR (dB), uses QoS=1 for state updates.
    * Includes delay after discovery to help with initial state.
    * Rich Attributes: Callsigns, locators, frequency, band, mode, Country/Continent, Lat/Lon, distance (km/miles), bearing, session stats (count, min/avg/max SNR, first/last heard).
    * Configurable Filtering: Enable/disable globally, filter by min distance, Allow/Filtered Callsign lists, Allow/Filtered Country (ADIF code) lists.
* **Statistics Sensors (Mixed Intervals):**
    * Calculates stats periodically (default every 5 minutes).
    * **15-min Interval Stats:** Spot Counts (Per-Band-Per-Mode, Global Per-Mode, Global Total, Per-Band Country, Global Country), Avg Distance (Per-Band-Per-Mode), Unique Stations (Per-Band-Per-Mode, Global Per-Mode, Global Total).
    * **1-hr Interval Stats:** Spot Count (Per-Band-Per-Mode), Avg Distance (Per-Band-Per-Mode), Avg SNR (Per-Band-Per-Mode), Unique Stations (Per-Band-Per-Mode). *(Note: This dual interval approach was simplified in later versions)*.
    * **Activity Indicators:** Most Active Band and Most Active Mode (based on 15min counts).
* **Data Processing:**
    * Dynamically uses `sl`/`rl` locators from messages.
    * Truncates locators (6-char for dist/head, 8-char for lat/lon).
    * Uses `calculate_heading`.
    * Cleans callsigns (`get_base_callsign`) before lookup.
    * Uses `pyhamtools` `get_all()` method for lookup.
    * Sanitizes strings for MQTT/HA compatibility.
* **Other:** Includes `DEBUG_MODE` flag, basic error handling, V2 API callbacks, reconnect logic, initial connection checks. Uses hardcoded Python variables for configuration.

### Known Issues in this Version
* The periodic statistics update task (`update_band_stats_task`) may crash due to a `NameError` when trying to update global country stats and potentially an `AttributeError` when publishing discovery for certain statistics due to incorrect function arguments/definitions. These are fixed in v1.4.7.
