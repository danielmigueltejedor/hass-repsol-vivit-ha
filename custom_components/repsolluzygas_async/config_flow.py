"""Config flow for Repsol Luz y Gas."""
from __future__ import annotations

import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    LOGGER,
    LOGIN_URL,
    CONTRACTS_URL,
    LOGIN_HEADERS,
    CONTRACTS_HEADERS,
    COOKIES_CONST,
    LOGIN_DATA,
)

class RepsolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._creds: dict[str, Any] | None = None
        self._contracts: list[dict[str, Any]] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input is not None:
            # 1) Login
            session = async_get_clientsession(self.hass)
            cookies = COOKIES_CONST.copy()
            data = LOGIN_DATA.copy()
            data.update(
                {"loginID": user_input["username"], "password": user_input["password"]}
            )
            headers = LOGIN_HEADERS.copy()

            try:
                async with session.post(
                    LOGIN_URL, headers=headers, cookies=cookies, data=data
                ) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        LOGGER.error("Login failed in flow. HTTP %s Body=%s", resp.status, text[:500])
                        errors["base"] = "invalid_auth"
                    else:
                        payload = await resp.json(content_type=None)
                        ui = payload.get("userInfo") or {}
                        uid = ui.get("UID")
                        sig = ui.get("UIDSignature")
                        ts = ui.get("signatureTimestamp")
                        if not (uid and sig and ts):
                            LOGGER.error("Login tokens missing in flow. userInfo=%s", ui)
                            errors["base"] = "invalid_auth"
                        else:
                            # 2) Get contracts
                            headers2 = CONTRACTS_HEADERS.copy()
                            headers2.update({"UID": uid, "signature": sig, "signatureTimestamp": ts})

                            async with session.get(CONTRACTS_URL, headers=headers2, cookies=cookies) as r2:
                                if r2.status != 200:
                                    LOGGER.error("Contracts fetch failed in flow. HTTP %s", r2.status)
                                    errors["base"] = "cannot_connect"
                                else:
                                    data2 = await r2.json()
                                    contracts: list[dict] = []
                                    for house in data2 or []:
                                        hid = house.get("code")
                                        for c in house.get("contracts", []):
                                            contracts.append(
                                                {
                                                    "code": c.get("code"),
                                                    "cups": c.get("cups"),
                                                    "type": c.get("contractType"),
                                                    "house_id": hid,
                                                }
                                            )
                                    if not contracts:
                                        errors["base"] = "no_contracts"
                                    else:
                                        self._creds = {
                                            "username": user_input["username"],
                                            "password": user_input["password"],
                                        }
                                        self._contracts = contracts
                                        return await self.async_step_contract()

            except Exception as e:
                LOGGER.error("Flow error: %s", e)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_contract(self, user_input: dict[str, Any] | None = None):
        assert self._contracts is not None
        # Mapa code -> "TYPE - CUPS"
        opts = {c["code"]: f'{(c.get("type") or "").upper()} - {c.get("cups") or ""}' for c in self._contracts}

        errors = {}
        if user_input is not None:
            code = user_input["contract_code"]
            selected = next(c for c in self._contracts if c["code"] == code)
            title = f'{(selected.get("type") or "ELECTRICITY").upper()} - {selected.get("cups") or code}'

            data = {
                **self._creds,
                "contract_id": selected["code"],
            }

            # Unique por contrato para permitir varias entradas (una por contrato)
            await self.async_set_unique_id(f"repsol_{selected['code']}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="contract",
            data_schema=vol.Schema({vol.Required("contract_code"): vol.In(opts)}),
            errors=errors,
        )