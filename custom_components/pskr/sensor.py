"""Sensor platform for PSKReporter HA Bridge."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
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

from .const import ATTRIBUTION, DOMAIN
from .coordinator import PSKReporterCoordinator, PSKReporterData


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
            datetime.fromtimestamp(data.last_spot_time).isoformat()
            if data.last_spot_time > 0
            else None
        ),
    ),
    PSKReporterSensorEntityDescription(
        key="connection_status",
        translation_key="connection_status",
        value_fn=lambda data: "Connected" if data.connected else "Disconnected",
        attr_fn=lambda data: {
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
        value_fn=lambda data: "Healthy" if data.health.feed_healthy else "Unhealthy",
        attr_fn=lambda data: {
            "last_message_time": (
                datetime.fromtimestamp(data.health.last_message_time).isoformat()
                if data.health.last_message_time > 0
                else None
            ),
            "feed_latency_seconds": round(data.health.feed_latency, 1),
            "threshold_seconds": 60,
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSKReporter sensors based on a config entry."""
    coordinator: PSKReporterCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[PSKReporterSensor] = []

    # Add main sensors
    for description in SENSOR_DESCRIPTIONS:
        entities.append(PSKReporterSensor(coordinator, description))

    # Add health sensors
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
        self._attr_unique_id = f"{coordinator.callsign}_{coordinator.direction}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.callsign}_{self.coordinator.direction}")},
            name=f"PSKReporter - {self.coordinator.callsign}",
            manufacturer="PSKReporter.info",
            model="PSKReporter HA Bridge",
            sw_version="2.0.0",
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
