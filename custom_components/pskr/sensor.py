"""Sensor platform for PSKReporter HA Bridge."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, HF_BANDS, MONITOR_GLOBAL
from .coordinator import BandStats, PSKReporterCoordinator, PSKReporterData


@dataclass(frozen=True, kw_only=True)
class PSKReporterSensorEntityDescription(SensorEntityDescription):
    """Describes PSKReporter sensor entity."""

    value_fn: Callable[[PSKReporterData], Any]
    attr_fn: Callable[[PSKReporterData], dict[str, Any]] | None = None


# Main activity sensors
SENSOR_DESCRIPTIONS: tuple[PSKReporterSensorEntityDescription, ...] = (
    PSKReporterSensorEntityDescription(
        key="total_spots",
        translation_key="total_spots",
        native_unit_of_measurement="spots",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.total_spots,
    ),
    PSKReporterSensorEntityDescription(
        key="unique_stations",
        translation_key="unique_stations",
        native_unit_of_measurement="stations",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.unique_stations,
    ),
    PSKReporterSensorEntityDescription(
        key="most_active_band",
        translation_key="most_active_band",
        value_fn=lambda data: data.most_active_band,
        attr_fn=lambda data: {"band_counts": data.band_counts},
    ),
    PSKReporterSensorEntityDescription(
        key="most_active_mode",
        translation_key="most_active_mode",
        value_fn=lambda data: data.most_active_mode,
        attr_fn=lambda data: {"mode_counts": data.mode_counts},
    ),
    PSKReporterSensorEntityDescription(
        key="max_distance",
        translation_key="max_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.max_distance_km, 1) if data.max_distance_km > 0 else None,
    ),
    PSKReporterSensorEntityDescription(
        key="avg_snr",
        translation_key="avg_snr",
        native_unit_of_measurement="dB",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.avg_snr if data.total_spots > 0 else None,
    ),
    PSKReporterSensorEntityDescription(
        key="spots_per_minute",
        translation_key="spots_per_minute",
        native_unit_of_measurement="spots/min",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.spots_per_minute,
    ),
    PSKReporterSensorEntityDescription(
        key="last_spot",
        translation_key="last_spot",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            datetime.fromtimestamp(data.last_spot_time, tz=UTC)
            if data.last_spot_time > 0
            else None
        ),
    ),
    PSKReporterSensorEntityDescription(
        key="connection_status",
        translation_key="connection_status",
        value_fn=lambda data: "Connected" if data.connected else "Disconnected",
        attr_fn=lambda data: {
            "transport_mode": data.health.transport_mode,
            "transport_port": data.health.transport_port,
            "reconnect_count": data.health.reconnect_count,
            "last_disconnect_reason": data.health.last_disconnect_reason,
            "subscribed_topics": data.health.subscribed_topics,
        },
    ),
)

# Health monitoring sensors (diagnostic category)
HEALTH_SENSOR_DESCRIPTIONS: tuple[PSKReporterSensorEntityDescription, ...] = (
    PSKReporterSensorEntityDescription(
        key="feed_status",
        translation_key="feed_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        # v2.2.0: Use feed_status for more granular states (healthy, low_activity, stale, etc.)
        value_fn=lambda data: data.health.feed_status.replace("_", " ").title(),
        attr_fn=lambda data: {
            "last_message_time": (
                datetime.fromtimestamp(data.health.last_message_time).isoformat()
                if data.health.last_message_time > 0
                else None
            ),
            "feed_latency_seconds": round(data.health.feed_latency, 1),
            "threshold_seconds": data.health.health_threshold_seconds,
            "reason": data.health.feed_status_reason,
            "feed_healthy": data.health.feed_healthy,  # Binary for automations
        },
    ),
    PSKReporterSensorEntityDescription(
        key="message_rate",
        translation_key="message_rate",
        native_unit_of_measurement="msg/min",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.health.messages_last_minute,
        attr_fn=lambda data: {
            "total_messages": data.health.total_messages,
        },
    ),
    PSKReporterSensorEntityDescription(
        key="feed_latency",
        translation_key="feed_latency",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: round(data.health.feed_latency, 1) if data.health.last_message_time > 0 else None,
    ),
    PSKReporterSensorEntityDescription(
        key="connection_uptime",
        translation_key="connection_uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: round(data.health.connection_uptime, 0) if data.connected else 0,
        attr_fn=lambda data: {
            "connected_at": (
                datetime.fromtimestamp(data.health.connected_at).isoformat()
                if data.health.connected_at > 0
                else None
            ),
        },
    ),
    PSKReporterSensorEntityDescription(
        key="reconnect_count",
        translation_key="reconnect_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.health.reconnect_count,
        attr_fn=lambda data: {
            "last_disconnect_reason": data.health.last_disconnect_reason or "N/A",
        },
    ),
    PSKReporterSensorEntityDescription(
        key="sequence_gaps",
        translation_key="sequence_gaps",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.health.sequence_gaps,
        attr_fn=lambda data: {
            "total_gap_size": data.health.total_gap_size,
            "description": "Number of detected message sequence gaps (missed messages)",
        },
    ),
    PSKReporterSensorEntityDescription(
        key="parse_errors",
        translation_key="parse_errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.health.parse_errors,
        attr_fn=lambda data: {
            "incomplete_spots": data.health.incomplete_spots,
            "description": "Messages that failed to parse",
        },
    ),
)

# Extended sensors for personal mode (v2.3.0)
EXTENDED_SENSOR_DESCRIPTIONS: tuple[PSKReporterSensorEntityDescription, ...] = (
    # Distance stats
    PSKReporterSensorEntityDescription(
        key="min_distance",
        translation_key="min_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.min_distance_km if data.min_distance_km > 0 else None,
    ),
    PSKReporterSensorEntityDescription(
        key="avg_distance",
        translation_key="avg_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.avg_distance_km if data.avg_distance_km > 0 else None,
    ),
    # SNR range
    PSKReporterSensorEntityDescription(
        key="min_snr",
        translation_key="min_snr",
        native_unit_of_measurement="dB",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.min_snr if data.total_spots > 0 else None,
    ),
    PSKReporterSensorEntityDescription(
        key="max_snr",
        translation_key="max_snr",
        native_unit_of_measurement="dB",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.max_snr if data.total_spots > 0 else None,
    ),
    # Geographic
    PSKReporterSensorEntityDescription(
        key="unique_countries",
        translation_key="unique_countries",
        native_unit_of_measurement="countries",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.unique_countries,
        attr_fn=lambda data: {"countries": data.countries_list},
    ),
    PSKReporterSensorEntityDescription(
        key="farthest_station",
        translation_key="farthest_station",
        value_fn=lambda data: data.farthest_station or None,
        attr_fn=lambda data: {"distance_km": data.farthest_station_distance},
    ),
    # Temporal
    PSKReporterSensorEntityDescription(
        key="spots_last_hour",
        translation_key="spots_last_hour",
        native_unit_of_measurement="spots",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.spots_last_hour,
    ),
    # Derived metrics
    PSKReporterSensorEntityDescription(
        key="dx_ratio",
        translation_key="dx_ratio",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.dx_ratio if data.total_spots > 0 else None,
        attr_fn=lambda _: {"description": "Percentage of spots beyond 5000 km"},
    ),
    PSKReporterSensorEntityDescription(
        key="propagation_score",
        translation_key="propagation_score",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.propagation_score,
        attr_fn=lambda _: {
            "formula": "spots × countries × (max_distance_km / 1000)",
            "description": "Composite propagation quality metric",
        },
    ),
)

# Global mode sensors (no callsign - PSKReporter-wide stats)
GLOBAL_SENSOR_DESCRIPTIONS: tuple[PSKReporterSensorEntityDescription, ...] = (
    PSKReporterSensorEntityDescription(
        key="global_spots_sampled",
        translation_key="global_spots_sampled",
        native_unit_of_measurement="spots",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.health.total_messages,
        attr_fn=lambda data: {
            "sample_rate": f"1:{data.sample_rate}",
            "processed_messages": data.processed_messages,
        },
    ),
    PSKReporterSensorEntityDescription(
        key="global_unique_stations",
        translation_key="global_unique_stations",
        native_unit_of_measurement="stations",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.global_unique_stations,
    ),
    PSKReporterSensorEntityDescription(
        key="global_most_active_band",
        translation_key="global_most_active_band",
        value_fn=lambda data: (
            max(data.band_counts, key=data.band_counts.get)
            if data.band_counts
            else "Unknown"
        ),
        attr_fn=lambda data: {"band_counts": data.band_counts},
    ),
    PSKReporterSensorEntityDescription(
        key="global_most_active_mode",
        translation_key="global_most_active_mode",
        value_fn=lambda data: (
            max(data.mode_counts, key=data.mode_counts.get)
            if data.mode_counts
            else "Unknown"
        ),
        attr_fn=lambda data: {"mode_counts": data.mode_counts},
    ),
    PSKReporterSensorEntityDescription(
        key="connection_status",
        translation_key="connection_status",
        value_fn=lambda data: "Connected" if data.connected else "Disconnected",
        attr_fn=lambda data: {
            "transport_mode": data.health.transport_mode,
            "transport_port": data.health.transport_port,
            "reconnect_count": data.health.reconnect_count,
            "last_disconnect_reason": data.health.last_disconnect_reason,
            "subscribed_topics": data.health.subscribed_topics,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSKReporter sensors based on a config entry."""
    coordinator: PSKReporterCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    if coordinator.monitor_type == MONITOR_GLOBAL:
        # Global mode: add global sensors
        for description in GLOBAL_SENSOR_DESCRIPTIONS:
            entities.append(PSKReporterSensor(coordinator, description))

        # Add per-band sensors for HF bands
        for band in HF_BANDS:
            entities.append(PSKReporterBandSensor(coordinator, band))
    else:
        # Personal mode: add main activity sensors
        for description in SENSOR_DESCRIPTIONS:
            entities.append(PSKReporterSensor(coordinator, description))

        # Add extended sensors (v2.3.0)
        for description in EXTENDED_SENSOR_DESCRIPTIONS:
            entities.append(PSKReporterSensor(coordinator, description))

        # Add per-band sensors for HF bands (v2.3.0)
        for band in HF_BANDS:
            for metric in PERSONAL_BAND_METRICS:
                entities.append(PSKReporterPersonalBandSensor(coordinator, band, metric))

    # Add health sensors for both modes
    for description in HEALTH_SENSOR_DESCRIPTIONS:
        entities.append(PSKReporterSensor(coordinator, description))

    async_add_entities(entities)


class PSKReporterSensor(CoordinatorEntity[PSKReporterCoordinator], SensorEntity):
    """Representation of a PSKReporter sensor."""

    entity_description: PSKReporterSensorEntityDescription
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PSKReporterCoordinator,
        description: PSKReporterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        # Unique ID based on monitor type
        if coordinator.monitor_type == MONITOR_GLOBAL:
            self._attr_unique_id = f"global_monitor_{description.key}"
        else:
            self._attr_unique_id = f"{coordinator.callsign}_{coordinator.direction}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        if self.coordinator.monitor_type == MONITOR_GLOBAL:
            return DeviceInfo(
                identifiers={(DOMAIN, "global_monitor")},
                name="PSKReporter - Global Monitor",
                manufacturer="PSKReporter.info",
                model="PSKReporter HA Bridge (Global)",
                sw_version="2.3.0",
                configuration_url="https://pskreporter.info",
            )
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.callsign}_{self.coordinator.direction}")},
            name=f"PSKReporter - {self.coordinator.callsign}",
            manufacturer="PSKReporter.info",
            model="PSKReporter HA Bridge",
            sw_version="2.3.0",
            configuration_url="https://pskreporter.info",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator.data)
        return None


class PSKReporterBandSensor(CoordinatorEntity[PSKReporterCoordinator], SensorEntity):
    """Sensor for per-band activity in global mode."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "spots"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PSKReporterCoordinator,
        band: str,
    ) -> None:
        """Initialize the band sensor."""
        super().__init__(coordinator)
        self._band = band
        self._attr_unique_id = f"global_monitor_band_{band}"
        self._attr_translation_key = "band_activity"
        self._attr_translation_placeholders = {"band": band}
        # Fallback name if translation not available
        self._attr_name = f"{band} Activity"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, "global_monitor")},
            name="PSKReporter - Global Monitor",
            manufacturer="PSKReporter.info",
            model="PSKReporter HA Bridge (Global)",
            sw_version="2.3.0",
            configuration_url="https://pskreporter.info",
        )

    @property
    def native_value(self) -> int:
        """Return the spot count for this band."""
        return self.coordinator.data.band_counts.get(self._band, 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "band": self._band,
            "percentage": self._calculate_percentage(),
        }

    def _calculate_percentage(self) -> float:
        """Calculate what percentage of total spots this band represents."""
        total = sum(self.coordinator.data.band_counts.values())
        if total == 0:
            return 0.0
        band_count = self.coordinator.data.band_counts.get(self._band, 0)
        return round((band_count / total) * 100, 1)


# Per-band metric types for personal mode (v2.3.0)
PERSONAL_BAND_METRICS = {
    "spots": {
        "unit": "spots",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": None,
        "attr_key": "spots",
    },
    "avg_snr": {
        "unit": "dB",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": None,
        "attr_key": "avg_snr",
    },
    "max_distance": {
        "unit": UnitOfLength.KILOMETERS,
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.DISTANCE,
        "attr_key": "max_distance_km",
    },
    "unique_stations": {
        "unit": "stations",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": None,
        "attr_key": "unique_stations",
    },
    "unique_countries": {
        "unit": "countries",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": None,
        "attr_key": "unique_countries",
    },
}


class PSKReporterPersonalBandSensor(CoordinatorEntity[PSKReporterCoordinator], SensorEntity):
    """Sensor for per-band statistics in personal mode (v2.3.0)."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PSKReporterCoordinator,
        band: str,
        metric: str,
    ) -> None:
        """Initialize the personal band sensor."""
        super().__init__(coordinator)
        self._band = band
        self._metric = metric

        # Get metric configuration
        metric_config = PERSONAL_BAND_METRICS.get(metric, {})

        self._attr_unique_id = f"{coordinator.callsign}_{coordinator.direction}_band_{band}_{metric}"
        self._attr_native_unit_of_measurement = metric_config.get("unit")
        self._attr_state_class = metric_config.get("state_class")
        if metric_config.get("device_class"):
            self._attr_device_class = metric_config["device_class"]

        # Translation key for per-band sensors
        self._attr_translation_key = f"band_{metric}"
        self._attr_translation_placeholders = {"band": band}
        # Fallback name
        metric_name = metric.replace("_", " ").title()
        self._attr_name = f"{band} {metric_name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.callsign}_{self.coordinator.direction}")},
            name=f"PSKReporter - {self.coordinator.callsign}",
            manufacturer="PSKReporter.info",
            model="PSKReporter HA Bridge",
            sw_version="2.3.0",
            configuration_url="https://pskreporter.info",
        )

    @property
    def native_value(self) -> Any:
        """Return the value for this band and metric."""
        band_stats: BandStats | None = self.coordinator.data.band_stats.get(self._band)
        if not band_stats:
            # Return appropriate default based on metric type
            if self._metric in ("spots", "unique_stations", "unique_countries"):
                return 0
            return None

        # Get the value from band_stats
        metric_config = PERSONAL_BAND_METRICS.get(self._metric, {})
        attr_key = metric_config.get("attr_key", self._metric)
        value = getattr(band_stats, attr_key, None)

        # Return None for zero distances/SNR to indicate no data
        if self._metric in ("avg_snr", "max_distance") and value == 0:
            return None
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        band_stats: BandStats | None = self.coordinator.data.band_stats.get(self._band)
        attrs = {"band": self._band, "metric": self._metric}

        if band_stats:
            # Add relevant context based on metric
            if self._metric == "spots":
                attrs["dominant_mode"] = band_stats.dominant_mode
            elif self._metric == "avg_snr":
                attrs["min_snr"] = band_stats.min_snr
                attrs["max_snr"] = band_stats.max_snr
            elif self._metric == "max_distance":
                attrs["avg_distance_km"] = band_stats.avg_distance_km
            elif self._metric == "unique_countries":
                attrs["countries"] = band_stats.countries_list

        return attrs
