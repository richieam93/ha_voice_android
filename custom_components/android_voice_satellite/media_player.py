from __future__ import annotations
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState, MediaType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([AndroidMediaPlayer(hass.data[DOMAIN][entry.entry_id]["connection"])])
class AndroidMediaPlayer(MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_media_content_type = MediaType.MUSIC
    _attr_supported_features = MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.STOP | MediaPlayerEntityFeature.PAUSE | MediaPlayerEntityFeature.VOLUME_SET | MediaPlayerEntityFeature.VOLUME_STEP | MediaPlayerEntityFeature.PLAY_MEDIA
    def __init__(self, c):
        self._conn = c; self._state = MediaPlayerState.IDLE; self._media_url = None
        self._attr_unique_id = f"{c.device_id}_media_player"; self._attr_device_info = {"identifiers": {(DOMAIN, c.device_id)}}
    @property
    def state(self): return MediaPlayerState.OFF if not self._conn.is_connected else self._state
    @property
    def volume_level(self): return self._conn.volume
    @property
    def is_volume_muted(self): return self._conn.muted
    async def async_set_volume_level(self, volume): await self._conn.cmd_set_volume(volume)
    async def async_volume_up(self): await self.async_set_volume_level(min(1.0, self._conn.volume + 0.05))
    async def async_volume_down(self): await self.async_set_volume_level(max(0.0, self._conn.volume - 0.05))
    async def async_media_play(self):
        if self._media_url: await self._conn.cmd_play_url(self._media_url); self._state = MediaPlayerState.PLAYING
    async def async_media_stop(self): await self._conn.cmd_stop_playback(); self._state = MediaPlayerState.IDLE
    async def async_media_pause(self): await self._conn.send_json({"type": "pause_playback"}); self._state = MediaPlayerState.PAUSED
    async def async_play_media(self, media_type, media_id, **kwargs): self._media_url = media_id; await self._conn.cmd_play_url(media_id, announcement=bool(kwargs.get('announce', False))); self._state = MediaPlayerState.PLAYING
