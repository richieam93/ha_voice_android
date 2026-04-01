"""Constants for Android Voice Assistant integration."""
from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Final

DOMAIN: Final = "android_voice_assistant"
CONF_DEVICE_ID: Final = "device_id"
CONF_DEVICE_NAME: Final = "device_name"
CONF_DEVICE_MODEL: Final = "device_model"
CONF_ANDROID_VERSION: Final = "android_version"
CONF_APP_VERSION: Final = "app_version"

class VoicePhase(IntEnum):
    IDLE = 1
    WAITING_FOR_COMMAND = 2
    LISTENING = 3
    THINKING = 4
    REPLYING = 5
    NOT_READY = 10
    ERROR = 11
    MUTED = 12

PHASE_NAMES: Final = {
    VoicePhase.IDLE: "Bereit",
    VoicePhase.WAITING_FOR_COMMAND: "Warte auf Befehl",
    VoicePhase.LISTENING: "Höre zu",
    VoicePhase.THINKING: "Verarbeite",
    VoicePhase.REPLYING: "Antworte",
    VoicePhase.NOT_READY: "Nicht bereit",
    VoicePhase.ERROR: "Fehler",
    VoicePhase.MUTED: "Stumm",
}

class WakeWordModel(StrEnum):
    HEY_JARVIS = "hey_jarvis"
    OKAY_NABU = "okay_nabu"
    HEY_MYCROFT = "hey_mycroft"
    COMPUTER = "computer"
    ALEXA = "alexa"
    HEY_SIRI = "hey_siri"
    KENOBI = "kenobi"
    CUSTOM = "custom"

WAKE_WORD_LABELS: Final = {
    WakeWordModel.HEY_JARVIS: "Hey Jarvis",
    WakeWordModel.OKAY_NABU: "Okay Nabu",
    WakeWordModel.HEY_MYCROFT: "Hey Mycroft",
    WakeWordModel.COMPUTER: "Computer",
    WakeWordModel.ALEXA: "Alexa",
    WakeWordModel.HEY_SIRI: "Hey Siri",
    WakeWordModel.KENOBI: "Kenobi",
    WakeWordModel.CUSTOM: "Benutzerdefiniert",
}

class WakeWordEngine(StrEnum):
    PORCUPINE = "porcupine"
    TFLITE = "tflite"
    VOSK = "vosk"

class TTSEngine(StrEnum):
    HOME_ASSISTANT = "ha_tts"
    GOOGLE = "google"
    PIPER = "piper"
    ANDROID_LOCAL = "android_local"

class STTEngine(StrEnum):
    HOME_ASSISTANT = "ha_stt"
    WHISPER = "whisper"
    GOOGLE = "google"
    ANDROID_LOCAL = "android_local"

class AlarmAction(StrEnum):
    PLAY_SOUND = "play_sound"
    SEND_EVENT = "send_event"
    SOUND_AND_EVENT = "sound_and_event"
    TTS_ANNOUNCEMENT = "tts_announcement"
    PUSH_NOTIFICATION = "push_notification"

class UITheme(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"
    AMOLED = "amoled"

DEFAULT_VOLUME: Final = 0.5
DEFAULT_VOLUME_MIN: Final = 0.0
DEFAULT_VOLUME_MAX: Final = 1.0
DEFAULT_VOLUME_STEP: Final = 0.05
DEFAULT_MIC_GAIN: Final = 1.0
DEFAULT_NOISE_SUPPRESSION: Final = 0
DEFAULT_AUTO_GAIN: Final = 0
DEFAULT_VAD_SENSITIVITY: Final = 0.5
DEFAULT_WAKE_WORD_SENSITIVITY: Final = 0.8
DEFAULT_SILENCE_TIMEOUT: Final = 2.0
DEFAULT_MAX_LISTEN_TIME: Final = 30
DEFAULT_TIMER_RING_DURATION: Final = 900
DEFAULT_TIMER_SOUND: Final = "default"
DEFAULT_RECONNECT_INTERVAL: Final = 5
DEFAULT_PING_INTERVAL: Final = 30

EVENT_WAKE_WORD_DETECTED: Final = f"{DOMAIN}_wake_word_detected"
EVENT_STT_RESULT: Final = f"{DOMAIN}_stt_result"
EVENT_TTS_URI: Final = f"{DOMAIN}_tts_uri"
EVENT_INTENT_RESULT: Final = f"{DOMAIN}_intent_result"
EVENT_PHASE_CHANGED: Final = f"{DOMAIN}_phase_changed"
EVENT_TIMER_STARTED: Final = f"{DOMAIN}_timer_started"
EVENT_TIMER_FINISHED: Final = f"{DOMAIN}_timer_finished"
EVENT_TIMER_CANCELLED: Final = f"{DOMAIN}_timer_cancelled"
EVENT_ALARM_RINGING: Final = f"{DOMAIN}_alarm_ringing"
EVENT_ERROR: Final = f"{DOMAIN}_error"
EVENT_DEVICE_CONNECTED: Final = f"{DOMAIN}_device_connected"
EVENT_DEVICE_DISCONNECTED: Final = f"{DOMAIN}_device_disconnected"
EVENT_BATTERY_LOW: Final = f"{DOMAIN}_battery_low"

WS_TYPE_REGISTER: Final = f"{DOMAIN}/register"
WS_TYPE_UPDATE_STATE: Final = f"{DOMAIN}/update_state"
WS_TYPE_GET_CONFIG: Final = f"{DOMAIN}/get_config"
WS_TYPE_SET_CONFIG: Final = f"{DOMAIN}/set_config"
WS_TYPE_START_VA: Final = f"{DOMAIN}/start_va"
WS_TYPE_STOP_VA: Final = f"{DOMAIN}/stop_va"
WS_TYPE_SEND_AUDIO: Final = f"{DOMAIN}/send_audio"
WS_TYPE_PLAY_SOUND: Final = f"{DOMAIN}/play_sound"
WS_TYPE_PLAY_TTS: Final = f"{DOMAIN}/play_tts"
WS_TYPE_SET_VOLUME: Final = f"{DOMAIN}/set_volume"
WS_TYPE_TIMER_ACTION: Final = f"{DOMAIN}/timer_action"

ATTR_PHASE: Final = "phase"
ATTR_PHASE_NAME: Final = "phase_name"
ATTR_LAST_WAKE_WORD: Final = "last_wake_word"
ATTR_LAST_STT_TEXT: Final = "last_stt_text"
ATTR_LAST_TTS_TEXT: Final = "last_tts_text"
ATTR_LAST_INTENT: Final = "last_intent"
ATTR_LAST_ERROR: Final = "last_error"
ATTR_VOLUME: Final = "volume"
ATTR_IS_MUTED: Final = "is_muted"
ATTR_BATTERY_LEVEL: Final = "battery_level"
ATTR_BATTERY_CHARGING: Final = "battery_charging"
ATTR_WIFI_SIGNAL: Final = "wifi_signal"
ATTR_ACTIVE_TIMERS: Final = "active_timers"
ATTR_UPTIME: Final = "uptime"
ATTR_ANDROID_VERSION: Final = "android_version"
ATTR_APP_VERSION: Final = "app_version"
ATTR_DEVICE_MODEL: Final = "device_model"
ATTR_WAKE_WORD_ENGINE: Final = "wake_word_engine"
ATTR_WAKE_WORD_MODEL: Final = "wake_word_model"
ATTR_PIPELINE_ID: Final = "pipeline_id"
ATTR_MIC_GAIN: Final = "mic_gain"

PLATFORMS: Final = [
    "sensor",
    "binary_sensor",
    "switch",
    "select",
    "number",
    "button",
    "media_player",
    "text",
]

SIGNAL_DEVICE_UPDATE: Final = f"{DOMAIN}_device_update_{{device_id}}"
SIGNAL_CONFIG_CHANGED: Final = f"{DOMAIN}_config_changed_{{device_id}}"
STORAGE_KEY: Final = DOMAIN
STORAGE_VERSION: Final = 1
