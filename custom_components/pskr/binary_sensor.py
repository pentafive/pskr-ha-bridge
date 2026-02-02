"""Binary sensor platform for PSKReporter HA Bridge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, MONITOR_GLOBAL
from .coordinator import PSKReporterCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSKReporter binary sensors based on a config entry."""
    coordinator: PSKReporterCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        PSKReporterFeedHealthBinarySensor(coordinator),
    ]

    # Only add wanted match sensor for personal mode (v2.4.0)
    if coordinator.monitor_type != MONITOR_GLOBAL:
        entities.append(PSKReporterWantedMatchBinarySensor(coordinator))

    async_add_entities(entities)


class PSKReporterFeedHealthBinarySensor(
    CoordinatorEntity[PSKReporterCoordinator], BinarySensorEntity
):
    """Binary sensor for PSKReporter feed health."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "feed_health"

    def __init__(self, coordinator: PSKReporterCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        if coordinator.monitor_type == MONITOR_GLOBAL:
            self._attr_unique_id = "global_monitor_feed_health"
        else:
            self._attr_unique_id = f"{coordinator.callsign}_{coordinator.direction}_feed_health"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        if self.coordinator.monitor_type == MONITOR_GLOBAL:
            return DeviceInfo(
                identifiers={(DOMAIN, "global_monitor")},
                name="PSKReporter - Global Monitor",
                manufacturer="PSKReporter.info",
                model="PSKReporter HA Bridge (Global)",
                sw_version="2.4.0",
                configuration_url="https://pskreporter.info",
            )
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.callsign}_{self.coordinator.direction}")},
            name=f"PSKReporter - {self.coordinator.callsign}",
            manufacturer="PSKReporter.info",
            model="PSKReporter HA Bridge",
            sw_version="2.4.0",
            configuration_url="https://pskreporter.info",
        )

    @property
    def is_on(self) -> bool:
        """Return true if feed is healthy (data flowing)."""
        return self.coordinator.data.health.feed_healthy

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes.

        v2.2.0: Uses activity-aware thresholds from coordinator.
        """
        health = self.coordinator.data.health
        return {
            "connected": self.coordinator.data.connected,
            "last_message_seconds_ago": round(health.feed_latency, 1),
            "messages_last_minute": health.messages_last_minute,
            "total_messages": health.total_messages,
            "healthy_threshold_seconds": health.health_threshold_seconds,
            "feed_status": health.feed_status,  # v2.2.0: healthy, low_activity, stale, disconnected
            "reason": health.feed_status_reason,  # v2.2.0: uses coordinator's reason
        }


class PSKReporterWantedMatchBinarySensor(
    CoordinatorEntity[PSKReporterCoordinator], BinarySensorEntity
):
    """Binary sensor indicating a wanted DXCC/band match occurred (v2.4.0)."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_translation_key = "wanted_match"

    def __init__(self, coordinator: PSKReporterCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.callsign}_{coordinator.direction}_wanted_match"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, f"{self.coordinator.callsign}_{self.coordinator.direction}")
            },
            name=f"PSKReporter - {self.coordinator.callsign}",
            manufacturer="PSKReporter.info",
            model="PSKReporter HA Bridge",
            sw_version="2.4.0",
            configuration_url="https://pskreporter.info",
        )

    @property
    def is_on(self) -> bool:
        """Return true if a wanted match occurred within the stats window."""
        return self.coordinator.data.wanted_match

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "match_count": self.coordinator.data.wanted_match_count,
            "wanted_list_size": self.coordinator.data.wanted_list_size,
        }
