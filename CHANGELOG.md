# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2026-02-07

### Added
- **Activity Heatmap** - Rolling 24-hour activity matrix (hour x band) as sensor attribute for visualization
  - New `activity_heatmap` sensor (personal + global) — state is total 24h spots, attribute contains full 24x10 matrix
  - Counts ALL messages (unaffected by sample rate) for accurate activity representation
- **Dashboard Generator Presets** - `--preset minimal|standard|full` for different complexity levels
  - Minimal: Native HA cards only (no HACS frontend dependencies)
  - Standard: Existing behavior (mushroom + mini-graph-card)
  - Full: Standard + per-band breakdowns and comparison charts
  - Web UI preset dropdown with auto-configuration

### Fixed
- **Disconnect Log Spam (v2)** - Replaced v2.5.0 boolean flag with timestamp-based rate limiting (max 1 WARNING per 300 seconds during extended outages, with disconnect count summary)
  - v2.5.0 fix reset the flag on every reconnect — production logs showed 2,348 warnings in 5.5 hours during unstable connections
  - Reconnection INFO logs demoted to DEBUG when connection was unstable (<30s since last warning)
  - Docker bridge: same rate-limiting applied to both PSKReporter and HA broker disconnects

### Changed
- Sensor count: Personal mode 79 → 80 sensors (+1 `activity_heatmap`)
- Global mode 22 → 23 sensors (+1 `activity_heatmap`)

### Technical
- `_disconnect_warn_time`/`_disconnect_count`/`_stable_connect_time` replace `_disconnect_logged` boolean
- `_hourly_counts` dict with `defaultdict(int)` per hour-band bucket, pruned to 24h window
- `_build_activity_heatmap()` produces full 24x10 matrix with all hours (0-23) and all HF_BANDS
- Dashboard `PRESETS` dict controls template, bands, comparison per tier
- New `minimal-section.yaml` template with native HA entity cards

---

## [2.5.1] - 2026-02-06

### Fixed
- **ReasonCode TypeError** - Fix `TypeError: int() argument must be a string` crash on MQTT disconnect with paho-mqtt v2 (`ReasonCode` object now accessed via `.value` attribute)

---

## [2.5.0] - 2026-02-06

### Added
- **DXCC Name Mapping** - Country names now appear alongside ADIF numeric codes in sensor attributes (`countries_list`, `farthest_station`, wanted events)
- **Bearing/Direction Sensor** - New `dominant_direction` sensor showing compass direction (N/NE/E/SE/S/SW/W/NW) with most spots, plus `bearing_degrees` attribute
- **Farthest Station Enrichment** - `farthest_station` sensor now includes `bearing_degrees` and `country` attributes
- **Dashboard Generator: `views:` Wrapper** - Generated YAML now wrapped in `views:` array for direct paste into HA's Raw Configuration Editor (CLI: `--no-views-wrapper` to disable; Web: checkbox)
- **Dashboard Generator: Global-Only Option** - Generate dashboard for global monitor without requiring a callsign (CLI: `--global-only`; Web: monitor type selector)
- **BMC Support Badge** - Buy Me a Coffee badge and support section in README

### Fixed
- **MQTT Disconnect Log Spam** - First disconnect logs WARNING, subsequent disconnects before reconnect log DEBUG only (was: WARNING on every disconnect causing 224+ warnings in 32 minutes)
- **Better Disconnect Reasons** - Human-readable disconnect reason messages with paho-mqtt reason code mapping

### Changed
- Sensor count: Personal mode 78 → 79 sensors (+1 `dominant_direction`)
- README: Added attribution blockquote, support section, and disclaimer; replaced Acknowledgements section
- Per-band `countries_list` attributes now include country names (e.g., `"291 (United States)"`)

### Technical
- New `dxcc_names.py` module with ~340 ADIF DXCC entity code → country name mappings
- `_on_disconnect` rate-limiting via `_disconnect_logged` flag, reset on reconnect
- `_format_disconnect_reason()` maps paho-mqtt reason codes to human-readable strings
- `_calculate_heading()` and `_bearing_to_compass()` helper methods
- `SpotData.sender_azimuth` now populated from pyhamtools heading calculation
- `PSKReporterData` extended with `dominant_bearing`, `dominant_direction`, `farthest_station_bearing`, `farthest_station_country`
- Docker bridge: disconnect log rate-limiting with per-client flags

---

## [2.4.0] - 2026-02-02

### Added
- **Band Filter** - Filter spots by amateur radio band (e.g., 20m, 40m, 6m)
  - HACS: Multi-select dropdown in integration options
  - Docker: `SPOT_BAND_FILTER` environment variable (comma-separated)
- **DXCC/Band Wanted List** - Detector system that fires events when specific DXCC/band combinations are spotted
  - Configure inline as comma-separated `DXCC:BAND` pairs (e.g., `339:20m,150:40m`)
  - HACS: Text input in integration options
  - Docker: `DXCC_WANTED` environment variable
  - New `pskr_wanted_spot` Home Assistant event fired on match (HACS mode)
  - Direction-aware: RX checks sender DXCC, TX checks receiver DXCC, Dual checks both
- **Wanted Match Sensors** (Personal mode only):
  - `wanted_match` binary sensor - ON when a wanted DXCC/band match occurs within the stats window
  - `wanted_match_count` sensor - Number of wanted matches in the current stats window
  - `wanted_list_size` sensor - Number of entries in the configured wanted list

### Technical
- New `wanted_list.py` shared parser module with `parse_wanted_list()` and `format_wanted_list()`
- Added `CONF_DXCC_WANTED` and `EVENT_WANTED_SPOT` constants
- Band filter uses O(1) set lookup in `_should_include_spot()`
- Wanted matching runs on all valid spots independent of spot sensor filters (detector, not filter)

---

## [2.3.1] - 2026-01-24

### Added
- **Dashboard Generator** - Web-based tool to generate customized dashboards for your callsign
  - Visit [Dashboard Generator](https://pentafive.github.io/pskr-ha-bridge/dashboard-generator.html)
  - Enter callsign, optionally add second callsign for comparison view
  - Generates complete Lovelace YAML with all v2.3.0 sensors
- **CLI Dashboard Generator** - Command-line alternative (`examples/dashboards/generate_dashboard.py`)
- **Template System** - Dashboard templates for maintainable generation
  - Templates in `examples/dashboards/templates/`
  - Both web and CLI generators use same templates
  - Template updates automatically propagate to users

### Changed
- **Example Dashboards** - Removed hardcoded callsigns, now use placeholders
- **Documentation** - Updated README and wiki with generator links

---

## [2.3.0] - 2026-01-24

### Added
- **Extended Distance Stats** - New sensors: `min_distance`, `avg_distance` for distance range analysis
- **SNR Range Sensors** - New sensors: `min_snr`, `max_snr` showing signal quality range
- **Geographic Tracking** - `unique_countries` sensor with DXCC country list attribute
- **Farthest Station** - `farthest_station` sensor showing the callsign of the most distant contact with distance attribute
- **Temporal Metrics** - `spots_last_hour` sensor for hourly activity tracking
- **DX Ratio** - `dx_ratio` sensor showing percentage of spots beyond 5000 km
- **Propagation Score** - `propagation_score` composite metric (spots × countries × distance/1000)
- **Per-Band Statistics (Personal Mode)** - 50 new sensors (10 HF bands × 5 metrics):
  - `{band}_spots` - Spot count per band
  - `{band}_avg_snr` - Average SNR per band
  - `{band}_max_distance` - Maximum distance per band
  - `{band}_unique_stations` - Unique stations per band
  - `{band}_unique_countries` - Unique countries per band

### Changed
- **Sensor Count** - Personal mode now has 75 sensors (was 16), Global unchanged at 22
- **Per-Band Attributes** - Band sensors include contextual attributes (dominant_mode, countries list, SNR range)

### Technical
- Added `BandStats` dataclass for per-band statistics
- Extended `PSKReporterData` with 14 new fields
- Added `PSKReporterPersonalBandSensor` class for per-band metrics
- Added `DX_THRESHOLD_KM` constant (5000 km)

---

## [2.2.0] - 2026-01-23

### Added
- **Activity-Aware Health Thresholds** - Personal monitors now use 300-second threshold (was 60s), Global monitors keep 60-second threshold
- **Granular Feed Status** - New states: `healthy`, `low_activity`, `stale`, `disconnected` (replaces binary on/off)
- **Enhanced Health Attributes** - Feed sensors now expose `feed_status`, `feed_status_reason`, and `health_threshold_seconds`
- **Configurable Transport Mode** - Choose between WebSocket+TLS (default), TCP+TLS, WebSocket, or TCP plain in integration options
- **Transport Info in Sensors** - Connection status sensor now shows `transport_mode` and `transport_port` attributes

### Changed
- **Feed Health Binary Sensor** - Now uses activity-aware thresholds from coordinator instead of hardcoded 60 seconds
- **Feed Status Sensor** - Shows human-readable status (e.g., "Low Activity") instead of just "Healthy" or "Stale"
- **Health Reason Messages** - Improved explanations (e.g., "Low activity (normal during low propagation)")
- **MQTT Connection** - No longer hardcoded to WebSocket+TLS; uses configured transport from options

### Fixed
- **False Unhealthy Alarms** - Personal callsign monitors no longer show constant "unhealthy" status during normal 1-10 minute gaps between spots
- **Data Analysis** - Based on 576,951 records over 3 days showing 2,054 false toggles vs only 5 actual disconnects

---

## [2.1.1] - 2026-01-05

### Fixed
- **Timestamp Sensor Bug** - `last_spot` sensor now returns proper `datetime` object with UTC timezone instead of ISO string, fixing `'str' object has no attribute 'tzinfo'` error
- **Options Flow 500 Error** - Fixed invalid multi-select syntax that caused "Server got itself in trouble" error when editing integration options

### Changed
- **Improved Setup Flow** - Two-step configuration: first choose monitor type (Personal/Global), then only relevant options are shown
- Global monitor setup no longer asks for callsign or direction (not applicable)
- Mode filter now uses proper dropdown multi-select UI

---

## [2.1.0] - 2026-01-04

### Added
- **Callsign Filtering (HACS)** - Allow/block lists for callsigns, ported from Docker bridge
- **Country Filtering (HACS)** - Allow/block lists for DXCC country codes, ported from Docker bridge
- Options flow now supports comma-separated input for callsign and country filters
- **Home Assistant Brand Registration** - Official icon now appears in HA integrations list ([PR #8971](https://github.com/home-assistant/brands/pull/8971))

### Changed
- All version references updated to 2.1.0

---

## [2.0.1] - 2026-01-04

### Fixed
- **Global Monitor Unique ID** - Binary sensor now generates valid unique_id for global mode (was creating invalid `__feed_health`)
- **Global Monitor Device Info** - Binary sensor now correctly associates with Global Monitor device in HA
- **Azimuth Field Parsing** - Removed incorrect parsing of DXCC country codes as azimuth values

---

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
