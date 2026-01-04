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
    CONF_COUNT_ONLY,
    CONF_COUNTRY_FILTER,
    CONF_DIRECTION,
    CONF_MAX_DISTANCE,
    CONF_MIN_DISTANCE,
    CONF_MODE_FILTER,
    CONF_SAMPLE_RATE,
    DEFAULT_COUNT_ONLY,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SPOT_TTL,
    DEFAULT_STATS_WINDOW,
    DIRECTION_DUAL,
    DIRECTION_RX,
    DIRECTION_TX,
    DOMAIN,
    GLOBAL_TOPICS,
    MONITOR_GLOBAL,
    MONITOR_PERSONAL,
    PSK_BROKER,
    PSK_PORT_WS_TLS,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Health monitoring constants
FEED_HEALTHY_THRESHOLD = 60  # seconds without messages = unhealthy
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
class HealthMetrics:
    """Health monitoring metrics."""

    # Connection health
    connection_uptime: float = 0.0  # Seconds since connected
    connected_at: float = 0.0  # Timestamp of connection
    reconnect_count: int = 0  # Number of reconnections
    last_disconnect_reason: str = ""

    # Feed health
    feed_healthy: bool = False  # Is data flowing?
    last_message_time: float = 0.0  # When last message received
    feed_latency: float = 0.0  # Seconds since last message
    total_messages: int = 0  # Total messages since startup
    messages_last_minute: int = 0  # Messages in last 60 seconds

    # Data quality
    sequence_gaps: int = 0  # Number of detected sequence gaps
    total_gap_size: int = 0  # Total missed messages
    parse_errors: int = 0  # Malformed message count
    incomplete_spots: int = 0  # Messages missing required fields

    # Subscription info
    subscribed_topics: list[str] = field(default_factory=list)


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

        # Monitor type and options
        self._monitor_type = entry.data.get("monitor_type", MONITOR_PERSONAL)
        if not self._callsign:
            self._monitor_type = MONITOR_GLOBAL
        self._count_only = entry.options.get(CONF_COUNT_ONLY, DEFAULT_COUNT_ONLY)
        self._sample_rate = entry.options.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE)

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
        self._mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            transport="websockets",
            client_id=client_id,
        )
        self._mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        self._mqtt_client.reconnect_delay_set(min_delay=5, max_delay=120)

        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_message = self._on_message

        self._mqtt_client.connect(PSK_BROKER, PSK_PORT_WS_TLS)
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
            _LOGGER.info("Connected to PSKReporter MQTT")
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
        self._health.last_disconnect_reason = str(reason_code)
        _LOGGER.warning("Disconnected from PSKReporter MQTT: %s", reason_code)

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

            # Calculate distance if both locators available
            distance_km = 0.0
            if sender_locator and receiver_locator:
                distance_km = self._calculate_distance(sender_locator, receiver_locator)

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
                # New fields
                band=band,
                sender_azimuth=int(payload.get("sa", 0)) if isinstance(payload.get("sa"), (int, float)) else 0,
                receiver_azimuth=int(payload.get("ra", 0)) if isinstance(payload.get("ra"), (int, float)) else 0,
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

    def _should_include_spot(self, spot: SpotData) -> bool:
        """Check if spot passes configured filters."""
        if self._min_distance > 0 and spot.distance_km < self._min_distance:
            return False
        if self._max_distance > 0 and spot.distance_km > self._max_distance:
            return False
        return not (self._mode_filter and spot.mode not in self._mode_filter)

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
        """Calculate current health metrics."""
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

        # Feed health determination
        # Feed is healthy if:
        # 1. We're connected AND
        # 2. We've received a message in the last FEED_HEALTHY_THRESHOLD seconds
        self._health.feed_healthy = (
            self._connected and
            self._health.last_message_time > 0 and
            self._health.feed_latency < FEED_HEALTHY_THRESHOLD
        )

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
            )

        # Personal mode with spot storage
        self._cleanup_old_spots()

        if not self._spots:
            return PSKReporterData(
                connected=self._connected,
                health=health,
                monitor_type=self._monitor_type,
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
            )

        unique_stations: set[str] = set()
        band_counts: dict[str, int] = defaultdict(int)
        mode_counts: dict[str, int] = defaultdict(int)
        total_snr = 0
        max_distance = 0.0

        for spot in recent_spots:
            if self._direction == DIRECTION_TX:
                unique_stations.add(spot.receiver_callsign)
            else:
                unique_stations.add(spot.sender_callsign)

            # Use band from spot (now populated from payload or calculated)
            band = spot.band if spot.band else self._get_band_from_frequency(spot.frequency)
            band_counts[band] += 1
            mode_counts[spot.mode] += 1
            total_snr += spot.snr
            if spot.distance_km > max_distance:
                max_distance = spot.distance_km

        most_active_band = max(band_counts, key=band_counts.get) if band_counts else "Unknown"
        most_active_mode = max(mode_counts, key=mode_counts.get) if mode_counts else "Unknown"
        avg_snr = total_snr / len(recent_spots) if recent_spots else 0
        time_range_minutes = self._stats_window / 60
        spots_per_minute = len(recent_spots) / time_range_minutes if time_range_minutes > 0 else 0

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
