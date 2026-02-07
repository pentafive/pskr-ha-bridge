"""Constants for the PSKReporter Monitor integration."""

from typing import Final

DOMAIN: Final = "pskr"

# Configuration keys
CONF_CALLSIGN: Final = "callsign"
CONF_DIRECTION: Final = "direction"
CONF_TRANSPORT: Final = "transport"
CONF_MIN_DISTANCE: Final = "min_distance"
CONF_MAX_DISTANCE: Final = "max_distance"
CONF_COUNTRY_FILTER: Final = "country_filter"
CONF_BAND_FILTER: Final = "band_filter"
CONF_MODE_FILTER: Final = "mode_filter"
CONF_COUNT_ONLY: Final = "count_only"
CONF_SAMPLE_RATE: Final = "sample_rate"
CONF_CALLSIGN_ALLOW: Final = "callsign_allow"
CONF_CALLSIGN_BLOCK: Final = "callsign_block"
CONF_COUNTRY_ALLOW: Final = "country_allow"
CONF_COUNTRY_BLOCK: Final = "country_block"
CONF_DXCC_WANTED: Final = "dxcc_wanted"

# Monitor types
MONITOR_PERSONAL: Final = "personal"
MONITOR_GLOBAL: Final = "global"

# Direction options
DIRECTION_RX: Final = "rx"
DIRECTION_TX: Final = "tx"
DIRECTION_DUAL: Final = "dual"

DIRECTION_OPTIONS: Final = [DIRECTION_RX, DIRECTION_TX, DIRECTION_DUAL]

# Global subscription topics (FT8 + FT4 for efficiency)
GLOBAL_TOPICS: Final = [
    "pskr/filter/v2/+/FT8/+/+/#",
    "pskr/filter/v2/+/FT4/+/+/#",
]

# HF bands for global per-band sensors
HF_BANDS: Final = ["160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m"]

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

# Transport mode options for config flow
TRANSPORT_OPTIONS: Final = [TRANSPORT_WS_TLS, TRANSPORT_MQTT_TLS, TRANSPORT_WS, TRANSPORT_MQTT]

# Transport to port/protocol mapping
TRANSPORT_CONFIG: Final = {
    TRANSPORT_MQTT: {"port": PSK_PORT_MQTT, "transport": "tcp", "tls": False},
    TRANSPORT_MQTT_TLS: {"port": PSK_PORT_MQTT_TLS, "transport": "tcp", "tls": True},
    TRANSPORT_WS: {"port": PSK_PORT_WS, "transport": "websockets", "tls": False},
    TRANSPORT_WS_TLS: {"port": PSK_PORT_WS_TLS, "transport": "websockets", "tls": True},
}

# Default settings
DEFAULT_DIRECTION: Final = DIRECTION_RX
DEFAULT_TRANSPORT: Final = TRANSPORT_WS_TLS  # WebSocket+TLS most firewall-friendly
DEFAULT_MIN_DISTANCE: Final = 0
DEFAULT_MAX_DISTANCE: Final = 0  # 0 = no limit
DEFAULT_STATS_WINDOW: Final = 900  # 15 minutes in seconds
DEFAULT_CLEANUP_INTERVAL: Final = 60  # seconds
DEFAULT_SPOT_TTL: Final = 900  # 15 minutes
DEFAULT_COUNT_ONLY: Final = False
DEFAULT_SAMPLE_RATE: Final = 10  # Process 1 in N messages for global mode

# Sensor update interval
UPDATE_INTERVAL: Final = 30  # seconds

# Feed health thresholds (v2.2.0)
# Personal monitors have sparse, intermittent activity (1-10+ min gaps normal)
# Global monitors have high volume (~1000 msg/min) so shorter threshold works
FEED_HEALTHY_THRESHOLD_PERSONAL: Final = 300  # 5 minutes for personal callsign monitors
FEED_HEALTHY_THRESHOLD_GLOBAL: Final = 60  # 1 minute for global (high volume)
FEED_LOW_ACTIVITY_THRESHOLD: Final = 180  # 3 minutes = low activity warning

# DX threshold for ratio calculation (v2.3.0)
DX_THRESHOLD_KM: Final = 5000  # Spots beyond this are considered DX

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

# Event types (v2.4.0)
EVENT_WANTED_SPOT: Final = "pskr_wanted_spot"

# Activity heatmap (v2.6.0)
SENSOR_ACTIVITY_HEATMAP: Final = "activity_heatmap"
HEATMAP_WINDOW_HOURS: Final = 24

# Attribution
ATTRIBUTION: Final = "Data provided by PSKReporter.info"
