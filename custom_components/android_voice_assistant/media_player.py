from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import ATTR_APP_VERSION, ATTR_DEVICE_MODEL, DOMAIN, SIGNAL_DEVICE_UPDATE, SIGNAL_CONFIG_CHANGED

def device_info(device):
    return DeviceInfo(identifiers={(DOMAIN, device.device_id)}, name=device.name, manufacturer="Android Voice Assistant", model=device.state.get(ATTR_DEVICE_MODEL, "Android"), sw_version=device.state.get(ATTR_APP_VERSION, "unknown"))

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerDeviceClass, MediaPlayerEntityFeature, MediaPlayerState
from .const import ATTR_PHASE, ATTR_VOLUME, VoicePhase
async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AndroidMediaPlayer(d) for d in coordinator.devices.values()], True)
class AndroidMediaPlayer(MediaPlayerEntity):
    _attr_has_entity_name = True; _attr_name = 'Lautsprecher'; _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_supported_features = MediaPlayerEntityFeature.VOLUME_SET | MediaPlayerEntityFeature.STOP
    def __init__(self, device): self._device=device; self._attr_unique_id=f"{device.device_id}_media_player"
    @property
    def state(self): return MediaPlayerState.PLAYING if self._device.state.get(ATTR_PHASE) == VoicePhase.REPLYING else MediaPlayerState.IDLE
    @property
    def volume_level(self): return self._device.state.get(ATTR_VOLUME, 0.5)
    @property
    def available(self): return self._device.is_connected
    @property
    def device_info(self): return device_info(self._device)
    async def async_set_volume_level(self, volume: float): self._device.update_config({'volume': volume}); self._device.update_state({ATTR_VOLUME: volume})
