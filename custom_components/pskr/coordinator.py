"""DataUpdateCoordinator for PSKReporter HA Bridge."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import paho.mqtt.client as mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_BAND_FILTER,
    CONF_CALLSIGN,
    CONF_CALLSIGN_ALLOW,
    CONF_CALLSIGN_BLOCK,
    CONF_COUNT_ONLY,
    CONF_COUNTRY_ALLOW,
    CONF_COUNTRY_BLOCK,
    CONF_COUNTRY_FILTER,
    CONF_DIRECTION,
    CONF_DXCC_WANTED,
    CONF_MAX_DISTANCE,
    CONF_MIN_DISTANCE,
    CONF_MODE_FILTER,
    CONF_SAMPLE_RATE,
    CONF_TRANSPORT,
    DEFAULT_COUNT_ONLY,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SPOT_TTL,
    DEFAULT_STATS_WINDOW,
    DEFAULT_TRANSPORT,
    DIRECTION_DUAL,
    DIRECTION_RX,
    DIRECTION_TX,
    DOMAIN,
    DX_THRESHOLD_KM,
    EVENT_WANTED_SPOT,
    FEED_HEALTHY_THRESHOLD_GLOBAL,
    FEED_HEALTHY_THRESHOLD_PERSONAL,
    FEED_LOW_ACTIVITY_THRESHOLD,
    GLOBAL_TOPICS,
    HF_BANDS,
    MONITOR_GLOBAL,
    MONITOR_PERSONAL,
    PSK_BROKER,
    TRANSPORT_CONFIG,
    UPDATE_INTERVAL,
)
from .dxcc_names import get_dxcc_name
from .wanted_list import parse_wanted_list

_LOGGER = logging.getLogger(__name__)

# Health monitoring constants (thresholds now in const.py)
MESSAGE_RATE_WINDOW = 60  # seconds for rate calculation
SEQUENCE_GAP_THRESHOLD = 100  # report gaps larger than this


@dataclass
class SpotData:
    """Represent a single spot."""

    sender_callsign: str
    receiver_callsign: str
    frequency: float
    mode: str
    snr: int
    timestamp: float
    sender_locator: str = ""
    receiver_locator: str = ""
    distance_km: float = 0.0
    sender_dxcc: str = ""
    receiver_dxcc: str = ""
    # New fields from MQTT payload
    band: str = ""  # Direct from payload 'b' field
    sender_azimuth: int = 0  # Bearing from sender to receiver
    receiver_azimuth: int = 0  # Bearing from receiver to sender
    sequence: int = 0  # Sequence number for gap detection


@dataclass
class BandStats:
    """Per-band statistics (v2.3.0)."""

    spots: int = 0
    unique_stations: int = 0
    avg_snr: float = 0.0
    min_snr: int = 0
    max_snr: int = 0
    avg_distance_km: float = 0.0
    max_distance_km: float = 0.0
    unique_countries: int = 0
    dominant_mode: str = "Unknown"
    countries_list: list[str] = field(default_factory=list)


@dataclass
class HealthMetrics:
    """Health monitoring metrics."""

    # Connection health
    connection_uptime: float = 0.0  # Seconds since connected
    connected_at: float = 0.0  # Timestamp of connection
    reconnect_count: int = 0  # Number of reconnections
    last_disconnect_reason: str = ""

    # Feed health (v2.2.0: improved with activity-aware thresholds)
    feed_healthy: bool = False  # Is data flowing? (binary for backwards compat)
    feed_status: str = "unknown"  # "healthy", "low_activity", "stale", "disconnected"
    feed_status_reason: str = ""  # Human-readable explanation
    last_message_time: float = 0.0  # When last message received
    feed_latency: float = 0.0  # Seconds since last message
    total_messages: int = 0  # Total messages since startup
    messages_last_minute: int = 0  # Messages in last 60 seconds
    health_threshold_seconds: int = 60  # Threshold being used (for diagnostics)

    # Data quality
    sequence_gaps: int = 0  # Number of detected sequence gaps
    total_gap_size: int = 0  # Total missed messages
    parse_errors: int = 0  # Malformed message count
    incomplete_spots: int = 0  # Messages missing required fields

    # Subscription info
    subscribed_topics: list[str] = field(default_factory=list)

    # Transport info (v2.2.0)
    transport_mode: str = ""  # Current transport mode (e.g., "WS_TLS")
    transport_port: int = 0  # Port being used


@dataclass
class PSKReporterData:
    """Data from PSKReporter."""

    spots: list[SpotData] = field(default_factory=list)
    total_spots: int = 0
    unique_stations: int = 0
    most_active_band: str = "Unknown"
    most_active_mode: str = "Unknown"
    max_distance_km: float = 0.0
    avg_snr: float = 0.0
    spots_per_minute: float = 0.0
    band_counts: dict[str, int] = field(default_factory=dict)
    mode_counts: dict[str, int] = field(default_factory=dict)
    last_spot_time: float = 0.0
    connected: bool = False
    # Health metrics
    health: HealthMetrics = field(default_factory=HealthMetrics)
    # Monitor type and global stats
    monitor_type: str = MONITOR_PERSONAL
    sample_rate: int = 1
    processed_messages: int = 0
    global_unique_stations: int = 0

    # Extended stats (v2.3.0)
    min_distance_km: float = 0.0
    avg_distance_km: float = 0.0
    min_snr: int = 0
    max_snr: int = 0
    unique_countries: int = 0
    countries_list: list[str] = field(default_factory=list)
    farthest_station: str = ""
    farthest_station_distance: float = 0.0

    # Per-band breakdown (v2.3.0)
    band_stats: dict[str, BandStats] = field(default_factory=dict)

    # Temporal metrics (v2.3.0)
    spots_last_hour: int = 0

    # Derived metrics (v2.3.0)
    dx_ratio: float = 0.0  # % spots > DX_THRESHOLD_KM
    propagation_score: int = 0  # composite metric

    # Bearing/direction (v2.5.0)
    dominant_bearing: int = 0
    dominant_direction: str = ""
    farthest_station_bearing: int = 0
    farthest_station_country: str = ""

    # Wanted list tracking (v2.4.0)
    wanted_match: bool = False
    wanted_match_count: int = 0
    wanted_list_size: int = 0


class PSKReporterCoordinator(DataUpdateCoordinator[PSKReporterData]):
    """Coordinator for PSKReporter data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.config_entry = entry
        self._callsign = entry.data.get(CONF_CALLSIGN, "").upper()
        self._direction = entry.data.get(CONF_DIRECTION, DIRECTION_RX)
        self._min_distance = entry.options.get(CONF_MIN_DISTANCE, 0)
        self._max_distance = entry.options.get(CONF_MAX_DISTANCE, 0)
        self._country_filter = entry.options.get(CONF_COUNTRY_FILTER, [])
        self._band_filter = entry.options.get(CONF_BAND_FILTER, [])
        self._mode_filter = entry.options.get(CONF_MODE_FILTER, [])
        # Callsign and country allow/block lists (v2.1.0)
        self._callsign_allow = {c.upper() for c in entry.options.get(CONF_CALLSIGN_ALLOW, [])}
        self._callsign_block = {c.upper() for c in entry.options.get(CONF_CALLSIGN_BLOCK, [])}
        self._country_allow = set(entry.options.get(CONF_COUNTRY_ALLOW, []))
        self._country_block = set(entry.options.get(CONF_COUNTRY_BLOCK, []))

        # Band filter set for O(1) lookup (v2.4.0)
        self._band_filter_set: set[str] = set(self._band_filter)

        # DXCC/Band wanted list (v2.4.0)
        wanted_raw = entry.options.get(CONF_DXCC_WANTED, "")
        self._wanted_set: set[tuple[str, str]] = parse_wanted_list(
            wanted_raw if isinstance(wanted_raw, str) else ""
        )
        self._wanted_match_times: list[float] = []

        # Monitor type and options
        self._monitor_type = entry.data.get("monitor_type", MONITOR_PERSONAL)
        if not self._callsign:
            self._monitor_type = MONITOR_GLOBAL
        self._count_only = entry.options.get(CONF_COUNT_ONLY, DEFAULT_COUNT_ONLY)
        self._sample_rate = entry.options.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE)

        # Transport configuration (v2.2.0)
        self._transport_mode = entry.options.get(CONF_TRANSPORT, DEFAULT_TRANSPORT)
        self._transport_config = TRANSPORT_CONFIG.get(self._transport_mode, TRANSPORT_CONFIG[DEFAULT_TRANSPORT])

        self._spots: list[SpotData] = []
        self._mqtt_client: mqtt.Client | None = None
        self._connected = False
        self._stats_window = DEFAULT_STATS_WINDOW
        self._spot_ttl = DEFAULT_SPOT_TTL

        # Health tracking
        self._health = HealthMetrics()
        self._message_times: deque[float] = deque(maxlen=1000)  # Track recent message times
        self._last_sequence: int | None = None  # For gap detection
        self._startup_time = time.time()
        self._message_counter = 0  # For rate limiting
        self._processed_messages = 0  # Processed after rate limiting
        self._disconnect_logged = False  # Rate-limit disconnect warnings

        # Global mode aggregation (count-only, no spot storage)
        self._global_band_counts: dict[str, int] = defaultdict(int)
        self._global_mode_counts: dict[str, int] = defaultdict(int)
        self._global_unique_stations: set[str] = set()
        self._last_window_reset = time.time()

        self.data = PSKReporterData(monitor_type=self._monitor_type)

    @property
    def callsign(self) -> str:
        """Return the monitored callsign."""
        return self._callsign

    @property
    def direction(self) -> str:
        """Return the monitoring direction."""
        return self._direction

    @property
    def monitor_type(self) -> str:
        """Return the monitor type (personal or global)."""
        return self._monitor_type

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and start MQTT connection."""
        await self._async_start_mqtt()
        await super().async_config_entry_first_refresh()

    def _setup_and_connect_mqtt(self) -> None:
        """Set up and connect MQTT client (blocking, runs in executor)."""
        client_id = f"ha_pskr_{self._callsign}" if self._callsign else "ha_pskr_global"

        # Use configured transport (v2.2.0)
        transport = self._transport_config["transport"]
        port = self._transport_config["port"]
        use_tls = self._transport_config["tls"]

        self._mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            transport=transport,
            client_id=client_id,
        )

        # Configure TLS if enabled
        if use_tls:
            self._mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

        self._mqtt_client.reconnect_delay_set(min_delay=5, max_delay=120)

        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_message = self._on_message

        # Store transport info in health metrics
        self._health.transport_mode = self._transport_mode
        self._health.transport_port = port

        _LOGGER.info(
            "Connecting to PSKReporter via %s (port %d, TLS=%s)",
            self._transport_mode, port, use_tls
        )
        self._mqtt_client.connect(PSK_BROKER, port)
        self._mqtt_client.loop_start()

    async def _async_start_mqtt(self) -> None:
        """Start MQTT connection to PSKReporter."""
        try:
            await self.hass.async_add_executor_job(self._setup_and_connect_mqtt)
            target = self._callsign if self._callsign else "global monitor"
            _LOGGER.info("Started MQTT connection to PSKReporter for %s", target)
        except Exception as err:
            _LOGGER.error("Failed to connect to PSKReporter: %s", err)
            raise UpdateFailed(f"Failed to connect to PSKReporter: {err}") from err

    def _on_connect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _flags: dict,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle MQTT connection."""
        if reason_code == 0:
            self._connected = True
            self._health.connected_at = time.time()
            if self._health.reconnect_count > 0:
                _LOGGER.info(
                    "Reconnected to PSKReporter MQTT (after %d disconnects)",
                    self._health.reconnect_count,
                )
            else:
                _LOGGER.info("Connected to PSKReporter MQTT")
            self._disconnect_logged = False
            self._subscribe_topics()
        else:
            _LOGGER.error("MQTT connection failed: %s", reason_code)

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle MQTT disconnection."""
        self._connected = False
        self._health.reconnect_count += 1
        reason_str = self._format_disconnect_reason(reason_code)
        self._health.last_disconnect_reason = reason_str
        if not self._disconnect_logged:
            _LOGGER.warning("Disconnected from PSKReporter MQTT: %s", reason_str)
            self._disconnect_logged = True
        else:
            _LOGGER.debug("Disconnected from PSKReporter MQTT: %s", reason_str)

    @staticmethod
    def _format_disconnect_reason(reason_code: mqtt.ReasonCode) -> str:
        """Map paho-mqtt reason codes to human-readable strings."""
        reason_map = {
            0: "Normal disconnect",
            1: "Unspecified error",
            4: "Disconnect with will message",
            128: "Unspecified error (server)",
            129: "Malformed packet",
            130: "Protocol error",
            131: "Implementation specific error",
            132: "Unsupported protocol version",
            133: "Client identifier not valid",
            134: "Bad username or password",
            135: "Not authorized",
            136: "Server unavailable",
            137: "Server busy",
            139: "Server shutting down",
            141: "Keep alive timeout",
            142: "Session taken over",
            143: "Topic filter invalid",
            144: "Topic name invalid",
            147: "Receive maximum exceeded",
            148: "Topic alias invalid",
            149: "Packet too large",
            151: "Quota exceeded",
            152: "Administrative action",
            153: "Payload format invalid",
            154: "Retain not supported",
            155: "QoS not supported",
            156: "Use another server",
            157: "Server moved",
            159: "Connection rate exceeded",
        }
        code_int = int(reason_code)
        name = reason_map.get(code_int)
        if name:
            return f"{name} (rc={code_int})"
        return f"Unknown (rc={code_int})"

    def _subscribe_topics(self) -> None:
        """Subscribe to PSKReporter topics based on direction.

        Topic format: pskr/filter/v2/{band}/{mode}/{sender}/{receiver}/...
        RX = spots where my callsign is receiver
        TX = spots where my callsign is sender
        Global = FT8 + FT4 across all bands (sampled)
        """
        if self._mqtt_client is None:
            return

        self._health.subscribed_topics = []

        if self._monitor_type == MONITOR_GLOBAL:
            # Global mode: subscribe to FT8 + FT4 (covers 90%+ of activity)
            for topic in GLOBAL_TOPICS:
                self._mqtt_client.subscribe(topic, qos=0)
                self._health.subscribed_topics.append(topic)
                _LOGGER.info("Subscribed to global topic: %s", topic)
            return

        # Personal mode: subscribe to callsign-specific topics
        callsign = self._callsign

        if self._direction in (DIRECTION_RX, DIRECTION_DUAL):
            # RX: any sender -> my callsign as receiver
            topic_rx = f"pskr/filter/v2/+/+/+/{callsign}/#"
            self._mqtt_client.subscribe(topic_rx, qos=0)
            self._health.subscribed_topics.append(topic_rx)
            _LOGGER.info("Subscribed to RX topic: %s", topic_rx)

        if self._direction in (DIRECTION_TX, DIRECTION_DUAL):
            # TX: my callsign as sender -> any receiver
            topic_tx = f"pskr/filter/v2/+/+/{callsign}/+/#"
            self._mqtt_client.subscribe(topic_tx, qos=0)
            self._health.subscribed_topics.append(topic_tx)
            _LOGGER.info("Subscribed to TX topic: %s", topic_tx)

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming MQTT message."""
        now = time.time()
        self._health.total_messages += 1
        self._health.last_message_time = now
        self._message_times.append(now)
        self._message_counter += 1

        # Rate limiting: skip messages based on sample rate
        if self._sample_rate > 1 and self._message_counter % self._sample_rate != 0:
            return

        self._processed_messages += 1

        try:
            payload = json.loads(msg.payload.decode("utf-8"))

            # Track sequence gaps (only meaningful for non-sampled messages)
            if self._sample_rate == 1 and "sq" in payload:
                seq = int(payload["sq"])
                if self._last_sequence is not None:
                    gap = seq - self._last_sequence - 1
                    if gap > 0 and gap < SEQUENCE_GAP_THRESHOLD:
                        self._health.sequence_gaps += 1
                        self._health.total_gap_size += gap
                        _LOGGER.debug("Sequence gap detected: %d messages missed", gap)
                self._last_sequence = seq

            # Global mode or count-only: lightweight aggregation
            if self._monitor_type == MONITOR_GLOBAL or self._count_only:
                self._process_global_spot(payload)
                asyncio.run_coroutine_threadsafe(
                    self.async_request_refresh(), self.hass.loop
                )
                return

            # Personal mode with spot storage
            spot = self._parse_spot(payload, msg.topic)
            if spot is None:
                self._health.incomplete_spots += 1
            elif self._should_include_spot(spot):
                self._spots.append(spot)
                # Check wanted list (v2.4.0)
                if self._wanted_set:
                    self._check_wanted_match(spot)
                asyncio.run_coroutine_threadsafe(
                    self.async_request_refresh(), self.hass.loop
                )
        except json.JSONDecodeError:
            self._health.parse_errors += 1
            _LOGGER.debug("Failed to parse MQTT message: %s", msg.payload)
        except Exception as err:
            self._health.parse_errors += 1
            _LOGGER.debug("Error processing spot: %s", err)

    def _process_global_spot(self, payload: dict) -> None:
        """Lightweight spot processing for global/count-only mode."""
        band = payload.get("b", "Unknown")
        mode = payload.get("md", "Unknown")
        sender = payload.get("sc", "")
        receiver = payload.get("rc", "")

        self._global_band_counts[band] += 1
        self._global_mode_counts[mode] += 1
        if sender:
            self._global_unique_stations.add(sender)
        if receiver:
            self._global_unique_stations.add(receiver)

    def _parse_spot(self, payload: dict, _topic: str) -> SpotData | None:
        """Parse spot data from MQTT payload."""
        try:
            # Extract callsigns from payload (matching Docker script)
            sender = payload.get("sc", "")
            receiver = payload.get("rc", "")

            if not sender or not receiver:
                _LOGGER.debug("Missing sender/receiver in payload: %s", payload)
                return None

            frequency = float(payload.get("f", 0)) / 1000000
            mode = payload.get("md", "UNKNOWN")
            snr = int(payload.get("rp", 0))
            sender_locator = payload.get("sl", "")
            receiver_locator = payload.get("rl", "")

            # Calculate distance and heading if both locators available
            distance_km = 0.0
            sender_azimuth = 0
            if sender_locator and receiver_locator:
                distance_km = self._calculate_distance(sender_locator, receiver_locator)
                sender_azimuth = self._calculate_heading(sender_locator, receiver_locator)

            # Get band directly from payload, fallback to calculation
            band = payload.get("b", "")
            if not band:
                band = self._get_band_from_frequency(frequency)

            return SpotData(
                sender_callsign=sender,
                receiver_callsign=receiver,
                frequency=frequency,
                mode=mode,
                snr=snr,
                timestamp=payload.get("t", time.time()),
                sender_locator=sender_locator,
                receiver_locator=receiver_locator,
                distance_km=distance_km,
                sender_dxcc=str(payload.get("sa", "")),
                receiver_dxcc=str(payload.get("ra", "")),
                band=band,
                sender_azimuth=sender_azimuth,
                sequence=int(payload.get("sq", 0)),
            )
        except (KeyError, ValueError, TypeError) as err:
            _LOGGER.debug("Failed to parse spot: %s", err)
            return None

    def _calculate_distance(self, loc1: str, loc2: str) -> float:
        """Calculate distance between two Maidenhead locators."""
        try:
            from pyhamtools.locator import calculate_distance

            # Truncate to 6 chars for calculation (matching Docker)
            loc1 = loc1[:6].upper() if len(loc1) >= 4 else ""
            loc2 = loc2[:6].upper() if len(loc2) >= 4 else ""

            if len(loc1) >= 4 and len(loc2) >= 4:
                return calculate_distance(loc1, loc2)
        except Exception as err:
            _LOGGER.debug("Distance calculation failed: %s", err)
        return 0.0

    def _calculate_heading(self, loc1: str, loc2: str) -> int:
        """Calculate heading from loc1 to loc2 in degrees."""
        try:
            from pyhamtools.locator import calculate_heading

            loc1 = loc1[:6].upper() if len(loc1) >= 4 else ""
            loc2 = loc2[:6].upper() if len(loc2) >= 4 else ""

            if len(loc1) >= 4 and len(loc2) >= 4:
                return int(calculate_heading(loc1, loc2))
        except Exception as err:
            _LOGGER.debug("Heading calculation failed: %s", err)
        return 0

    @staticmethod
    def _bearing_to_compass(bearing: int) -> str:
        """Convert bearing degrees to 8-point compass direction."""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(bearing / 45) % 8
        return directions[index]

    def _should_include_spot(self, spot: SpotData) -> bool:
        """Check if spot passes configured filters."""
        # Distance filtering
        if self._min_distance > 0 and spot.distance_km < self._min_distance:
            return False
        if self._max_distance > 0 and spot.distance_km > self._max_distance:
            return False
        # Mode filtering
        if self._mode_filter and spot.mode not in self._mode_filter:
            return False
        # Band filtering (v2.4.0)
        if self._band_filter_set and spot.band.lower() not in self._band_filter_set:
            return False
        # Callsign block list (exclude if either station is blocked)
        if self._callsign_block:
            sender_upper = spot.sender_callsign.upper()
            receiver_upper = spot.receiver_callsign.upper()
            if sender_upper in self._callsign_block or receiver_upper in self._callsign_block:
                return False
        # Callsign allow list (only include if at least one station is allowed)
        if self._callsign_allow:
            sender_upper = spot.sender_callsign.upper()
            receiver_upper = spot.receiver_callsign.upper()
            if sender_upper not in self._callsign_allow and receiver_upper not in self._callsign_allow:
                return False
        # Country block list (exclude if either station's country is blocked)
        if self._country_block and (
            spot.sender_dxcc in self._country_block or spot.receiver_dxcc in self._country_block
        ):
            return False
        # Country allow list (only include if at least one station's country is allowed)
        if self._country_allow:
            return spot.sender_dxcc in self._country_allow or spot.receiver_dxcc in self._country_allow
        return True

    def _check_wanted_match(self, spot: SpotData) -> None:
        """Check if spot matches any DXCC/band wanted combination (v2.4.0)."""
        matched_dxcc: str | None = None

        # Direction-aware matching
        band_lower = spot.band.lower()
        if self._direction in (DIRECTION_RX, DIRECTION_DUAL) and (spot.sender_dxcc, band_lower) in self._wanted_set:
            matched_dxcc = spot.sender_dxcc
        if matched_dxcc is None and self._direction in (DIRECTION_TX, DIRECTION_DUAL) and (spot.receiver_dxcc, band_lower) in self._wanted_set:
            matched_dxcc = spot.receiver_dxcc

        if matched_dxcc is not None:
            self._wanted_match_times.append(time.time())

            # Fire HA event
            event_data = {
                "sender_callsign": spot.sender_callsign,
                "receiver_callsign": spot.receiver_callsign,
                "frequency": spot.frequency,
                "band": spot.band,
                "mode": spot.mode,
                "snr": spot.snr,
                "distance_km": spot.distance_km,
                "sender_dxcc": spot.sender_dxcc,
                "receiver_dxcc": spot.receiver_dxcc,
                "matched_dxcc": matched_dxcc,
                "matched_country_name": get_dxcc_name(matched_dxcc),
                "matched_band": spot.band,
            }
            self.hass.loop.call_soon_threadsafe(
                self.hass.bus.async_fire, EVENT_WANTED_SPOT, event_data
            )

    def _get_band_from_frequency(self, freq_mhz: float) -> str:
        """Determine band from frequency."""
        band_ranges = {
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
        for band, (low, high) in band_ranges.items():
            if low <= freq_mhz <= high:
                return band
        return "Unknown"

    def _cleanup_old_spots(self) -> None:
        """Remove spots older than TTL."""
        cutoff = time.time() - self._spot_ttl
        self._spots = [s for s in self._spots if s.timestamp > cutoff]

    def _calculate_health_metrics(self) -> HealthMetrics:
        """Calculate current health metrics.

        v2.2.0: Uses monitor-type-specific thresholds:
        - Personal monitors: 300s threshold (sparse activity is normal)
        - Global monitors: 60s threshold (high volume expected)
        """
        now = time.time()

        # Connection uptime
        if self._connected and self._health.connected_at > 0:
            self._health.connection_uptime = now - self._health.connected_at
        else:
            self._health.connection_uptime = 0.0

        # Feed latency (time since last message)
        if self._health.last_message_time > 0:
            self._health.feed_latency = now - self._health.last_message_time
        else:
            self._health.feed_latency = now - self._startup_time  # Never received a message

        # Messages in last minute
        cutoff = now - MESSAGE_RATE_WINDOW
        self._health.messages_last_minute = sum(1 for t in self._message_times if t > cutoff)

        # Select threshold based on monitor type (v2.2.0)
        if self._monitor_type == MONITOR_GLOBAL:
            healthy_threshold = FEED_HEALTHY_THRESHOLD_GLOBAL
        else:
            healthy_threshold = FEED_HEALTHY_THRESHOLD_PERSONAL

        self._health.health_threshold_seconds = healthy_threshold

        # Feed health determination with activity-aware states (v2.2.0)
        if not self._connected:
            self._health.feed_status = "disconnected"
            self._health.feed_status_reason = "Not connected to PSKReporter MQTT"
            self._health.feed_healthy = False
        elif self._health.last_message_time == 0:
            self._health.feed_status = "waiting"
            self._health.feed_status_reason = "Waiting for first message"
            self._health.feed_healthy = False
        elif self._health.feed_latency < FEED_LOW_ACTIVITY_THRESHOLD:
            # Within low activity threshold = healthy
            self._health.feed_status = "healthy"
            self._health.feed_status_reason = "Receiving data normally"
            self._health.feed_healthy = True
        elif self._health.feed_latency < healthy_threshold:
            # Between low activity and healthy threshold = low activity
            self._health.feed_status = "low_activity"
            latency_int = int(self._health.feed_latency)
            if self._monitor_type == MONITOR_GLOBAL:
                self._health.feed_status_reason = f"Low activity ({latency_int}s since last message)"
            else:
                self._health.feed_status_reason = (
                    f"Low activity ({latency_int}s) - normal during poor propagation"
                )
            self._health.feed_healthy = True  # Still considered healthy
        else:
            # Beyond healthy threshold = stale
            self._health.feed_status = "stale"
            latency_int = int(self._health.feed_latency)
            if self._monitor_type == MONITOR_GLOBAL:
                self._health.feed_status_reason = (
                    f"No messages for {latency_int}s (PSKReporter feed may be down)"
                )
            else:
                self._health.feed_status_reason = (
                    f"No messages for {latency_int}s - station may be offline or band closed"
                )
            self._health.feed_healthy = False

        return self._health

    def _reset_global_stats_if_needed(self) -> None:
        """Reset global stats if window has expired."""
        now = time.time()
        if now - self._last_window_reset > self._stats_window:
            self._global_band_counts.clear()
            self._global_mode_counts.clear()
            self._global_unique_stations.clear()
            self._last_window_reset = now

    def _calculate_statistics(self) -> PSKReporterData:
        """Calculate statistics from current spots."""
        health = self._calculate_health_metrics()

        # Global mode or count-only: use aggregated counters
        if self._monitor_type == MONITOR_GLOBAL or self._count_only:
            self._reset_global_stats_if_needed()

            most_active_band = (
                max(self._global_band_counts, key=self._global_band_counts.get)
                if self._global_band_counts else "Unknown"
            )
            most_active_mode = (
                max(self._global_mode_counts, key=self._global_mode_counts.get)
                if self._global_mode_counts else "Unknown"
            )
            total_spots = sum(self._global_band_counts.values())

            return PSKReporterData(
                total_spots=total_spots,
                unique_stations=len(self._global_unique_stations),
                most_active_band=most_active_band,
                most_active_mode=most_active_mode,
                band_counts=dict(self._global_band_counts),
                mode_counts=dict(self._global_mode_counts),
                connected=self._connected,
                health=health,
                monitor_type=self._monitor_type,
                sample_rate=self._sample_rate,
                processed_messages=self._processed_messages,
                global_unique_stations=len(self._global_unique_stations),
                wanted_list_size=len(self._wanted_set),
            )

        # Personal mode with spot storage
        self._cleanup_old_spots()

        if not self._spots:
            return PSKReporterData(
                connected=self._connected,
                health=health,
                monitor_type=self._monitor_type,
                wanted_list_size=len(self._wanted_set),
            )

        stats_cutoff = time.time() - self._stats_window
        recent_spots = [s for s in self._spots if s.timestamp > stats_cutoff]

        if not recent_spots:
            return PSKReporterData(
                spots=self._spots,
                total_spots=len(self._spots),
                connected=self._connected,
                health=health,
                monitor_type=self._monitor_type,
                wanted_list_size=len(self._wanted_set),
            )

        unique_stations: set[str] = set()
        band_counts: dict[str, int] = defaultdict(int)
        mode_counts: dict[str, int] = defaultdict(int)
        countries: set[str] = set()
        total_snr = 0
        max_distance = 0.0
        farthest_spot: SpotData | None = None

        # Per-band data collection (v2.3.0)
        band_spots: dict[str, list[SpotData]] = defaultdict(list)

        for spot in recent_spots:
            if self._direction == DIRECTION_TX:
                unique_stations.add(spot.receiver_callsign)
                # Track receiver country for TX mode
                if spot.receiver_dxcc:
                    countries.add(spot.receiver_dxcc)
            else:
                unique_stations.add(spot.sender_callsign)
                # Track sender country for RX mode
                if spot.sender_dxcc:
                    countries.add(spot.sender_dxcc)

            # Use band from spot (now populated from payload or calculated)
            band = spot.band if spot.band else self._get_band_from_frequency(spot.frequency)
            band_counts[band] += 1
            mode_counts[spot.mode] += 1
            total_snr += spot.snr

            # Track farthest spot
            if spot.distance_km > max_distance:
                max_distance = spot.distance_km
                farthest_spot = spot

            # Collect spots by band for per-band stats
            band_spots[band].append(spot)

        most_active_band = max(band_counts, key=band_counts.get) if band_counts else "Unknown"
        most_active_mode = max(mode_counts, key=mode_counts.get) if mode_counts else "Unknown"
        avg_snr = total_snr / len(recent_spots) if recent_spots else 0
        time_range_minutes = self._stats_window / 60
        spots_per_minute = len(recent_spots) / time_range_minutes if time_range_minutes > 0 else 0

        # Extended distance stats (v2.3.0)
        distances = [s.distance_km for s in recent_spots if s.distance_km > 0]
        min_distance = min(distances) if distances else 0.0
        avg_distance = sum(distances) / len(distances) if distances else 0.0

        # SNR range (v2.3.0)
        snrs = [s.snr for s in recent_spots]
        min_snr = min(snrs) if snrs else 0
        max_snr = max(snrs) if snrs else 0

        # Farthest station details (v2.3.0)
        farthest_station = ""
        farthest_station_distance = 0.0
        farthest_station_bearing = 0
        farthest_station_country = ""
        if farthest_spot:
            if self._direction == DIRECTION_TX:
                farthest_station = farthest_spot.receiver_callsign
                dxcc_code = farthest_spot.receiver_dxcc
            else:
                farthest_station = farthest_spot.sender_callsign
                dxcc_code = farthest_spot.sender_dxcc
            farthest_station_country = get_dxcc_name(dxcc_code) if dxcc_code else ""
            farthest_station_distance = farthest_spot.distance_km
            farthest_station_bearing = farthest_spot.sender_azimuth

        # Dominant bearing (v2.5.0) — bearing with most spots
        bearing_buckets: dict[int, int] = defaultdict(int)
        for spot in recent_spots:
            if spot.sender_azimuth > 0:
                # Bucket to nearest 45 degrees for 8-point compass
                bucket = round(spot.sender_azimuth / 45) * 45 % 360
                bearing_buckets[bucket] += 1
        dominant_bearing = 0
        dominant_direction = ""
        if bearing_buckets:
            dominant_bearing = max(bearing_buckets, key=bearing_buckets.get)
            dominant_direction = self._bearing_to_compass(dominant_bearing)

        # Country list with names (v2.3.0, enriched v2.5.0)
        countries_list = sorted(
            f"{c} ({get_dxcc_name(c)})" for c in countries
        )
        unique_countries = len(countries)

        # DX ratio - percentage of spots > DX_THRESHOLD_KM (v2.3.0)
        dx_spots = sum(1 for s in recent_spots if s.distance_km > DX_THRESHOLD_KM)
        dx_ratio = (dx_spots / len(recent_spots) * 100) if recent_spots else 0.0

        # Spots in last hour (v2.3.0)
        hour_cutoff = time.time() - 3600
        spots_last_hour = sum(1 for s in self._spots if s.timestamp > hour_cutoff)

        # Propagation score - composite metric (v2.3.0)
        # Formula: spots × unique_countries × (max_distance / 1000)
        propagation_score = int(
            len(recent_spots) * unique_countries * (max_distance / 1000)
        ) if max_distance > 0 else 0

        # Per-band statistics (v2.3.0)
        band_stats: dict[str, BandStats] = {}
        for band in HF_BANDS:
            spots_in_band = band_spots.get(band, [])
            if not spots_in_band:
                band_stats[band] = BandStats()
                continue

            # Calculate per-band metrics
            band_snrs = [s.snr for s in spots_in_band]
            band_distances = [s.distance_km for s in spots_in_band if s.distance_km > 0]
            band_stations: set[str] = set()
            band_countries: set[str] = set()
            band_mode_counts: dict[str, int] = defaultdict(int)

            for spot in spots_in_band:
                if self._direction == DIRECTION_TX:
                    band_stations.add(spot.receiver_callsign)
                    if spot.receiver_dxcc:
                        band_countries.add(spot.receiver_dxcc)
                else:
                    band_stations.add(spot.sender_callsign)
                    if spot.sender_dxcc:
                        band_countries.add(spot.sender_dxcc)
                band_mode_counts[spot.mode] += 1

            band_dominant_mode = (
                max(band_mode_counts, key=band_mode_counts.get)
                if band_mode_counts else "Unknown"
            )

            band_stats[band] = BandStats(
                spots=len(spots_in_band),
                unique_stations=len(band_stations),
                avg_snr=round(sum(band_snrs) / len(band_snrs), 1) if band_snrs else 0.0,
                min_snr=min(band_snrs) if band_snrs else 0,
                max_snr=max(band_snrs) if band_snrs else 0,
                avg_distance_km=round(sum(band_distances) / len(band_distances), 1) if band_distances else 0.0,
                max_distance_km=max(band_distances) if band_distances else 0.0,
                unique_countries=len(band_countries),
                dominant_mode=band_dominant_mode,
                countries_list=sorted(
                    f"{c} ({get_dxcc_name(c)})" for c in band_countries
                ),
            )

        # Wanted list window tracking (v2.4.0)
        wanted_cutoff = time.time() - self._stats_window
        wanted_in_window = sum(1 for t in self._wanted_match_times if t > wanted_cutoff)
        self._wanted_match_times = [t for t in self._wanted_match_times if t > wanted_cutoff]

        return PSKReporterData(
            spots=self._spots,
            total_spots=len(recent_spots),
            unique_stations=len(unique_stations),
            most_active_band=most_active_band,
            most_active_mode=most_active_mode,
            max_distance_km=max_distance,
            avg_snr=round(avg_snr, 1),
            spots_per_minute=round(spots_per_minute, 2),
            band_counts=dict(band_counts),
            mode_counts=dict(mode_counts),
            last_spot_time=max(s.timestamp for s in recent_spots),
            connected=self._connected,
            health=health,
            monitor_type=self._monitor_type,
            # Extended stats (v2.3.0)
            min_distance_km=round(min_distance, 1),
            avg_distance_km=round(avg_distance, 1),
            min_snr=min_snr,
            max_snr=max_snr,
            unique_countries=unique_countries,
            countries_list=countries_list,
            farthest_station=farthest_station,
            farthest_station_distance=round(farthest_station_distance, 1),
            # Bearing/direction (v2.5.0)
            dominant_bearing=dominant_bearing,
            dominant_direction=dominant_direction,
            farthest_station_bearing=farthest_station_bearing,
            farthest_station_country=farthest_station_country,
            band_stats=band_stats,
            spots_last_hour=spots_last_hour,
            dx_ratio=round(dx_ratio, 1),
            propagation_score=propagation_score,
            # Wanted list (v2.4.0)
            wanted_match=wanted_in_window > 0,
            wanted_match_count=wanted_in_window,
            wanted_list_size=len(self._wanted_set),
        )

    async def _async_update_data(self) -> PSKReporterData:
        """Fetch data from coordinator."""
        return await self.hass.async_add_executor_job(self._calculate_statistics)

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
            _LOGGER.info("Disconnected from PSKReporter MQTT")
