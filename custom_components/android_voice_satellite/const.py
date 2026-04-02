from __future__ import annotations

DOMAIN = "android_voice_satellite"
CONF_DEVICE_NAME = "device_name"
CONF_DEVICE_ID = "device_id"
CONF_API_KEY = "api_key"
CONF_CLIENT_ID = "client_id"
WS_PATH = "/api/android_voice_satellite/ws"
REGISTER_PATH = "/api/android_voice_satellite/register"
PAIR_PATH = "/api/android_voice_satellite/pair"
PAIRING_PAGE_PATH = "/api/android_voice_satellite/pairing_page/{pair_token}"
PAIRING_TTL_SECONDS = 300

PHASE_IDLE = 1
PHASE_WAITING_FOR_COMMAND = 2
PHASE_LISTENING = 3
PHASE_THINKING = 4
PHASE_REPLYING = 5
PHASE_NOT_READY = 10
PHASE_ERROR = 11
PHASE_MUTED = 12

PHASE_NAMES = {
    PHASE_IDLE: "Idle",
    PHASE_WAITING_FOR_COMMAND: "Waiting for command",
    PHASE_LISTENING: "Listening",
    PHASE_THINKING: "Thinking",
    PHASE_REPLYING: "Replying",
    PHASE_NOT_READY: "Not ready",
    PHASE_ERROR: "Error",
    PHASE_MUTED: "Muted",
}

WAKE_WORDS = [
    {"id": "okay_nabu", "name": "Okay Nabu"},
    {"id": "hey_jarvis", "name": "Hey Jarvis"},
    {"id": "hey_mycroft", "name": "Hey Mycroft"},
]

ALARM_ACTIONS = ["Play sound", "Send event", "Sound and event"]
VAD_SENSITIVITIES = ["Relaxed", "Normal", "Aggressive"]

AUDIO_SAMPLE_RATE = 16000
AUDIO_SAMPLE_WIDTH = 2
AUDIO_CHANNELS = 1

SIGNAL_DEVICE_STATE = f"{DOMAIN}_device_state"
SIGNAL_DEVICE_CONNECTED = f"{DOMAIN}_device_connected"
SIGNAL_DEVICE_DISCONNECTED = f"{DOMAIN}_device_disconnected"
