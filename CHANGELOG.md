# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (conceptually, starting point is 1.4.7).

## [1.4.7] - 2025-04-13

This version represents the first documented state of the script, incorporating numerous features and fixes developed during initial creation.

### Features

* **Core Functionality:** Connects to PSKReporter.info MQTT feed, processes spots, calculates statistics, and publishes sensors to a local Home Assistant MQTT broker using Auto Discovery.
* **Direction Modes:** Supports monitoring spots Received (`rx`), Transmitted (`tx`), or `dual`, configured via `SCRIPT_DIRECTION`. Subscribes to appropriate MQTT topics based on mode.
* **Connection Flexibility:** Supports connecting to PSKReporter via `MQTT` (1883), `MQTT_TLS` (1884), `MQTT_WS` (1885), or `MQTT_WS_TLS` (1886) via `PSK_TRANSPORT_MODE`. Includes an option (`PSK_TLS_INSECURE`) to disable TLS verification (use with caution).
* **Home Assistant Integration:**
    * Creates two distinct HA Devices: `PSKr Spots ({CALLSIGN})` and `PSKr Stats {DIRECTION} ({CALLSIGN})`.
    * Uses `pskr_` base for entity IDs/topics (e.g., `sensor.pskr_spots_...`, `sensor.pskr_stats_...`).
    * Applies appropriate `device_class` (`signal_strength`, `distance`) to sensors.
    * Uses simplified friendly names (e.g., `W1AW -> KD5QLM`, `20m FT8 Count`).
* **Spot Sensors:**
    * (Optional via `ENABLE_SPOT_SENSORS`) Creates sensors per Sender->Receiver pair.
    * State = SNR (dB), QoS=1 used for reliability.
    * Includes delay after discovery to mitigate initial "Unknown" state.
    * Rich Attributes: Callsigns, original locators, band, mode, frequency, Country/Continent, Lat/Lon, distance (km/miles), bearing, session stats (count, min/avg/max SNR, first/last heard).
    * Filtering: Allows enabling/disabling globally, filtering by min distance, Allow/Filtered Callsign lists, Allow/Filtered Country (ADIF code) lists.
* **Statistics Sensors (15min Interval):**
    * All aggregate stats calculated over a 15-minute window, updated every 5 minutes.
    * Separate RX/TX sensors created in DUAL mode.
    * Per Band & Signal Mode: Sensors for Count, Avg Distance, Avg SNR, Unique Stations (Senders/Receivers).
    * Per Band: Sensor for Unique Countries.
    * Global: Sensors for Total Unique Countries, Total Spot Count, Total Unique Stations.
    * Activity Indicators: Sensors for Most Active Band and Most Active Mode (State=Name, Attribute=Count).
* **Data Processing & Enrichment:**
    * Dynamically uses `sl`/`rl` locators from messages for geo calculations.
    * Truncates locators (6-char for dist/heading, 8-char for lat/lon) for `pyhamtools` compatibility.
    * Cleans callsigns (removes `/P`, `PREFIX/` etc.) using `get_base_callsign` before lookup.
    * Uses correct `pyhamtools` methods (`calculate_heading`, `get_all`).
    * Enriches spot attributes with Country, Continent, Lat/Lon data.
    * Sanitizes various strings (`.`->`-`) for MQTT/HA compatibility.
* **Configuration:** Uses hardcoded variables within the Python script (this version).
* **Other:** Includes `DEBUG_MODE`, robust connection/disconnection handling, initial connection checks, `pyhamtools` initialization with error handling.
