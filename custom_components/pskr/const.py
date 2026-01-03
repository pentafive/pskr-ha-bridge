"""Constants for the PSKReporter Monitor integration."""

from typing import Final

DOMAIN: Final = "pskr"

# Configuration keys
CONF_CALLSIGN: Final = "callsign"
CONF_DIRECTION: Final = "direction"
CONF_MIN_DISTANCE: Final = "min_distance"
CONF_MAX_DISTANCE: Final = "max_distance"
CONF_COUNTRY_FILTER: Final = "country_filter"
CONF_BAND_FILTER: Final = "band_filter"
CONF_MODE_FILTER: Final = "mode_filter"

# Direction options
DIRECTION_RX: Final = "rx"
DIRECTION_TX: Final = "tx"
DIRECTION_DUAL: Final = "dual"

DIRECTION_OPTIONS: Final = [DIRECTION_RX, DIRECTION_TX, DIRECTION_DUAL]

# PSKReporter MQTT settings
PSK_BROKER: Final = "mqtt.pskreporter.info"
PSK_PORT_MQTT: Final = 1883
PSK_PORT_MQTT_TLS: Final = 1884
PSK_PORT_WS: Final = 1885
PSK_PORT_WS_TLS: Final = 1886

# Transport modes
TRANSPORT_MQTT: Final = "MQTT"
TRANSPORT_MQTT_TLS: Final = "MQTT_TLS"
TRANSPORT_WS: Final = "WS"
TRANSPORT_WS_TLS: Final = "WS_TLS"

# Default settings
DEFAULT_DIRECTION: Final = DIRECTION_RX
DEFAULT_TRANSPORT: Final = TRANSPORT_MQTT
DEFAULT_MIN_DISTANCE: Final = 0
DEFAULT_MAX_DISTANCE: Final = 0  # 0 = no limit
DEFAULT_STATS_WINDOW: Final = 900  # 15 minutes in seconds
DEFAULT_CLEANUP_INTERVAL: Final = 60  # seconds
DEFAULT_SPOT_TTL: Final = 900  # 15 minutes

# Sensor update interval
UPDATE_INTERVAL: Final = 30  # seconds

# Amateur radio band definitions (MHz)
BAND_MAPPING: Final = {
    "160m": (1.8, 2.0),
    "80m": (3.5, 4.0),
    "60m": (5.3, 5.4),
    "40m": (7.0, 7.3),
    "30m": (10.1, 10.15),
    "20m": (14.0, 14.35),
    "17m": (18.068, 18.168),
    "15m": (21.0, 21.45),
    "12m": (24.89, 24.99),
    "10m": (28.0, 29.7),
    "6m": (50.0, 54.0),
    "4m": (70.0, 70.5),
    "2m": (144.0, 148.0),
    "70cm": (420.0, 450.0),
}

# Common digital modes
DIGITAL_MODES: Final = [
    "FT8",
    "FT4",
    "JS8",
    "WSPR",
    "JT65",
    "JT9",
    "PSK31",
    "RTTY",
    "CW",
    "MFSK",
    "OLIVIA",
    "ROS",
    "SSTV",
]

# Sensor types
SENSOR_TOTAL_SPOTS: Final = "total_spots"
SENSOR_UNIQUE_STATIONS: Final = "unique_stations"
SENSOR_MOST_ACTIVE_BAND: Final = "most_active_band"
SENSOR_MOST_ACTIVE_MODE: Final = "most_active_mode"
SENSOR_MAX_DISTANCE: Final = "max_distance_km"
SENSOR_AVG_SNR: Final = "avg_snr"
SENSOR_SPOTS_PER_MINUTE: Final = "spots_per_minute"

# Attribution
ATTRIBUTION: Final = "Data provided by PSKReporter.info"
