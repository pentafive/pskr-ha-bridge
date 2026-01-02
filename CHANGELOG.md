# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-02

### Added
- **Native HACS Integration** - Full Home Assistant custom component with ConfigFlow UI
- **Dual Deployment Architecture** - Choose between HACS (no MQTT broker required) or Docker
- **DataUpdateCoordinator** - Modern Home Assistant integration pattern
- **Options Flow** - Configure filtering options post-installation
- **Multi-language Support** - Translations framework with English strings
- **CI/CD Pipelines** - GitHub Actions for Ruff linting, hassfest, and HACS validation
- **Community Documentation** - CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md

### Changed
- **Configuration** - Docker mode now uses environment variables (config.py module)
- **Version Bump** - Major version for breaking changes in architecture
- **README** - Complete rewrite for dual deployment documentation

### Migration from v1.x

**Docker Users:** Your existing setup continues to work. Update `.env` file with configuration (previously hardcoded in script).

**New HACS Users:** Install via HACS for native integration - no MQTT broker required.

---

## [1.4.8] - 2025-04-14

### Fixed
- Resolved `NameError: name 'publish_global_country_update' is not defined` in periodic stats task by replacing the call with the correct `publish_stat_update` function.
- Resolved `AttributeError: 'NoneType' object has no attribute 'lower'` during MQTT client initialization by passing `transport="tcp"` instead of `None` for non-WebSocket modes.

---

## [1.4.7] - 2025-04-13

### Added
- New global statistics sensors (calculated over 15min interval):
    - Total Spot Count (`..._total_spots`)
    - Total Unique Stations (Senders/Receivers) (`..._total_unique_stations`)
    - Min/Avg/Max Distance (`..._total_min_dist`, `..._total_avg_dist`, `..._total_max_dist`)
    * Min/Avg/Max SNR (`..._total_min_snr`, `..._total_avg_snr`, `..._total_max_snr`)
    * Active Band Count (`..._active_bands`)
    * Most Active Band (State: Band Name, Attr: Count) (`..._most_active_band`)
    * Most Active Mode (State: Mode Name, Attr: Count) (`..._most_active_mode`)
    * Global Spot Count Per Mode (`..._mode_{mode}_count`)
    * Global Unique Stations Per Mode (`..._mode_{mode}_unique_stations`)
- `device_class` attribute (`distance`, `signal_strength`) added to relevant sensor discovery payloads for better HA integration.
- Debug logging feature controlled by `DEBUG_MODE` flag.
- More comments throughout the code for clarity.
- Initial connection wait loop to ensure brokers are connected before proceeding.
- `on_disconnect` handlers to log unexpected MQTT disconnections.

### Changed
- **Consolidated Statistics Interval:** All aggregate statistics sensors now calculate based *only* on the `STATS_INTERVAL_WINDOW_SECONDS` (default 15 minutes). Removed calculations based on the 1-hour window.
- **Sensor Naming:** Removed "KM" and interval suffixes (e.g., "(15min)") from statistics sensor friendly names. Changed average distance metric ID from `avg_dist_km` to `avg_dist`.
- **Spot Sensor State:** Set QoS to 1 for potentially more reliable initial state updates after discovery. Increased post-discovery delay to 0.5s.
- **Code Structure:** Refactored statistics discovery publishing into a more generic `publish_stat_discovery` function. Refactored device config generation. Improved thread locking in `on_message_psk`.

### Fixed
- Corrected `pyhamtools` callsign lookup method to use `callinfo.get_all()`.
- Fixed `NameError` for `publish_global_country_update` by replacing with correct call to `publish_stat_update`.
- Fixed `AttributeError` potentially caused by incorrect positional arguments passed to `publish_stat_discovery` within the periodic stats task.

---

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
