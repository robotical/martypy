import requests
import json
import time
from urllib.parse import quote
# from pydub import AudioSegment
# from pydub.playback import play
from io import BytesIO
# from .Exceptions import (MartyConnectException,
#                          MartyCommandException)
import io


# Voice IDs
VOICES = {
    "ALTO_ID": "ALTO",
    "KITTEN_ID": "KITTEN",
    "GIANT_ID": "GIANT",
    "TENOR_ID": "TENOR",
    "ALIEN_ID": "ALIEN",
    "THUNDER_ID": "THUNDER",
    "STONE_ID": "STONE",
    "RUMBLE_ID": "RUMBLE",
    "ECHO_ID": "ECHO",
    "DRIFT_ID": "DRIFT",
    "BREEZE_ID": "BREEZE",
    "WAVE_ID": "WAVE",
    "BLAZE_ID": "BLAZE",
    "BOLT_ID": "BOLT",
    "STARLIGHT_ID": "STARLIGHT",
    "MIST_ID": "MIST",
    "WHIRLWIND_ID": "WHIRLWIND",
    "DAWN_ID": "DAWN",
    "CRYSTAL_ID": "CRYSTAL",
    "LULLABY_ID": "LULLABY",
    "AURORA_ID": "AURORA",
    "RADIANCE_ID": "RADIANCE",
    "FLASH_ID": "FLASH"
}

# language IDs
LANGUAGES = {
    "ARABIC_ID": "ar",
    "CHINESE_ID": "zh-cn",
    "DANISH_ID": "da",
    "DUTCH_ID": "nl",
    "ENGLISH_ID": "en",
    "FRENCH_ID": "fr",
    "GERMAN_ID": "de",
    "HINDI_ID": "hi",
    "ICELANDIC_ID": "is",
    "ITALIAN_ID": "it",
    "JAPANESE_ID": "ja",
    "KOREAN_ID": "ko",
    "NORWEGIAN_ID": "nb",
    "POLISH_ID": "pl",
    "PORTUGUESE_BR_ID": "pt-br",
    "PORTUGUESE_ID": "pt",
    "ROMANIAN_ID": "ro",
    "RUSSIAN_ID": "ru",
    "SPANISH_ID": "es",
    "SPANISH_419_ID": "es-419",
    "SWEDISH_ID": "sv",
    "TURKISH_ID": "tr",
    "WELSH_ID": "cy"
}

VOICE_INFO =  {
    VOICES['ALTO_ID']: {"name": {"id": "text2speech.female", "default": "Alto", "description": "Name for a female voice."},
                    "gender": "female", "playbackRate": 1, "pitch": 1},
    VOICES['KITTEN_ID']: {"name": {"id": "text2speech.kitten", "default": "kitten", "description": "A baby cat."},
                    "gender": "female", "playbackRate": 1.41, "pitch": 1.5},
    VOICES['GIANT_ID']: {"name": {"id": "text2speech.giant", "default": "giant", "description": "A giant."},
                    "gender": "male", "playbackRate": 0.79, "pitch": 0.5},
    VOICES['TENOR_ID']: {"name": {"id": "text2speech.tenor", "default": "tenor", "description": "A tenor."},
                    "gender": "female", "playbackRate": 1.41, "pitch": 0.5},
    VOICES['ALIEN_ID']: {"name": {"id": "text2speech.alien", "default": "alien", "description": "An alien."},
                    "gender": "female", "playbackRate": 0.79, "pitch": 1.5},
    VOICES['THUNDER_ID']: {"name": {"id": "text2speech.thunder", "default": "Thunder", "description": "Male voice with low pitch and playback rate."},
                    "gender": "male", "playbackRate": 0.7, "pitch": 0.7},
    VOICES['STONE_ID']: {"name": {"id": "text2speech.stone", "default": "Stone", "description": "Male voice with low pitch."},
                    "gender": "male", "playbackRate": 1, "pitch": 0.7},
    VOICES['RUMBLE_ID']: {"name": {"id": "text2speech.rumble", "default": "Rumble", "description": "Male voice with high playback rate and low pitch."},
                    "gender": "male", "playbackRate": 1.3, "pitch": 0.7},
    VOICES['ECHO_ID']: {"name": {"id": "text2speech.echo", "default": "Echo", "description": "Male voice with standard pitch and low playback rate."},
                "gender": "male", "playbackRate": 0.7, "pitch": 1},
    VOICES['DRIFT_ID']: {"name": {"id": "text2speech.drift", "default": "Drift", "description": "Standard male voice."},
                    "gender": "male", "playbackRate": 1, "pitch": 1},
    VOICES['BREEZE_ID']: {"name": {"id": "text2speech.breeze", "default": "Breeze", "description": "Male voice with standard pitch and high playback rate."},
                    "gender": "male", "playbackRate": 1.3, "pitch": 1},
    VOICES['WAVE_ID']: {"name": {"id": "text2speech.wave", "default": "Wave", "description": "Male voice with high pitch and low playback rate."},
                "gender": "male", "playbackRate": 0.7, "pitch": 1.3},
    VOICES['BLAZE_ID']: {"name": {"id": "text2speech.blaze", "default": "Blaze", "description": "High-pitched male voice."},
                    "gender": "male", "playbackRate": 1, "pitch": 1.3},
    VOICES['BOLT_ID']: {"name": {"id": "text2speech.bolt", "default": "Bolt", "description": "Male voice with high pitch and playback rate."},
                "gender": "male", "playbackRate": 1.3, "pitch": 1.3},
    VOICES['STARLIGHT_ID']: {"name": {"id": "text2speech.starlight", "default": "Starlight", "description": "Female voice with low pitch and playback rate."},
                        "gender": "female", "playbackRate": 0.7, "pitch": 0.7},
    VOICES['MIST_ID']: {"name": {"id": "text2speech.mist", "default": "Mist", "description": "Female voice with low pitch."},
                "gender": "female", "playbackRate": 1, "pitch": 0.7},
    VOICES['WHIRLWIND_ID']: {"name": {"id": "text2speech.whirlwind", "default": "Whirlwind", "description": "Female voice with high playback rate and low pitch."},
                        "gender": "female", "playbackRate": 1.3, "pitch": 0.7},
    VOICES['DAWN_ID']: {"name": {"id": "text2speech.dawn", "default": "Dawn", "description": "Female voice with standard pitch and low playback rate."},
                "gender": "female", "playbackRate": 0.7, "pitch": 1},
    VOICES['CRYSTAL_ID']: {"name": {"id": "text2speech.crystal", "default": "Crystal", "description": "Standard female voice."},
                    "gender": "female", "playbackRate": 1, "pitch": 1},
    VOICES['LULLABY_ID']: {"name": {"id": "text2speech.lullaby", "default": "Lullaby", "description": "Female voice with standard pitch and high playback rate."},
                    "gender": "female", "playbackRate": 1.3, "pitch": 1},
    VOICES['AURORA_ID']: {"name": {"id": "text2speech.aurora", "default": "Aurora", "description": "Female voice with high pitch and low playback rate."},
                    "gender": "female", "playbackRate": 0.7, "pitch": 1.3},
    VOICES['RADIANCE_ID']: {"name": {"id": "text2speech.radiance", "default": "Radiance", "description": "High-pitched female voice."},
                    "gender": "female", "playbackRate": 1, "pitch": 1.3},
    VOICES['FLASH_ID']: {"name": {"id": "text2speech.flash", "default": "Flash", "description": "Female voice with high pitch and playback rate."},
                    "gender": "female", "playbackRate": 1.3, "pitch": 1.3}
    }
LANGUAGE_INFO = {
      LANGUAGES['ARABIC_ID']: {
        "name": "Arabic",
        "locales": ["ar"],
        "speechSynthLocale": "arb",
        "singleGender": True,
      },
      LANGUAGES['CHINESE_ID']: {
        "name": "Chinese (Mandarin)",
        "locales": ["zh-cn", "zh-tw"],
        "speechSynthLocale": "cmn-CN",
        "singleGender": True,
      },
      LANGUAGES['DANISH_ID']: {
        "name": "Danish",
        "locales": ["da"],
        "speechSynthLocale": "da-DK",
        "singleGender": False
      },
      LANGUAGES['DUTCH_ID']: {
        "name": "Dutch",
        "locales": ["nl"],
        "speechSynthLocale": "nl-NL",
        "singleGender": False
      },
      LANGUAGES['ENGLISH_ID']: {
        "name": "English",
        "locales": ["en"],
        "speechSynthLocale": "en-US",
        "singleGender": False
      },
      LANGUAGES['FRENCH_ID']: {
        "name": "French",
        "locales": ["fr"],
        "speechSynthLocale": "fr-FR",
        "singleGender": False
      },
      LANGUAGES['GERMAN_ID']: {
        "name": "German",
        "locales": ["de"],
        "speechSynthLocale": "de-DE",
        "singleGender": False
      },
      LANGUAGES['HINDI_ID']: {
        "name": "Hindi",
        "locales": ["hi"],
        "speechSynthLocale": "hi-IN",
        "singleGender": True,
      },
      LANGUAGES['ICELANDIC_ID']: {
        "name": "Icelandic",
        "locales": ["is"],
        "speechSynthLocale": "is-IS",
        "singleGender": False
      },
      LANGUAGES['ITALIAN_ID']: {
        "name": "Italian",
        "locales": ["it"],
        "speechSynthLocale": "it-IT",
        "singleGender": False
      },
      LANGUAGES['JAPANESE_ID']: {
        "name": "Japanese",
        "locales": ["ja", "ja-hira"],
        "speechSynthLocale": "ja-JP",
        "singleGender": False
      },
      LANGUAGES['KOREAN_ID']: {
        "name": "Korean",
        "locales": ["ko"],
        "speechSynthLocale": "ko-KR",
        "singleGender": True,
      },
      LANGUAGES['NORWEGIAN_ID']: {
        "name": "Norwegian",
        "locales": ["nb", "nn"],
        "speechSynthLocale": "nb-NO",
        "singleGender": True,
      },
      LANGUAGES['POLISH_ID']: {
        "name": "Polish",
        "locales": ["pl"],
        "speechSynthLocale": "pl-PL",
        "singleGender": False
      },
      LANGUAGES['PORTUGUESE_BR_ID']: {
        "name": "Portuguese (Brazilian)",
        "locales": ["pt-br"],
        "speechSynthLocale": "pt-BR",
        "singleGender": False
      },
      LANGUAGES['PORTUGUESE_ID']: {
        "name": "Portuguese (European)",
        "locales": ["pt"],
        "speechSynthLocale": "pt-PT",
        "singleGender": False
      },
      LANGUAGES['ROMANIAN_ID']: {
        "name": "Romanian",
        "locales": ["ro"],
        "speechSynthLocale": "ro-RO",
        "singleGender": True,
      },
      LANGUAGES['RUSSIAN_ID']: {
        "name": "Russian",
        "locales": ["ru"],
        "speechSynthLocale": "ru-RU",
        "singleGender": False
      },
      LANGUAGES['SPANISH_ID']: {
        "name": "Spanish (European)",
        "locales": ["es"],
        "speechSynthLocale": "es-ES",
        "singleGender": False
      },
      LANGUAGES['SPANISH_419_ID']: {
        "name": "Spanish (Latin American)",
        "locales": ["es-419"],
        "speechSynthLocale": "es-US",
        "singleGender": False
      },
      LANGUAGES['SWEDISH_ID']: {
        "name": "Swedish",
        "locales": ["sv"],
        "speechSynthLocale": "sv-SE",
        "singleGender": True,
      },
      LANGUAGES['TURKISH_ID']: {
        "name": "Turkish",
        "locales": ["tr"],
        "speechSynthLocale": "tr-TR",
        "singleGender": True,
      },
      LANGUAGES['WELSH_ID']: {
        "name": "Welsh",
        "locales": ["cy"],
        "speechSynthLocale": "cy-GB",
        "singleGender": True,
      },
    }

class Text2Speech:
    def __init__(self):
        self.SERVER_HOST = "https://synthesis-service.scratch.mit.edu"
        self.voiceSpeed = 1

    def speak(self, words, voice, language="en"):
        voice_id = voice.upper()
        # if voice_id not in VOICES.values():
        #     raise MartyCommandException(f"Voice must be one of {set(VOICES.values())}, not {voice_id}")
        # if language not in LANGUAGES.values():
        #     raise MartyCommandException(f"Language must be one of {set(LANGUAGES.values())}, not {language}")

        locale = self._get_speech_synth_locale(language)
        gender = VOICE_INFO[voice_id]["gender"]
        playback_rate = VOICE_INFO[voice_id]["playbackRate"] * self.voiceSpeed
        pitch = VOICE_INFO[voice_id]["pitch"]
        
        # Special case for voices where the synthesis service only provides a
        # single gender voice. In that case, always request the female voice,
        # and set special playback rates for the tenor and giant voices.
        if LANGUAGE_INFO[language]['singleGender']: 
            gender = "female"

        if voice_id == VOICES['KITTEN_ID']:
            words = " ".join(["meow" for word in words.split(" ")])
            locale = LANGUAGE_INFO["en"]["speechSynthLocale"]
        
        path = f"{self.SERVER_HOST}/synth"
        path += f"?locale={locale}"
        path += f"&gender={gender}"
        path += f"&text={quote(words[:128])}"    
        # perform http request to get audio file
        response = requests.get(path)
        response.raise_for_status()

        # Return the MP3 bytes as-is. Previously this method appended the
        # first bytes of the MP3 to the end to simulate a short silence, but
        # that caused the start of the phrase to repeat briefly.
        return response.content

    def _get_speech_synth_locale(self, language):
        if language in LANGUAGE_INFO:
            return LANGUAGE_INFO[language]["speechSynthLocale"]
        else:
            return "en"
