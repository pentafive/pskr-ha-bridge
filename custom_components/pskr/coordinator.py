"""DataUpdateCoordinator for PSKReporter Monitor."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from collections import defaultdict
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
    CONF_COUNTRY_FILTER,
    CONF_DIRECTION,
    CONF_MAX_DISTANCE,
    CONF_MIN_DISTANCE,
    CONF_MODE_FILTER,
    DEFAULT_SPOT_TTL,
    DEFAULT_STATS_WINDOW,
    DIRECTION_DUAL,
    DIRECTION_RX,
    DIRECTION_TX,
    DOMAIN,
    PSK_BROKER,
    PSK_PORT_WS_TLS,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


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
        self._callsign = entry.data[CONF_CALLSIGN].upper()
        self._direction = entry.data.get(CONF_DIRECTION, DIRECTION_RX)
        self._min_distance = entry.options.get(CONF_MIN_DISTANCE, 0)
        self._max_distance = entry.options.get(CONF_MAX_DISTANCE, 0)
        self._country_filter = entry.options.get(CONF_COUNTRY_FILTER, [])
        self._band_filter = entry.options.get(CONF_BAND_FILTER, [])
        self._mode_filter = entry.options.get(CONF_MODE_FILTER, [])

        self._spots: list[SpotData] = []
        self._mqtt_client: mqtt.Client | None = None
        self._connected = False
        self._stats_window = DEFAULT_STATS_WINDOW
        self._spot_ttl = DEFAULT_SPOT_TTL

        self.data = PSKReporterData()

    @property
    def callsign(self) -> str:
        """Return the monitored callsign."""
        return self._callsign

    @property
    def direction(self) -> str:
        """Return the monitoring direction."""
        return self._direction

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and start MQTT connection."""
        await self._async_start_mqtt()
        await super().async_config_entry_first_refresh()

    async def _async_start_mqtt(self) -> None:
        """Start MQTT connection to PSKReporter."""
        try:
            self._mqtt_client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                transport="websockets",
            )
            self._mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
            self._mqtt_client.ws_set_options(path="/")

            self._mqtt_client.on_connect = self._on_connect
            self._mqtt_client.on_disconnect = self._on_disconnect
            self._mqtt_client.on_message = self._on_message

            await self.hass.async_add_executor_job(
                self._mqtt_client.connect, PSK_BROKER, PSK_PORT_WS_TLS
            )
            self._mqtt_client.loop_start()
            _LOGGER.info("Started MQTT connection to PSKReporter for %s", self._callsign)
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
        _LOGGER.warning("Disconnected from PSKReporter MQTT: %s", reason_code)

    def _subscribe_topics(self) -> None:
        """Subscribe to PSKReporter topics based on direction."""
        if self._mqtt_client is None:
            return

        callsign = self._callsign.replace("/", "_")

        if self._direction in (DIRECTION_RX, DIRECTION_DUAL):
            topic_rx = f"pskr/filter/v2/+/+/+/+/+/{callsign}/+"
            self._mqtt_client.subscribe(topic_rx, qos=0)
            _LOGGER.debug("Subscribed to RX topic: %s", topic_rx)

        if self._direction in (DIRECTION_TX, DIRECTION_DUAL):
            topic_tx = f"pskr/filter/v2/{callsign}/+/+/+/+/+/+"
            self._mqtt_client.subscribe(topic_tx, qos=0)
            _LOGGER.debug("Subscribed to TX topic: %s", topic_tx)

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming MQTT message."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            spot = self._parse_spot(payload, msg.topic)
            if spot and self._should_include_spot(spot):
                self._spots.append(spot)
                asyncio.run_coroutine_threadsafe(
                    self.async_request_refresh(), self.hass.loop
                )
        except json.JSONDecodeError:
            _LOGGER.debug("Failed to parse MQTT message: %s", msg.payload)
        except Exception as err:
            _LOGGER.debug("Error processing spot: %s", err)

    def _parse_spot(self, payload: dict, topic: str) -> SpotData | None:
        """Parse spot data from MQTT payload."""
        try:
            parts = topic.split("/")
            if len(parts) < 10:
                return None

            sender = parts[3]
            receiver = parts[8]
            frequency = float(payload.get("f", 0)) / 1000000
            mode = payload.get("md", "UNKNOWN")
            snr = int(payload.get("rp", 0))

            return SpotData(
                sender_callsign=sender,
                receiver_callsign=receiver,
                frequency=frequency,
                mode=mode,
                snr=snr,
                timestamp=time.time(),
                sender_locator=payload.get("sl", ""),
                receiver_locator=payload.get("rl", ""),
                sender_dxcc=str(payload.get("sa", "")),
                receiver_dxcc=str(payload.get("ra", "")),
            )
        except (KeyError, ValueError, IndexError) as err:
            _LOGGER.debug("Failed to parse spot: %s", err)
            return None

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

    def _calculate_statistics(self) -> PSKReporterData:
        """Calculate statistics from current spots."""
        self._cleanup_old_spots()

        if not self._spots:
            return PSKReporterData(connected=self._connected)

        stats_cutoff = time.time() - self._stats_window
        recent_spots = [s for s in self._spots if s.timestamp > stats_cutoff]

        if not recent_spots:
            return PSKReporterData(
                spots=self._spots,
                total_spots=len(self._spots),
                connected=self._connected,
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

            band = self._get_band_from_frequency(spot.frequency)
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
