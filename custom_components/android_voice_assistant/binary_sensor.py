"""Binary sensor platform for Android Voice Assistant."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_APP_VERSION,
    ATTR_BATTERY_CHARGING,
    ATTR_DEVICE_MODEL,
    ATTR_PHASE,
    DOMAIN,
    SIGNAL_DEVICE_UPDATE,
    VoicePhase,
)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []
    for device in coordinator.devices.values():
        entities.extend(
            [
                ConnectedSensor(device),
                ListeningSensor(device),
                ChargingSensor(device),
                ErrorSensor(device),
            ]
        )

    async_add_entities(entities, True)


class _BaseBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, device, key: str, name: str) -> None:
        self._device = device
        self._attr_unique_id = f"{device.device_id}_{key}"
        self._attr_name = name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.device_id)},
            name=self._device.name,
            manufacturer="Android Voice Assistant",
            model=self._device.state.get(ATTR_DEVICE_MODEL, "Android"),
            sw_version=self._device.state.get(ATTR_APP_VERSION, "unknown"),
        )

    @property
    def available(self) -> bool:
        return True

    async def async_added_to_hass(self) -> None:
        signal = SIGNAL_DEVICE_UPDATE.format(device_id=self._device.device_id)
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class ConnectedSensor(_BaseBinarySensor):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = "diagnostic"

    def __init__(self, device) -> None:
        super().__init__(device, "connected", "Verbunden")

    @property
    def is_on(self) -> bool:
        return self._device.is_connected


class ListeningSensor(_BaseBinarySensor):
    _attr_icon = "mdi:ear-hearing"

    def __init__(self, device) -> None:
        super().__init__(device, "listening", "Hört zu")

    @property
    def is_on(self) -> bool:
        return self._device.state.get(ATTR_PHASE) in (
            VoicePhase.WAITING_FOR_COMMAND,
            VoicePhase.LISTENING,
        )


class ChargingSensor(_BaseBinarySensor):
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _attr_entity_category = "diagnostic"

    def __init__(self, device) -> None:
        super().__init__(device, "charging", "Lädt")

    @property
    def is_on(self) -> bool:
        return bool(self._device.state.get(ATTR_BATTERY_CHARGING, False))


class ErrorSensor(_BaseBinarySensor):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = "diagnostic"

    def __init__(self, device) -> None:
        super().__init__(device, "has_error", "Fehler")

    @property
    def is_on(self) -> bool:
        return self._device.state.get(ATTR_PHASE) == VoicePhase.ERROR
