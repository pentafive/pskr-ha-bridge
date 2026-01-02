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
    CONF_DIRECTION,
    CONF_MAX_DISTANCE,
    CONF_MIN_DISTANCE,
    CONF_MODE_FILTER,
    DEFAULT_DIRECTION,
    DIGITAL_MODES,
    DIRECTION_DUAL,
    DIRECTION_RX,
    DIRECTION_TX,
    DOMAIN,
)

CALLSIGN_REGEX = re.compile(r"^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}[A-Z](?:/[A-Z0-9]+)?$", re.IGNORECASE)


def validate_callsign(callsign: str) -> str | None:
    """Validate amateur radio callsign format."""
    callsign = callsign.strip().upper()
    if not CALLSIGN_REGEX.match(callsign):
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
            callsign = user_input[CONF_CALLSIGN].strip().upper()

            if error := validate_callsign(callsign):
                errors["base"] = error
            else:
                await self.async_set_unique_id(f"{callsign}_{user_input[CONF_DIRECTION]}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"PSKReporter - {callsign}",
                    data={
                        CONF_CALLSIGN: callsign,
                        CONF_DIRECTION: user_input[CONF_DIRECTION],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CALLSIGN): str,
                    vol.Required(CONF_DIRECTION, default=DEFAULT_DIRECTION): vol.In(
                        {
                            DIRECTION_RX: "Receive (spots where I am receiving)",
                            DIRECTION_TX: "Transmit (spots where others hear me)",
                            DIRECTION_DUAL: "Both (RX and TX spots)",
                        }
                    ),
                }
            ),
            errors=errors,
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

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MIN_DISTANCE,
                        default=options.get(CONF_MIN_DISTANCE, 0),
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_MAX_DISTANCE,
                        default=options.get(CONF_MAX_DISTANCE, 0),
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_MODE_FILTER,
                        default=options.get(CONF_MODE_FILTER, []),
                    ): vol.All(
                        vol.Coerce(list),
                        [vol.In(DIGITAL_MODES)],
                    ),
                }
            ),
        )
