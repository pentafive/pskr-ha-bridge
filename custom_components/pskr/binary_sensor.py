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

    async_add_entities([
        PSKReporterFeedHealthBinarySensor(coordinator),
    ])


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
                sw_version="2.0.1",
                configuration_url="https://pskreporter.info",
            )
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.callsign}_{self.coordinator.direction}")},
            name=f"PSKReporter - {self.coordinator.callsign}",
            manufacturer="PSKReporter.info",
            model="PSKReporter HA Bridge",
            sw_version="2.0.1",
            configuration_url="https://pskreporter.info",
        )

    @property
    def is_on(self) -> bool:
        """Return true if feed is healthy (data flowing)."""
        return self.coordinator.data.health.feed_healthy

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        health = self.coordinator.data.health
        return {
            "connected": self.coordinator.data.connected,
            "last_message_seconds_ago": round(health.feed_latency, 1),
            "messages_last_minute": health.messages_last_minute,
            "total_messages": health.total_messages,
            "healthy_threshold_seconds": 60,
            "reason": self._get_health_reason(),
        }

    def _get_health_reason(self) -> str:
        """Get human-readable reason for health status."""
        health = self.coordinator.data.health

        if not self.coordinator.data.connected:
            return "Not connected to MQTT broker"

        if health.last_message_time == 0:
            return "No messages received yet"

        if health.feed_latency >= 60:
            return f"No messages for {int(health.feed_latency)} seconds (PSKReporter feed may be down)"

        return "Feed is healthy - data flowing normally"
