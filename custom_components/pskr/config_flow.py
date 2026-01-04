"""Config flow for PSKReporter Monitor integration."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CALLSIGN,
    CONF_COUNT_ONLY,
    CONF_DIRECTION,
    CONF_MAX_DISTANCE,
    CONF_MIN_DISTANCE,
    CONF_MODE_FILTER,
    CONF_SAMPLE_RATE,
    DEFAULT_COUNT_ONLY,
    DEFAULT_DIRECTION,
    DEFAULT_SAMPLE_RATE,
    DIGITAL_MODES,
    DIRECTION_DUAL,
    DIRECTION_RX,
    DIRECTION_TX,
    DOMAIN,
    MONITOR_GLOBAL,
    MONITOR_PERSONAL,
)

CALLSIGN_REGEX = re.compile(r"^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}[A-Z](?:/[A-Z0-9]+)?$", re.IGNORECASE)


def validate_callsign(callsign: str) -> str | None:
    """Validate amateur radio callsign format. Empty is valid for global mode."""
    callsign = callsign.strip().upper()
    if callsign and not CALLSIGN_REGEX.match(callsign):
        return "invalid_callsign"
    return None


class PSKReporterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PSKReporter Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            callsign = user_input.get(CONF_CALLSIGN, "").strip().upper()

            if error := validate_callsign(callsign):
                errors["base"] = error
            else:
                # Determine monitor type based on callsign
                if callsign:
                    # Personal monitor
                    monitor_type = MONITOR_PERSONAL
                    direction = user_input.get(CONF_DIRECTION, DEFAULT_DIRECTION)
                    unique_id = f"{callsign}_{direction}"
                    title = f"PSKReporter - {callsign}"
                else:
                    # Global monitor
                    monitor_type = MONITOR_GLOBAL
                    direction = DIRECTION_RX  # Not used for global
                    unique_id = "global_monitor"
                    title = "PSKReporter - Global Monitor"

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_CALLSIGN: callsign,
                        CONF_DIRECTION: direction,
                        "monitor_type": monitor_type,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CALLSIGN, default=""): str,
                    vol.Optional(CONF_DIRECTION, default=DEFAULT_DIRECTION): vol.In(
                        {
                            DIRECTION_RX: "Receive (spots where I am receiving)",
                            DIRECTION_TX: "Transmit (spots where others hear me)",
                            DIRECTION_DUAL: "Both (RX and TX spots)",
                        }
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "global_hint": "Leave callsign empty for global propagation monitor"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return PSKReporterOptionsFlow(config_entry)


class PSKReporterOptionsFlow(OptionsFlow):
    """Handle options flow for PSKReporter Monitor."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        is_global = self.config_entry.data.get("monitor_type") == MONITOR_GLOBAL

        # Base schema for all monitor types
        schema_dict: dict[vol.Marker, Any] = {
            vol.Optional(
                CONF_COUNT_ONLY,
                default=options.get(CONF_COUNT_ONLY, DEFAULT_COUNT_ONLY),
            ): bool,
        }

        # Add sample rate option (more relevant for global, but available for all)
        schema_dict[vol.Optional(
            CONF_SAMPLE_RATE,
            default=options.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE),
        )] = vol.All(vol.Coerce(int), vol.Range(min=1, max=100))

        # Personal monitor gets distance and mode filters
        if not is_global:
            schema_dict[vol.Optional(
                CONF_MIN_DISTANCE,
                default=options.get(CONF_MIN_DISTANCE, 0),
            )] = vol.Coerce(int)
            schema_dict[vol.Optional(
                CONF_MAX_DISTANCE,
                default=options.get(CONF_MAX_DISTANCE, 0),
            )] = vol.Coerce(int)
            schema_dict[vol.Optional(
                CONF_MODE_FILTER,
                default=options.get(CONF_MODE_FILTER, []),
            )] = vol.All(vol.Coerce(list), [vol.In(DIGITAL_MODES)])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
