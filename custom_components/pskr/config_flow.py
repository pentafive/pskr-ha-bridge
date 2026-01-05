"""Config flow for PSKReporter Monitor integration."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_CALLSIGN,
    CONF_CALLSIGN_ALLOW,
    CONF_CALLSIGN_BLOCK,
    CONF_COUNT_ONLY,
    CONF_COUNTRY_ALLOW,
    CONF_COUNTRY_BLOCK,
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

CONF_MONITOR_TYPE = "monitor_type"


def validate_callsign(callsign: str) -> str | None:
    """Validate amateur radio callsign format."""
    callsign = callsign.strip().upper()
    if not callsign:
        return "callsign_required"
    if not CALLSIGN_REGEX.match(callsign):
        return "invalid_callsign"
    return None


class PSKReporterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PSKReporter Monitor."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._monitor_type: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - choose monitor type."""
        if user_input is not None:
            self._monitor_type = user_input[CONF_MONITOR_TYPE]

            if self._monitor_type == MONITOR_GLOBAL:
                # Global monitor - check uniqueness and create entry
                await self.async_set_unique_id("global_monitor")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="PSKReporter - Global Monitor",
                    data={
                        CONF_CALLSIGN: "",
                        CONF_DIRECTION: DIRECTION_RX,
                        CONF_MONITOR_TYPE: MONITOR_GLOBAL,
                    },
                )
            # Personal monitor - proceed to callsign step
            return await self.async_step_callsign()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MONITOR_TYPE, default=MONITOR_PERSONAL): vol.In(
                        {
                            MONITOR_PERSONAL: "Personal Monitor (track my callsign)",
                            MONITOR_GLOBAL: "Global Monitor (network-wide propagation)",
                        }
                    ),
                }
            ),
        )

    async def async_step_callsign(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the callsign configuration step for personal monitor."""
        errors: dict[str, str] = {}

        if user_input is not None:
            callsign = user_input.get(CONF_CALLSIGN, "").strip().upper()

            if error := validate_callsign(callsign):
                errors["base"] = error
            else:
                direction = user_input.get(CONF_DIRECTION, DEFAULT_DIRECTION)
                unique_id = f"{callsign}_{direction}"

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"PSKReporter - {callsign}",
                    data={
                        CONF_CALLSIGN: callsign,
                        CONF_DIRECTION: direction,
                        CONF_MONITOR_TYPE: MONITOR_PERSONAL,
                    },
                )

        return self.async_show_form(
            step_id="callsign",
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
    def async_get_options_flow(_config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return PSKReporterOptionsFlow()


class PSKReporterOptionsFlow(OptionsFlow):
    """Handle options flow for PSKReporter Monitor."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert comma-separated strings to lists for callsign/country filters
            processed_input = dict(user_input)
            for key in [CONF_CALLSIGN_ALLOW, CONF_CALLSIGN_BLOCK, CONF_COUNTRY_ALLOW, CONF_COUNTRY_BLOCK]:
                if key in processed_input and isinstance(processed_input[key], str):
                    # Split by comma, strip whitespace, filter empty, uppercase callsigns
                    items = [item.strip() for item in processed_input[key].split(",") if item.strip()]
                    if key in [CONF_CALLSIGN_ALLOW, CONF_CALLSIGN_BLOCK]:
                        items = [item.upper() for item in items]
                    processed_input[key] = items
            return self.async_create_entry(title="", data=processed_input)

        options = self.config_entry.options
        is_global = self.config_entry.data.get(CONF_MONITOR_TYPE) == MONITOR_GLOBAL

        # Base schema for all monitor types
        schema_dict: dict[vol.Marker, Any] = {
            vol.Optional(
                CONF_COUNT_ONLY,
                default=options.get(CONF_COUNT_ONLY, DEFAULT_COUNT_ONLY),
            ): bool,
            vol.Optional(
                CONF_SAMPLE_RATE,
                default=options.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        }

        # Personal monitor gets additional filter options
        if not is_global:
            schema_dict[vol.Optional(
                CONF_MIN_DISTANCE,
                default=options.get(CONF_MIN_DISTANCE, 0),
            )] = vol.Coerce(int)
            schema_dict[vol.Optional(
                CONF_MAX_DISTANCE,
                default=options.get(CONF_MAX_DISTANCE, 0),
            )] = vol.Coerce(int)
            # Multi-select for digital modes
            schema_dict[vol.Optional(
                CONF_MODE_FILTER,
                default=options.get(CONF_MODE_FILTER, []),
            )] = SelectSelector(
                SelectSelectorConfig(
                    options=DIGITAL_MODES,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
            # Callsign allow/block lists (comma-separated strings converted to lists)
            schema_dict[vol.Optional(
                CONF_CALLSIGN_ALLOW,
                default=",".join(options.get(CONF_CALLSIGN_ALLOW, [])),
            )] = str
            schema_dict[vol.Optional(
                CONF_CALLSIGN_BLOCK,
                default=",".join(options.get(CONF_CALLSIGN_BLOCK, [])),
            )] = str
            # Country allow/block lists (DXCC codes, comma-separated)
            schema_dict[vol.Optional(
                CONF_COUNTRY_ALLOW,
                default=",".join(options.get(CONF_COUNTRY_ALLOW, [])),
            )] = str
            schema_dict[vol.Optional(
                CONF_COUNTRY_BLOCK,
                default=",".join(options.get(CONF_COUNTRY_BLOCK, [])),
            )] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
