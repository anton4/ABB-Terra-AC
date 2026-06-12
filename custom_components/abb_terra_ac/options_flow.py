"""Options flow for ABB Terra AC (runtime settings separate from host/port)."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class AbbTerraAcOptionsFlow(config_entries.OptionsFlow):
    """Options flow: polling interval and future runtime-only settings."""

    def _communication_timeout(self) -> int | None:
        """Charger's Modbus communication timeout from the latest poll, if known."""
        runtime = getattr(self.config_entry, "runtime_data", None)
        if runtime is None or runtime.coordinator.data is None:
            return None
        timeout = int(runtime.coordinator.data.get("communication_timeout") or 0)
        return timeout or None

    async def async_step_init(
        self, user_input: dict[str, int] | None = None
    ) -> ConfigFlowResult:
        """Offer options form."""
        errors: dict[str, str] = {}
        timeout = self._communication_timeout()

        if user_input is not None:
            # The charger flags lost communication (and may stop the session or
            # drop to the fallback limit) when no register is read within its
            # communication timeout, so polling must happen more often.
            if timeout is not None and int(user_input[CONF_SCAN_INTERVAL]) >= timeout:
                errors[CONF_SCAN_INTERVAL] = "scan_interval_exceeds_timeout"
            else:
                return self.async_create_entry(title="", data=user_input)

        current = int(
            self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
            user_input if user_input is not None else {CONF_SCAN_INTERVAL: current},
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "communication_timeout": str(timeout) if timeout is not None else "?"
            },
        )
