# PSKreporter HA Bridge

Connects to the public PSKReporter.info MQTT feed and integrates amateur radio spot data into Home Assistant using MQTT Auto Discovery.

This script listens for spots reported by or heard by a specific callsign, processes the data (including enrichment like country/continent lookup and geo calculations), calculates various statistics, and publishes corresponding sensor entities to Home Assistant via your local MQTT broker.

## Features

* **Flexible Monitoring:** Monitor spots received by your callsign (`RX`), transmitted by your callsign (`TX`), or both (`DUAL`) via the `SCRIPT_DIRECTION` variable.
* **Multiple Connection Modes:** Connect to PSKReporter using standard MQTT (1883), MQTTS/TLS (1884), WebSockets (WS, 1885), or Secure WebSockets (WSS, 1886) via the `PSK_TRANSPORT_MODE` variable. Option to disable TLS verification (`PSK_TLS_INSECURE`) for troubleshooting (use with caution!).
* **Home Assistant Auto Discovery:** Automatically creates and updates sensor entities in Home Assistant via MQTT discovery.
* **Organized HA Devices:** Creates dedicated devices in Home Assistant: `PSKr Spots ({CALLSIGN})` for individual spots, and `PSKr Stats {DIRECTION} ({CALLSIGN})` for aggregate statistics (in `DUAL` mode, both `Stats RX` and `Stats TX` devices are created).
* **Detailed Spot Sensors:** (Optional/Filterable) Creates sensors for each unique Sender -> Receiver pair (e.g., `sensor.pskr_spots_n7ri_kd5qlm`).
    * State: Latest SNR (dB).
    * Attributes: Full callsigns, original locators, frequency, band, mode, calculated distance (km/miles), bearing, session spot count, session min/avg/max SNR, first/last heard timestamps, country/continent for both stations, lat/lon coordinates.
* **Comprehensive Statistics Sensors:** Creates various aggregate statistics sensors calculated over a configurable **15-minute interval** (`STATS_INTERVAL_WINDOW_SECONDS`), updated periodically (default 5 minutes via `STATS_UPDATE_INTERVAL_SECONDS`). Separate RX/TX sensors created in DUAL mode. Includes:
    * **Per Band & Per Signal Mode:** Spot Count, Avg Distance (km), Avg SNR (dB), Unique Stations (Senders/Receivers).
    * **Per Band:** Unique Countries.
    * **Global:** Total Unique Countries, Total Spot Count, Total Unique Stations, Min/Avg/Max Distance (km), Min/Avg/Max SNR (dB).
    * **Activity Indicators:** Most Active Band (State=Name, Attr=Count), Most Active Mode (State=Name, Attr=Count).
* **Spot Sensor Filtering:** Control which individual spot sensors are created/updated via script variables:
    * Global enable/disable flag (`ENABLE_SPOT_SENSORS`).
    * Filter by minimum distance (`SPOT_FILTER_MIN_DISTANCE_KM`).
    * Allow/Filter lists for specific Callsigns (`SPOT_ALLOW_CALLSIGNS`, `SPOT_FILTERED_CALLSIGNS`).
    * Allow/Filter lists for specific Countries by ADIF code (`SPOT_ALLOW_COUNTRIES`, `SPOT_FILTERED_COUNTRIES`).
* **Data Enrichment & Processing:**
    * Uses `pyhamtools` to look up Country and Continent based on cleaned callsigns.
    * Uses `pyhamtools` to calculate distance, bearing (heading), and Lat/Lon from Maidenhead locators (truncating inputs for compatibility).
    * Sanitizes various strings (`.`->`-`, etc.) for MQTT/HA compatibility.
    * Uses `device_class` (`distance`, `signal_strength`) for relevant sensors for better HA display.

## Requirements

* **Python 3:** Version 3.9 or higher recommended (tested with 3.12).
* **Pip:** Python package installer.
* **Python Virtual Environment (`venv`):** Strongly recommended to isolate dependencies.
* **Required Python Libraries:** `paho-mqtt`, `pyhamtools`, `websockets` (installable via `requirements.txt`).
* **MQTT Broker:** An MQTT broker accessible on your network.
    * _Recommended:_ The [Mosquitto broker Home Assistant Add-on](https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md).
    * Ensure the broker is configured with user credentials if required by your setup.
* **Home Assistant MQTT Integration:**
    * The [MQTT Integration](https://www.home-assistant.io/integrations/mqtt/) must be installed and configured in your Home Assistant instance to connect to your MQTT Broker.
    * You can typically add or configure this under **Settings -> Devices & Services**. Click **+ Add Integration** and search for MQTT if you haven't set it up yet.
* **MQTT Discovery Enabled in Home Assistant:**
    * For the sensors created by this script to appear automatically, MQTT Discovery must be enabled within the Home Assistant MQTT Integration settings.
    * **To check/enable:** Go to **Settings -> Devices & Services**, find your configured **MQTT** integration card, click **Configure**, and ensure **"Enable discovery"** (or similar wording) is checked.
    * The default **Discovery prefix** should typically be `homeassistant` (which matches the script's default `HA_DISCOVERY_PREFIX`). If you have changed the prefix in Home Assistant, you *must* edit the `HA_DISCOVERY_PREFIX` variable in the script to match.

## Installation & Setup

1.  **Download Script:** Obtain the `pskr-ha-bridge.py` script file and the `requirements.txt` file. Place them in a dedicated directory (e.g., `/home/user/pskr-ha-bridge`).
2.  **Navigate to Directory:** Open a terminal and `cd` into the directory containing the script.
3.  **Create Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    ```
4.  **Activate Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```
    *(Your prompt should change, e.g., `(.venv) user@host:...$ `)*
5.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
6.  **Configure Script:**
    * Open the `pskr-ha-bridge.py` script in a text editor (like `nano`).
    * Carefully review and **edit the variables in the Configuration section** near the top. Pay close attention to `MY_CALLSIGN`, `HA_MQTT_BROKER`, `HA_MQTT_USER`, `HA_MQTT_PASS`, `SCRIPT_DIRECTION`, and any desired Spot Sensor filters.
    * Save the changes.

## Configuration Variables (Edit in Script)

These variables are located near the top of the `pskr-ha-bridge.py` script file.

* **`MY_CALLSIGN`** (String): **Required.** Your amateur radio callsign.
* **`PSK_BROKER`** (String): Hostname for the PSKReporter MQTT feed. *Default: "mqtt.pskreporter.info"*
* **`PSK_TRANSPORT_MODE`** (String): Connection method to PSKReporter. *Default: "MQTT_WS_TLS"*
    * Options: `"MQTT"`, `"MQTT_TLS"`, `"MQTT_WS"`, `"MQTT_WS_TLS"`
* **`PSK_TLS_INSECURE`** (Boolean): Disable TLS certificate check for PSKReporter. **USE WITH CAUTION.** *Default: False*
* **`HA_MQTT_BROKER`** (String): **Required.** Hostname or IP address of your HA MQTT broker.
* **`HA_MQTT_PORT`** (Integer): Port for your HA MQTT broker. *Default: 1883*
* **`HA_MQTT_USER`** (String or None): Username for your HA MQTT broker. *Default: None*
* **`HA_MQTT_PASS`** (String or None): Password for your HA MQTT broker. *Default: None*
* **`SCRIPT_DIRECTION`** (String): Which spots to monitor. *Default: "rx"*
    * Options: `"rx"`, `"tx"`, `"dual"`
* **`STATS_INTERVAL_WINDOW_SECONDS`** (Integer): Calculation window for all stats in seconds. *Default: 900* (15 minutes)
* **`STATS_UPDATE_INTERVAL_SECONDS`** (Integer): How often stats are recalculated/published. *Default: 300* (5 minutes)
* **`ENABLE_SPOT_SENSORS`** (Boolean): Master switch for creating individual spot sensors. *Default: True*
* **`SPOT_FILTER_MIN_DISTANCE_KM`** (Integer): Only process spots with distance > value (Km). Set <= 0 to disable. *Default: 0*
* **`SPOT_ALLOW_CALLSIGNS`** (List of Strings): Keep spots involving these calls (case-insensitive). Empty list allows all not filtered. *Default: []*
* **`SPOT_FILTERED_CALLSIGNS`** (List of Strings): Discard spots involving these calls (case-insensitive). Empty list filters none. *Default: []*
* **`SPOT_ALLOW_COUNTRIES`** (List of Integers): Keep spots involving these ADIF country codes. Empty list allows all not filtered. *Default: []* (See [ADIF Files](https://www.country-files.com/category/adif-country-files/) for codes)
* **`SPOT_FILTERED_COUNTRIES`** (List of Integers): Discard spots involving these ADIF country codes. Empty list filters none. *Default: []*
* **`HA_DISCOVERY_PREFIX`** (String): MQTT discovery prefix used by Home Assistant. *Default: "homeassistant"*
* **`HA_ENTITY_BASE`** (String): Base prefix for entity IDs and MQTT topics created by this script. *Default: "pskr"*
* **`DEBUG_MODE`** (Boolean): Enable verbose logging to the console. *Default: False*
* **`MAX_SPOT_HISTORY`** (Integer): Max number of spots to keep in memory for stats. *Default: 5000*
* **`MODES_FILTER`** (String): Filter for signal modes in PSKReporter topic subscription. *Default: "+"* (All modes)

## Usage

1.  **Activate Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```
2.  **Run the Script:**
    ```bash
    python3 pskr-ha-bridge.py
    ```
3.  **Keep it Running:** Use `screen`, `tmux`, `nohup`, or preferably set up a `systemd` service to run the script continuously in the background.

Check the script's console output for status, warnings, or errors.

## Home Assistant Integration

Once the script is running and connected to your HA MQTT broker:

1.  Navigate to **Settings -> Devices & Services -> MQTT**.
2.  You should see **new devices** discovered after a short time:
    * `PSKr Spots ({MY_CALLSIGN})`
    * `PSKr Stats RX ({MY_CALLSIGN})` (If `SCRIPT_DIRECTION` is `rx` or `dual`)
    * `PSKr Stats TX ({MY_CALLSIGN})` (If `SCRIPT_DIRECTION` is `tx` or `dual`)
3.  Click into these devices to see the associated sensor entities. Spot sensors appear as spots are received (and pass filters). Statistics sensors appear and update after the first calculation interval (default 5 minutes).
4.  Add these sensors to your Lovelace dashboards!

## Troubleshooting

* **Script doesn't start:** Check Python version, ensure dependencies installed in active `venv` (`pip list`). Check for syntax errors after editing config.
* **No Connection to PSKReporter:** Check firewall rules for the selected port. Try switching `PSK_TRANSPORT_MODE`. Ensure internet access. Check script logs.
* **No Connection to HA MQTT:** Verify `HA_MQTT_` variables in script config. Check HA MQTT broker logs. Check script logs.
* **Missing `websockets` library Error:** If using `MQTT_WS` or `MQTT_WS_TLS`, run `pip install websockets` in your venv.
* **`pyhamtools` errors / No Enrichment:** On first run, `pyhamtools` might need to download data files - ensure internet access. Check script logs for download errors. Ensure `pyhamtools_lookups_ok` is True in startup logs.
* **Sensors Stuck at "Unknown" (Initial State):** Ensure script is running and connected to HA MQTT. Check MQTT Explorer for discovery and state messages. Check script and HA logs. QoS=1 and delays should mitigate this.
* **Too Many Spot Sensors:** Set `ENABLE_SPOT_SENSORS=False` or configure the filtering options in the script. Restart script after changes.
* **Incorrect Stats/Sensors:** Set `DEBUG_MODE=True` and check script console logs. Verify data in MQTT Explorer. Check system time/timezone settings where the script runs.

## License

This project is licensed under the MIT License.

## Acknowledgements

* **Philip Gladstone, N1DQ:** For creating and maintaining the invaluable [PSKReporter.info](https://pskreporter.info/) service.
* **Tom, M0LTE:** For providing and maintaining the public MQTT feed at `mqtt.pskreporter.info`.
* **Home Assistant Project:** For the amazing home automation platform.
* **Eclipse Paho™ MQTT Python Client Library:** (`paho-mqtt`).
* **PyHamtools:** Library for amateur radio functions (`pyhamtools`).
* **Websockets:** Python library (`websockets`).
