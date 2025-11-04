"""Platform for Repsol Luz y Gas sensor integration."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, LOGGER
from . import RepsolLuzYGasAPI


# === Definición de sensores (idéntica a tu original) ===
SENSOR_DEFINITIONS = [
    {"name": "Amount", "variable": "amount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Consumption", "variable": "consumption", "device_class": SensorDeviceClass.ENERGY},
    {"name": "Total Days", "variable": "totalDays", "device_class": None},
    {"name": "Amount Variable", "variable": "amountVariable", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Amount Fixed", "variable": "amountFixed", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Average Daily Amount", "variable": "averageAmount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Last Invoice", "variable": "lastInvoiceAmount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Last Invoice Paid", "variable": "lastInvoicePaid", "device_class": None},
    {"name": "Next Invoice Amount", "variable": "nextInvoiceAmount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Next Invoice Variable Amount", "variable": "nextInvoiceVariableAmount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Next Invoice Fixed Amount", "variable": "nextInvoiceFixedAmount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Contract Status", "variable": "status", "device_class": None},
    {"name": "Power", "variable": "power", "device_class": SensorDeviceClass.POWER},
    {"name": "Tariff", "variable": "fee", "device_class": None},
    {"name": "Power Price Punta", "variable": "pricesPowerPunta", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Power Price Valle", "variable": "pricesPowerValle", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Energy Price", "variable": "pricesEnergyAmount", "device_class": SensorDeviceClass.MONETARY},
    # GAS (solo se poblarán si el contrato es GAS)
    {"name": "Gas Fixed Term", "variable": "fixedTerm", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Gas Variable Term", "variable": "variableTerm", "device_class": SensorDeviceClass.MONETARY},
]

VB_SENSORS = [
    {"name": "Virtual Battery Amount Pending", "variable": "pendingAmount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Virtual Battery kWh Available", "variable": "kwhAvailable", "device_class": SensorDeviceClass.ENERGY},
    {"name": "Virtual Battery Total Amount Redeemed", "variable": "appliedAmount", "device_class": SensorDeviceClass.MONETARY},
    {"name": "Virtual Battery Total kWh Redeemed", "variable": "kwhRedeemed", "device_class": SensorDeviceClass.ENERGY},
    {"name": "Virtual Battery Total kWh Charged", "variable": "totalKWh", "device_class": SensorDeviceClass.ENERGY},
    {"name": "Virtual Battery Excedents Price", "variable": "excedentsPrice", "device_class": SensorDeviceClass.MONETARY},
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Repsol Luz y Gas sensors based on a config entry."""
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]
    api: RepsolLuzYGasAPI = stored["api"]

    # Estructura que viene del coordinator:
    # { contract_id: { "contracts": {...(incluye house_id)...}, "house_data": {...}, "invoices": {... o [..]}, "costs": {...}, "nextInvoice": {...}, "virtual_battery_history": {...} } }
    all_data: Dict[str, Dict[str, Any]] = coordinator.data or {}
    if not all_data:
        LOGGER.error("Coordinator has no data; cannot create sensors.")
        return

    # Filtra por contrato seleccionado (si procede)
    if api.selected_contract_id:
        payload = all_data.get(api.selected_contract_id)
        if not payload:
            LOGGER.error("Selected contract_id %s not found in coordinator data", api.selected_contract_id)
            return
        contracts_to_create = {api.selected_contract_id: payload}
    else:
        contracts_to_create = all_data

    entities: List[SensorEntity] = []

    for contract_id, payload in contracts_to_create.items():
        if not payload:
            continue

        contract_info = payload.get("contracts") or {}
        cups = contract_info.get("cups") or contract_id
        ctype = (contract_info.get("contractType") or "ELECTRICITY").upper()
        house_id = contract_info.get("house_id")

        # Enriquecemos con house_data: allí suelen venir power/fee/prices/sva
        house_data = payload.get("house_data") or {}
        house_contracts = house_data.get("contracts") or []
        house_contract = next((c for c in house_contracts if c.get("code") == contract_id), {})  # puede estar vacío

        # Device para agrupar
        device = DeviceInfo(
            identifiers={(DOMAIN, f"{house_id}_{contract_id}")},
            name=f"{ctype} - {cups}",
            manufacturer="Repsol Luz y Gas",
            model=ctype,
            serial_number=str(contract_id),
            configuration_url="https://areacliente.repsol.es/productos-y-servicios",
        )

        # === Sensores de costes/estado/facturas/tarifa ===
        for sd in SENSOR_DEFINITIONS:
            name = sd["name"]
            var = sd["variable"]
            devc = sd["device_class"]

            # Filtrado GAS vs ELECTRICIDAD manteniendo tu lógica
            if (ctype == "GAS" and "Gas" in name) or (ctype == "ELECTRICITY" and "Gas" not in name):
                entities.append(
                    RepsolLuzYGasSensor(
                        coordinator=coordinator,
                        name=f"Repsol {cups} {name}",
                        variable=var,
                        device_class=devc,
                        house_id=house_id,
                        contract_type=ctype,
                        contract_id=contract_id,
                        cups=cups,
                        contract_info=contract_info,
                        house_contract=house_contract,
                    )
                )

        # === SVA (si existen en house_contract) ===
        for sva in house_contract.get("sva", []) or []:
            entities.append(
                SVASensor(
                    coordinator=coordinator,
                    house_id=house_id,
                    name=sva.get("name"),
                    code=sva.get("code"),
                )
            )

        # === Batería virtual (solo electricidad) ===
        if ctype == "ELECTRICITY":
            vb = payload.get("virtual_battery_history")
            if vb:
                for sd in VB_SENSORS:
                    entities.append(
                        VirtualBatterySensor(
                            coordinator=coordinator,
                            name=f"Repsol {cups} {sd['name']}",
                            variable=sd["variable"],
                            device_class=sd["device_class"],
                            house_id=house_id,
                            contract_id=contract_id,
                        )
                    )

                # Último canje (si existe)
                last_red = max((vb.get("discounts", {}) or {}).get("data", []), key=lambda x: x.get("billingDate", ""), default=None)
                if last_red:
                    entities.append(
                        VirtualBatterySensor(
                            coordinator=coordinator,
                            name=f"Repsol {cups} Last Amount Redeemed",
                            variable="amount",
                            device_class=SensorDeviceClass.MONETARY,
                            house_id=house_id,
                            contract_id=contract_id,
                            coupon_data=last_red,
                        )
                    )
                    entities.append(
                        VirtualBatterySensor(
                            coordinator=coordinator,
                            name=f"Repsol {cups} Last kWh Redeemed",
                            variable="kWh",
                            device_class=SensorDeviceClass.ENERGY,
                            house_id=house_id,
                            contract_id=contract_id,
                            coupon_data=last_red,
                        )
                    )

    async_add_entities(entities, True)
    LOGGER.info("Added %s sensors", len(entities))


class RepsolLuzYGasSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Repsol Luz y Gas Sensor backed by coordinator data."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator,
        name: str,
        variable: str,
        device_class: Optional[SensorDeviceClass],
        house_id: str,
        contract_type: str,
        contract_id: str,
        cups: str,
        contract_info: Dict[str, Any],
        house_contract: Dict[str, Any],
    ):
        super().__init__(coordinator)
        self._attr_name = name
        self.variable = variable
        self._attr_device_class = device_class
        self.house_id = house_id
        self.contract_type = contract_type
        self.contract_id = contract_id
        self.cups = cups
        self.contract_info = contract_info or {}
        self.house_contract = house_contract or {}

    @property
    def unique_id(self) -> str:
        return f"{self.house_id}_{self.contract_id}_{self.variable}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.house_id}_{self.contract_id}")},
            name=f"{self.contract_type} - {self.cups}",
            manufacturer="Repsol Luz y Gas",
            model=self.contract_type,
            serial_number=str(self.contract_id),
            configuration_url="https://areacliente.repsol.es/productos-y-servicios",
        )

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        user_currency = self.hass.config.currency
        if self._attr_device_class == SensorDeviceClass.ENERGY:
            return "kWh"
        if self._attr_device_class == SensorDeviceClass.MONETARY:
            if self.variable in ("pricesEnergyAmount", "excedentsPrice"):
                return f"{user_currency}/kWh"
            return user_currency
        if self._attr_device_class == SensorDeviceClass.POWER:
            return "kW"
        return None

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        payload = data.get(self.contract_id) or {}

        # --- COSTES ---
        if self.variable in {"amount", "consumption", "totalDays", "amountVariable", "amountFixed", "averageAmount"}:
            return (payload.get("costs") or {}).get(self.variable)

        # --- FACTURAS (última) ---
        if self.variable in {"lastInvoiceAmount", "lastInvoicePaid"}:
            inv = payload.get("invoices")
            if isinstance(inv, list) and inv:
                obj = inv[0]
            elif isinstance(inv, dict):
                obj = inv
            else:
                obj = None
            if not obj:
                return None
            if self.variable == "lastInvoiceAmount":
                return obj.get("amount") or obj.get("totalAmount")
            return "Yes" if (obj.get("status") == "PAID") else "No"

        # --- SIGUIENTE FACTURA ---
        if self.variable in {"nextInvoiceAmount", "nextInvoiceVariableAmount", "nextInvoiceFixedAmount"}:
            nxt = payload.get("nextInvoice") or {}
            if self.variable == "nextInvoiceAmount":
                return nxt.get("amount")
            if self.variable == "nextInvoiceVariableAmount":
                return nxt.get("amountVariable")
            if self.variable == "nextInvoiceFixedAmount":
                return nxt.get("amountFixed")

        # --- CAMPOS DE CONTRATO / TARIFA (suelen venir en house_contract) ---
        if self.contract_type == "ELECTRICITY":
            if self.variable in {"status", "power", "fee"}:
                # status/power/fee pueden venir en house_contract o contract_info
                return self.house_contract.get(self.variable) or self.contract_info.get(self.variable)

            prices = (self.house_contract.get("prices") or self.contract_info.get("prices") or {})
            if self.variable == "pricesPowerPunta":
                return self._parse_price_list((prices.get("power") or []), 0)
            if self.variable == "pricesPowerValle":
                return self._parse_price_list((prices.get("power") or []), 1)
            if self.variable == "pricesEnergyAmount":
                return self._parse_price_list((prices.get("energy") or []), 0)

        if self.contract_type == "GAS":
            if self.variable in {"status", "fixedTerm", "variableTerm"}:
                energy_prices = (self.house_contract.get("prices") or {}).get("energy") or []
                if self.variable == "status":
                    return self.house_contract.get("status") or self.contract_info.get("status")
                if self.variable == "fixedTerm":
                    return self._extract_gas_price(energy_prices, fixed=True)
                if self.variable == "variableTerm":
                    return self._extract_gas_price(energy_prices, fixed=False)

        return None

    @staticmethod
    def _parse_price_list(prices: List[str], index: int) -> Any:
        """Parse strings like 'Punta: 0,1234 €/kWh' to numeric '0.1234'."""
        parsed: List[str] = []
        for p in prices:
            m = re.search(r"(\d+,\d+)", str(p))
            if m:
                parsed.append(m.group(1).replace(",", "."))
        return parsed[index] if index < len(parsed) else None

    @staticmethod
    def _extract_gas_price(prices: List[str], fixed: bool) -> Any:
        """Return price for fixed/variable gas term."""
        key = "Término Fijo" if fixed else "Término Variable"
        for p in prices:
            if key in str(p):
                m = re.search(r"(\d+,\d+)", str(p))
                if m:
                    return m.group(1).replace(",", ".")
        return None


class VirtualBatterySensor(CoordinatorEntity, SensorEntity):
    """Virtual Battery sensors."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator,
        name: str,
        variable: str,
        device_class: Optional[SensorDeviceClass],
        house_id: str,
        contract_id: str,
        coupon_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(coordinator)
        self._attr_name = name
        self.variable = variable
        self._attr_device_class = device_class
        self.house_id = house_id
        self.contract_id = contract_id
        self.coupon_data = coupon_data

    @property
    def unique_id(self) -> str:
        suffix = "_coupon" if self.coupon_data else ""
        return f"{self.house_id}_{self.contract_id}_{self.variable}_vb{suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"virtual_battery_{self.house_id}_{self.contract_id}")},
            name=f"Virtual Battery - {self.house_id}",
            manufacturer="Repsol Luz y Gas",
            model="Virtual Battery",
            serial_number=str(self.house_id),
            configuration_url="https://areacliente.repsol.es/productos-y-servicios",
        )

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        user_currency = self.hass.config.currency
        if self._attr_device_class == SensorDeviceClass.ENERGY:
            return "kWh"
        if self._attr_device_class == SensorDeviceClass.MONETARY:
            if self.variable == "excedentsPrice":
                return f"{user_currency}/kWh"
            return user_currency
        return None

    @property
    def native_value(self) -> Any:
        if self.coupon_data:
            return self.coupon_data.get(self.variable)

        data = (self.coordinator.data or {}).get(self.contract_id) or {}
        vb = data.get("virtual_battery_history") or {}
        discounts = vb.get("discounts") or {}
        excedents = vb.get("excedents") or {}

        if self.variable == "pendingAmount":
            c = next((c for c in (discounts.get("contracts") or []) if c.get("productCode") == self.contract_id), None)
            return c.get("pendingAmount") if c else None

        if self.variable == "kwhAvailable":
            c = next((c for c in (discounts.get("contracts") or []) if c.get("productCode") == self.contract_id), None)
            pending = c.get("pendingAmount") if c else 0
            conv = next((d.get("conversionPrice") for d in (excedents.get("data") or [])), 0)
            try:
                return round(float(pending) / float(conv), 2) if conv else None
            except Exception:
                return None

        if self.variable == "appliedAmount":
            return excedents.get("appliedAmount")

        if self.variable == "kwhRedeemed":
            conv = next((d.get("conversionPrice") for d in (excedents.get("data") or [])), 0)
            try:
                return round(float(excedents.get("appliedAmount", 0)) / float(conv), 2) if conv else None
            except Exception:
                return None

        if self.variable == "totalKWh":
            return round(float(excedents.get("totalkWh", 0)), 2)

        if self.variable == "excedentsPrice":
            return next((d.get("conversionPrice") for d in (excedents.get("data") or [])), None)

        return None


class SVASensor(CoordinatorEntity, SensorEntity):
    """Sensor para SVAs de la casa."""

    _attr_has_entity_name = False

    def __init__(self, coordinator, house_id: str, name: str, code: str):
        super().__init__(coordinator)
        self.house_id = house_id
        self._attr_name = name
        self.code = code

    @property
    def unique_id(self) -> str:
        return f"{self.house_id}_{self.code}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.house_id)},
            name=f"SVA - {self.house_id}",
            manufacturer="Repsol Luz y Gas",
            model="SVAs",
            serial_number=str(self.house_id),
            configuration_url="https://areacliente.repsol.es/productos-y-servicios",
        )

    @property
    def native_value(self) -> Any:
        return self.code