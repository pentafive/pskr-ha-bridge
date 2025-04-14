# PSKreporter HA Bridge

Connects to the public PSKReporter.info MQTT feed and integrates amateur radio spot data into Home Assistant using MQTT Auto Discovery.

This script listens for spots reported by or heard by a specific callsign, processes the data (including enrichment like country/continent lookup and geo calculations), calculates various statistics, and publishes corresponding sensor entities to Home Assistant via your local MQTT broker.

## Features

* **Flexible Monitoring:** Monitor spots received by your callsign (`RX`), transmitted by your callsign (`TX`), or both (`DUAL`) by editing the `SCRIPT_DIRECTION` variable.
* **Multiple Connection Modes:** Connect to PSKReporter using standard MQTT (1883), MQTTS/TLS (1884), WebSockets (WS, 1885), or Secure WebSockets (WSS, 1886) via the `PSK_TRANSPORT_MODE` variable. Option to disable TLS verification (`PSK_TLS_INSECURE`) for troubleshooting (use with caution!).
* **Home Assistant Auto Discovery:** Automatically creates and updates sensor entities in Home Assistant via MQTT discovery.
* **Organized HA Devices:** Creates two distinct devices in Home Assistant for better organization:
    * `PSKr Spots ({CALLSIGN})`: Holds sensors for individual spots between stations.
    * `PSKr Stats {DIRECTION} ({CALLSIGN})`: Holds sensors for aggregated statistics.
* **Detailed Spot Sensors:** (Optional/Filterable) Creates sensors for each unique Sender -> Receiver pair (e.g., `sensor.pskr_spots_n7ri_kd5qlm`).
    * State: Latest SNR (dB).
    * Attributes: Full callsigns, original locators, frequency, band, mode, calculated distance (km/miles), bearing, session spot count, session min/avg/max SNR, first/last heard timestamps, country/continent for both stations, lat/lon coordinates.
* **Comprehensive Statistics Sensors:** Creates various aggregate statistics sensors calculated over a configurable 15-minute interval, updated every 5 minutes. Separate RX/TX sensors created in DUAL mode. Includes:
    * Per Band & Per Signal Mode: Spot Count, Avg Distance (km), Avg SNR (dB), Unique Stations (Senders/Receivers).
    * Per Band: Unique Countries.
    * Global: Total Unique Countries, Total Spot Count, Total Unique Stations.
    * Activity Indicators: Most Active Band, Most Active Mode (based on spot counts).
* **Spot Sensor Filtering:** Control which individual spot sensors are created/updated via script variables:
    * Global enable/disable flag (`ENABLE_SPOT_SENSORS`).
    * Filter by minimum distance (`SPOT_FILTER_MIN_DISTANCE_KM`).
    * Allow/Filter lists for specific Callsigns (`SPOT_ALLOW_CALLSIGNS`, `SPOT_FILTERED_CALLSIGNS`).
    * Allow/Filter lists for specific Countries by ADIF code (`SPOT_ALLOW_COUNTRIES`, `SPOT_FILTERED_COUNTRIES`).
* **Data Enrichment:**
    * Uses `pyhamtools` to look up Country and Continent based on callsigns.
    * Uses `pyhamtools` to calculate distance, bearing (heading), and Lat/Lon from Maidenhead locators.
    * Attempts to parse common callsign modifiers (`/P`, `PREFIX/`, etc.) before lookup.
    * Handles potentially overly precise locators by truncating for calculations.
* **MQTT Compatibility:** Sanitizes callsigns, bands, modes etc., replacing potentially problematic characters (`.` `/` `#` `+`) with `-` when creating MQTT topics and entity IDs.

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

1.  **Download Script:** Obtain the `pskr-ha-bridge.py` script file and the `requirements.txt` file. Place them in a dedicated directory on the machine where you plan to run the script (e.g., `/home/user/pskr-ha-bridge`).
2.  **Navigate to Directory:** Open a terminal and `cd` into the directory containing the script.
3.  **Create Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    ```
4.  **Activate Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```
    *(Your prompt should change to indicate the active environment, e.g., `(.venv) user@host:...$ `)*
5.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Alternatively: `pip install paho-mqtt pyhamtools websockets`)*
6.  **Configure Script:**
    * Open the `pskr-ha-bridge.py` script in a text editor (like `nano`).
    * Carefully review and **edit the variables in the Configuration section** near the top of the script to match your setup. Pay close attention to `MY_CALLSIGN`, `HA_MQTT_BROKER`, `HA_MQTT_USER`, `HA_MQTT_PASS`, `SCRIPT_DIRECTION`, and any desired Spot Sensor filters.
    * Save the changes to the script file.

## Configuration Variables (Edit in Script)

These variables are located near the top of the `pskr-ha-bridge.py` script file.

* **`MY_CALLSIGN`** (String): **Required.** Your amateur radio callsign.
* **`PSK_BROKER`** (String): Hostname for the PSKReporter MQTT feed. *Default: "mqtt.pskreporter.info"*
* **`PSK_TRANSPORT_MODE`** (String): Connection method to PSKReporter. *Default: "MQTT_WS_TLS"*
    * Options: `"MQTT"`, `"MQTT_TLS"`, `"MQTT_WS"`, `"MQTT_WS_TLS"`
* **`PSK_TLS_INSECURE`** (Boolean): Disable TLS certificate check for PSKReporter connection. **Use `True` with extreme caution.** *Default: False*
* **`HA_MQTT_BROKER`** (String): **Required.** Hostname or IP address of your Home Assistant MQTT broker.
* **`HA_MQTT_PORT`** (Integer): Port for your HA MQTT broker. *Default: 1883*
* **`HA_MQTT_USER`** (String or None): Username for your HA MQTT broker. *Default: None*
* **`HA_MQTT_PASS`** (String or None): Password for your HA MQTT broker. *Default: None*
* **`SCRIPT_DIRECTION`** (String): Which spots to monitor relative to `MY_CALLSIGN`. *Default: "rx"*
    * Options: `"rx"`, `"tx"`, `"dual"`
* **`STATS_INTERVAL_WINDOW_SECONDS`** (Integer): Calculation window for all stats in seconds. *Default: 900* (15 minutes)
* **`STATS_UPDATE_INTERVAL_SECONDS`** (Integer): How often stats are recalculated and published. *Default: 300* (5 minutes)
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
3.  **Keep it Running:** The script needs to run continuously in the background. You can use tools like:
    * `screen` or `tmux`: Simple terminal multiplexers.
    * `nohup`: Basic background execution (`nohup python3 pskr-ha-bridge.py &`).
    * `systemd`: Create a system service for robust background operation and auto-restart (Recommended for long-term use).

Check the script's console output for connection status and potential warnings or errors.

## Home Assistant Integration

Once the script is running and connected to your HA MQTT broker:

1.  Navigate to **Settings -> Devices & Services -> MQTT**.
2.  You should see **two new devices** discovered after a short time:
    * `PSKr Spots ({MY_CALLSIGN})`
    * `PSKr Stats {DIRECTION} ({MY_CALLSIGN})`
3.  Click into these devices to see the associated sensor entities created by the script. Individual spot sensors will appear as they are received (if enabled and not filtered). Statistics sensors will appear and update after the first calculation interval (default 5 minutes).
4.  Add these sensors to your Lovelace dashboards!

## Troubleshooting

* **Script doesn't start:** Check Python version, ensure dependencies are installed in the active `venv` (`pip list`). Check for syntax errors if you edited the script heavily.
* **No Connection to PSKReporter:** Check firewall rules for the selected port (1883, 1884, 1885, 1886). Try switching `PSK_TRANSPORT_MODE` in the script config. Ensure machine has internet access. Check script logs.
* **No Connection to HA MQTT:** Verify `HA_MQTT_BROKER`, `HA_MQTT_PORT`, `HA_MQTT_USER`, `HA_MQTT_PASS` in the script config. Check HA MQTT broker logs. Check script logs.
* **Missing `websockets` library Error:** If using `MQTT_WS` or `MQTT_WS_TLS`, ensure the library was installed (`pip install websockets`).
* **`pyhamtools` errors:** On first run, `pyhamtools` might need to download country files - ensure the script has internet access and write permissions if needed for caching (usually writes to `~/.pyhamtools`). Check script logs for download errors.
* **Sensors Stuck at "Unknown" (Initial State):** Ensure script is running and connected to HA MQTT. Check MQTT Explorer to verify discovery and state messages are being published. The script uses QoS=1 for spot sensor state and includes delays which should mitigate this, but heavy system load could still cause issues. Check script and HA logs.
* **Too Many Spot Sensors:** Set `ENABLE_SPOT_SENSORS=False` in the script config or configure the filtering options (`SPOT_ALLOW_CALLSIGNS`, `SPOT_FILTER_ADIF`, `SPOT_MIN_DIST`, etc.). Restart the script after changes.
* **Incorrect Stats/Sensors:** Set `DEBUG_MODE=True` in the script config and check the script console logs for processing details and potential warnings. Verify the data in MQTT Explorer.

## License

This project is licensed under the MIT License.

## Acknowledgements

* **Philip Gladstone, N1DQ:** For creating and maintaining the invaluable [PSKReporter.info](https://pskreporter.info/) service.
* **Tom, M0LTE:** For providing and maintaining the public MQTT feed at `mqtt.pskreporter.info`.
* **Home Assistant Project:** For the amazing home automation platform.
* **Eclipse Paho™ MQTT Python Client Library:** (`paho-mqtt`).
* **PyHamtools:** Library for amateur radio functions (`pyhamtools`).
* **Websockets:** Python library (`websockets`).
