import requests
import locale
import math
import re
from pydub import AudioSegment
from io import BytesIO


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
                    "gender": "male", "playbackRate": 0.7, "pitch": 0.5},
    VOICES['TENOR_ID']: {"name": {"id": "text2speech.tenor", "default": "tenor", "description": "A tenor."},
                    "gender": "male", "playbackRate": 1, "pitch": 0.5},
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
        self.SERVER_HOST = "https://appv2-analytics-server.robotical.io"
        self.voiceSpeed = 1
        self.duration_ms = 0

    @staticmethod
    def normalise_voice(voice):
        aliases = {"FEMALE": "ALTO", "MALE": "TENOR", "SQUEAK": "KITTEN", "CHIPMUNK": "KITTEN"}
        voice_id = str(voice).upper()
        try:
            index = float(voice_id)
            if math.isfinite(index):
                menu = ("TENOR", "ALTO", "KITTEN", "ALIEN", "GIANT", "BOLT", "STARLIGHT", "WHIRLWIND")
                voice_id = menu[(int(index) - 1) % len(menu)]
        except ValueError:
            pass
        voice_id = aliases.get(voice_id, voice_id)
        if voice_id not in VOICE_INFO:
            raise ValueError("Unknown speech voice: {}".format(voice))
        return voice_id

    @staticmethod
    def validate_speed(speed):
        value = float(speed)
        if not math.isfinite(value) or not 0.1 <= value <= 2:
            raise ValueError("Speech speed must be between 0.1 and 2")
        return value

    @staticmethod
    def language_code(language):
        value = str(language).strip().lower().replace("_", "-")
        for code, info in LANGUAGE_INFO.items():
            if value in (code, info["name"].lower(), info["speechSynthLocale"].lower()) or value in info["locales"]:
                return code
        # Translate supports more languages than speech synthesis.
        if re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,4})?", value):
            return value
        raise ValueError("Unknown language: {}. Use a language code such as 'en'.".format(language))

    def speak(self, words, voice="alto", language="en", speed=None):
        voice_id = self.normalise_voice(voice)
        language = self.language_code(language)
        if language not in LANGUAGE_INFO:
            raise ValueError("Unsupported speech language: {}".format(language))
        locale_code = self._get_speech_synth_locale(language)
        gender = VOICE_INFO[voice_id]["gender"]
        voice_speed = self.validate_speed(self.voiceSpeed if speed is None else speed)
        playback_rate = VOICE_INFO[voice_id]["playbackRate"] * voice_speed
        
        # Special case for voices where the synthesis service only provides a
        # single gender voice. In that case, always request the female voice,
        # and set special playback rates for the tenor and giant voices.
        if LANGUAGE_INFO[language]['singleGender']: 
            gender = "female"
            if voice_id == "TENOR":
                playback_rate = 0.89 * voice_speed
            elif voice_id == "GIANT":
                playback_rate = 0.79 * voice_speed

        if voice_id == VOICES['KITTEN_ID']:
            words = " ".join("meow" for word in str(words).split())
            locale_code = LANGUAGE_INFO["en"]["speechSynthLocale"]
        
        response = requests.get(self.SERVER_HOST + "/synth", params={
            "locale": locale_code, "gender": gender, "text": str(words)[:128]
        }, timeout=10)
        response.raise_for_status()
        audio = AudioSegment.from_file(BytesIO(response.content), format="mp3")
        if playback_rate != 1:
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * playback_rate)
            }).set_frame_rate(audio.frame_rate)
        self.duration_ms = len(audio)
        if playback_rate == 1:
            return response.content
        return audio.export(BytesIO(), format="mp3").getvalue()

    def translate(self, words, language):
        """Translate text using the same online service as Blocks. Requires internet."""
        words = str(words)
        if not words or words.isdigit():
            return words
        response = requests.get(self.SERVER_HOST + "/translate", params={
            "language": self.language_code(language), "text": words
        }, timeout=10)
        response.raise_for_status()
        result = response.json().get("result")
        if not isinstance(result, str):
            raise ValueError("Translation service returned an invalid result")
        return result

    @staticmethod
    def get_language():
        """Return the computer's language name (the editor language in Blocks)."""
        language = (locale.getlocale()[0] or "en").replace("_", "-").lower()
        info = LANGUAGE_INFO.get(language) or LANGUAGE_INFO.get(language.split("-")[0])
        return info["name"] if info else language

    def _get_speech_synth_locale(self, language):
        if language in LANGUAGE_INFO:
            return LANGUAGE_INFO[language]["speechSynthLocale"]
        else:
            return "en"
