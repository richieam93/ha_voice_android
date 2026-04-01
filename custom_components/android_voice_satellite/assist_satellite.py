from __future__ import annotations
import asyncio, logging
from homeassistant.components.assist_satellite import AssistSatelliteEntity, AssistSatelliteEntityDescription, AssistSatelliteConfiguration, AssistSatelliteWakeWord, AssistSatelliteAnnouncement
from homeassistant.components.assist_pipeline import PipelineEvent, PipelineStage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .connection import DeviceConnection
from .const import DOMAIN, WAKE_WORDS, PHASE_IDLE, PHASE_LISTENING, PHASE_THINKING, PHASE_REPLYING, PHASE_WAITING_FOR_COMMAND, PHASE_ERROR, PHASE_NOT_READY
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([AndroidAssistSatellite(hass.data[DOMAIN][entry.entry_id]["connection"])])

class AndroidAssistSatellite(AssistSatelliteEntity):
    entity_description = AssistSatelliteEntityDescription(key="assist_satellite", name=None)
    _attr_has_entity_name = True
    _attr_name = None
    def __init__(self, connection: DeviceConnection) -> None:
        self._conn = connection
        self._attr_unique_id = f"{connection.device_id}_assist_satellite"
        self._attr_device_info = {"identifiers": {(DOMAIN, connection.device_id)}, "name": connection.device_name, "manufacturer": "Android Voice Satellite", "model": connection.device_model or "Android Device", "sw_version": connection.app_version or "unknown"}
    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, f"{DOMAIN}_wake_word_{self._conn.device_id}", self._on_wake_word_detected))
    @callback
    def async_get_configuration(self) -> AssistSatelliteConfiguration:
        return AssistSatelliteConfiguration(available_wake_words=[AssistSatelliteWakeWord(id=w['id'], wake_word=w['name']) for w in WAKE_WORDS], active_wake_words=list(self._conn.active_wake_word_ids), max_active_wake_words=2)
    async def async_set_configuration(self, config: AssistSatelliteConfiguration) -> None:
        self._conn.active_wake_word_ids = list(config.active_wake_words)
        await self._conn.cmd_set_config({"active_wake_word_ids": self._conn.active_wake_word_ids})
        self.async_write_ha_state()
    async def async_announce(self, announcement: AssistSatelliteAnnouncement) -> None:
        if announcement.media_id:
            await self._conn.cmd_play_url(announcement.media_id, announcement=True)
            try:
                await asyncio.wait_for(self._conn.announcement_done_event.wait(), timeout=120)
            except asyncio.TimeoutError:
                _LOGGER.warning("Announcement timeout on %s", self._conn.device_name)
    @callback
    def on_pipeline_event(self, event: PipelineEvent) -> None:
        event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
        phase_map = {"run-start": PHASE_WAITING_FOR_COMMAND, "stt-start": PHASE_LISTENING, "stt-vad-start": PHASE_LISTENING, "stt-vad-end": PHASE_THINKING, "stt-end": PHASE_THINKING, "intent-start": PHASE_THINKING, "intent-end": PHASE_THINKING, "tts-start": PHASE_REPLYING, "tts-end": PHASE_REPLYING, "run-end": PHASE_IDLE, "error": PHASE_ERROR}
        if event_type in phase_map:
            self._conn.set_phase(phase_map[event_type])
        asyncio.create_task(self._conn.cmd_pipeline_event(event_type, event.data or {}))
    @callback
    def _on_wake_word_detected(self, wake_word_id: str, wake_word_phrase: str) -> None:
        if not self._conn.voice_enabled:
            return
        asyncio.create_task(self._conn.cmd_start_mic())
        self.async_accept_pipeline_from_satellite(audio_stream=self._conn.audio_stream(), start_stage=PipelineStage.STT, end_stage=PipelineStage.TTS, wake_word_phrase=wake_word_phrase)
