"""Integration for Repsol Luz y Gas."""

import aiohttp
import asyncio
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    LOGGER,
    LOGIN_URL,
    CONTRACTS_URL,
    HOUSES_URL,
    INVOICES_URL,
    COSTS_URL,
    NEXT_INVOICE_URL,
    VIRTUAL_BATTERY_HISTORY_URL,
    UPDATE_INTERVAL,
    LOGIN_HEADERS,
    CONTRACTS_HEADERS,
    COOKIES_CONST,
    LOGIN_DATA,
)

# Config only by config entries
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Repsol Luz y Gas integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Repsol Luz y Gas integration from a config entry."""
    session = async_get_clientsession(hass)

    selected_contract_id = entry.data.get("contract_id")  # puede ser None

    client = RepsolLuzYGasAPI(
        session=session,
        username=entry.data["username"],
        password=entry.data["password"],
        selected_contract_id=selected_contract_id,
    )

    async def async_update_data_start():
        try:
            return await client.fetch_all_data()
        except Exception as e:
            raise UpdateFailed(f"Error fetching data: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name="repsolluzygas",
        update_method=async_update_data_start,
        update_interval=UPDATE_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class RepsolLuzYGasAPI:
    """Class to communicate with Repsol Luz y Gas API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        selected_contract_id: str | None = None,
    ):
        """Initialize the API client."""
        self.session = session
        self.username = username
        self.password = password
        self.uid = None
        self.signature = None
        self.timestamp = None
        self.selected_contract_id = selected_contract_id
        # ⬇️ cookies por instancia (no a nivel de clase)
        self.cookies = COOKIES_CONST.copy()

    async def async_login(self):
        """Asynchronously login to the Repsol API."""
        data = LOGIN_DATA.copy()
        data.update(
            {
                "loginID": self.username,
                "password": self.password,
            }
        )
        headers = LOGIN_HEADERS.copy()

        try:
            async with self.session.post(
                LOGIN_URL, headers=headers, cookies=self.cookies, data=data
            ) as response:
                text = await response.text()
                if response.status != 200:
                    LOGGER.error(
                        "Login failed. HTTP %s. Body: %s",
                        response.status,
                        text[:500],
                    )
                    raise Exception("login_failed_http")

                try:
                    payload = await response.json(content_type=None)
                except Exception:
                    LOGGER.error("Login parse error. Body: %s", text[:500])
                    raise Exception("login_failed_parse")

                LOGGER.debug("Login payload: %s", payload)
                user_info = payload.get("userInfo") or {}
                self.uid = user_info.get("UID")
                self.signature = user_info.get("UIDSignature")
                self.timestamp = user_info.get("signatureTimestamp")

                if not (self.uid and self.signature and self.timestamp):
                    LOGGER.error("Login missing tokens. userInfo=%s", user_info)
                    raise Exception("login_failed_tokens")

                return True

        except Exception as e:
            LOGGER.error("Error during login to Repsol API: %s", e)
            raise

    async def async_get_contracts(self):
        """Retrieve contracts.

        Returns:
        {
          "information": [
             {"contract_id":"...", "contractType":"ELECTRICITY","cups":"...","active":True,"house_id":"..."},
             ...
          ]
        }
        """
        headers = CONTRACTS_HEADERS.copy()
        headers.update(
            {
                "UID": self.uid,
                "signature": self.signature,
                "signatureTimestamp": self.timestamp,
            }
        )

        url = CONTRACTS_URL
        contracts = {"information": []}

        try:
            async with asyncio.timeout(10):
                async with self.session.get(
                    url, headers=headers, cookies=self.cookies
                ) as response:
                    LOGGER.debug("Contracts Headers: %s", headers)
                    if response.status == 200:
                        data = await response.json()
                        LOGGER.debug("Contracts Data %s", data)

                        if data:
                            for house in data:
                                house_id = house.get("code")
                                for contract in house.get("contracts", []):
                                    info = {
                                        "contract_id": contract.get("code"),
                                        "contractType": contract.get("contractType"),
                                        "cups": contract.get("cups"),
                                        "active": contract.get("status") == "ACTIVE",
                                        "house_id": house_id,
                                    }
                                    contracts["information"].append(info)
                            LOGGER.debug("Contracts Parsed %s", contracts)
                        else:
                            LOGGER.warning("No contract data received")
                    else:
                        LOGGER.error(
                            "Failed to fetch contracts data. HTTP Status: %s",
                            response.status,
                        )
                        return None
        except Exception as e:
            LOGGER.error("Error fetching contracts data: %s", e)
            return None

        return contracts

    async def async_get_invoices(self, house_id, contract_id):
        """Retrieve the latest invoice for a given contract."""
        headers = CONTRACTS_HEADERS.copy()
        headers.update(
            {
                "UID": self.uid,
                "signature": self.signature,
                "signatureTimestamp": self.timestamp,
            }
        )
        url = INVOICES_URL.format(house_id, contract_id)

        try:
            async with asyncio.timeout(10):
                async with self.session.get(
                    url, headers=headers, cookies=self.cookies
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        LOGGER.debug("Invoices Data %s", response_data)
                        return response_data
                    else:
                        LOGGER.error(
                            "Failed to fetch invoice data. HTTP Status: %s",
                            response.status,
                        )
                        return None
        except Exception as e:
            LOGGER.error("Error fetching invoice data: %s", e)
            return None

    async def async_get_costs(self, house_id, contract_id):
        """Retrieve cost data for a given contract."""
        headers = CONTRACTS_HEADERS.copy()
        headers.update(
            {
                "UID": self.uid,
                "signature": self.signature,
                "signatureTimestamp": self.timestamp,
            }
        )
        url = COSTS_URL.format(house_id, contract_id)
        data = {
            "totalDays": 0,
            "consumption": 0,
            "amount": 0,
            "amountVariable": 0,
            "amountFixed": 0,
            "averageAmount": 0,
        }

        try:
            async with asyncio.timeout(10):
                async with self.session.get(
                    url, headers=headers, cookies=self.cookies
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        for var in data.keys():
                            data[var] = response_data.get(var, 0)
                        LOGGER.debug("Costs Data %s", data)
                    else:
                        LOGGER.error(
                            "Failed to fetch costs data. HTTP Status: %s",
                            response.status,
                        )
        except Exception as e:
            LOGGER.error("Error fetching costs data: %s", e)

        return data

    async def async_get_next_invoice(self, house_id, contract_id):
        """Retrieve next invoice data for a given contract."""
        headers = CONTRACTS_HEADERS.copy()
        headers.update(
            {
                "UID": self.uid,
                "signature": self.signature,
                "signatureTimestamp": self.timestamp,
            }
        )
        url = NEXT_INVOICE_URL.format(house_id, contract_id)
        data = {
            "amount": 0,
            "amountVariable": 0,
            "amountFixed": 0,
        }

        try:
            async with asyncio.timeout(10):
                async with self.session.get(
                    url, headers=headers, cookies=self.cookies
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        for var in data.keys():
                            data[var] = response_data.get(var, 0)
                        LOGGER.debug("Next Invoice Data %s", data)
                    else:
                        LOGGER.debug(
                            "Failed to fetch next invoice data. HTTP Status: %s",
                            response.status,
                        )
        except Exception as e:
            LOGGER.debug("Error fetching next invoice data: %s", e)

        return data

    async def async_get_virtual_battery_history(self, house_id, contract_id):
        """Retrieve virtual battery history for a given contract."""
        headers = CONTRACTS_HEADERS.copy()
        headers.update(
            {
                "UID": self.uid,
                "signature": self.signature,
                "signatureTimestamp": self.timestamp,
            }
        )
        url = VIRTUAL_BATTERY_HISTORY_URL.format(house_id, contract_id)

        try:
            async with asyncio.timeout(10):
                async with self.session.get(
                    url, headers=headers, cookies=self.cookies
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        LOGGER.debug("Virtual Battery History Data %s", response_data)
                        return response_data
                    else:
                        LOGGER.error(
                            "Failed to fetch Virtual Battery History data. HTTP Status: %s",
                            response.status,
                        )
                        return None
        except Exception as e:
            LOGGER.error("Error fetching Virtual Battery History data: %s", e)
            return None

    async def async_get_houseDetails(self, house_id):
        """Fetch house details including contracts and SVA data."""
        headers = CONTRACTS_HEADERS.copy()
        headers.update(
            {
                "UID": self.uid,
                "signature": self.signature,
                "signatureTimestamp": self.timestamp,
            }
        )
        url = HOUSES_URL.format(house_id)

        try:
            async with asyncio.timeout(10):
                async with self.session.get(
                    url, headers=headers, cookies=self.cookies
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        LOGGER.debug("House Data %s", response_data)
                        return response_data
                    else:
                        LOGGER.error(
                            "Failed to fetch house data. HTTP Status: %s",
                            response.status,
                        )
                        return None
        except Exception as e:
            LOGGER.error("Error fetching house data: %s", e)
            return None

    async def fetch_all_data(self):
        """Fetch and combine all necessary data from the API.

        Si self.selected_contract_id está definido, solo consulta ese contrato.
        """
        try:
            await self.async_login()
            contracts_data = await self.async_get_contracts()
            if not contracts_data:
                raise Exception("Failed to fetch contracts.")

            all_data: dict = {}

            # Lista de contratos a consultar
            contracts_list = contracts_data.get("information", [])

            if self.selected_contract_id:
                contracts_list = [
                    c for c in contracts_list if c["contract_id"] == self.selected_contract_id
                ]
                if not contracts_list:
                    raise Exception(
                        f"Selected contract_id {self.selected_contract_id} not found"
                    )

            for contract in contracts_list:
                house_id = contract["house_id"]
                contract_id = contract["contract_id"]

                house_data = await self.async_get_houseDetails(house_id)
                invoices_data = await self.async_get_invoices(house_id, contract_id)
                costs_data = await self.async_get_costs(house_id, contract_id)
                next_invoice_data = await self.async_get_next_invoice(
                    house_id, contract_id
                )

                virtual_battery_history_data = None
                if contract.get("contractType") == "ELECTRICITY":
                    virtual_battery_history_data = await self.async_get_virtual_battery_history(
                        house_id, contract_id
                    )

                all_data[contract_id] = {
                    "contracts": contract,
                    "house_data": house_data,
                    "invoices": invoices_data,
                    "costs": costs_data,
                    "nextInvoice": next_invoice_data,
                    "virtual_battery_history": virtual_battery_history_data,
                }

            LOGGER.debug("Sensor Data %s", all_data)
            return all_data

        except Exception as e:
            LOGGER.error(f"Error fetching all data: {e}")
            raise