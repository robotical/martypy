"""Speak/Translate tests discovered by the standard suite; no robot or sound output."""
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from pydub import AudioSegment

from martypy.Marty import Marty
from martypy.ClientMV2 import ClientMV2
from martypy.Text2Speech import Text2Speech


@pytest.fixture
def audio_bytes():
    return AudioSegment.silent(duration=400).export(BytesIO(), format="mp3").getvalue()


@pytest.fixture
def service(monkeypatch, audio_bytes):
    response = Mock(content=audio_bytes)
    response.json.return_value = {"result": "bonjour"}
    get = Mock(return_value=response)
    monkeypatch.setattr("martypy.Text2Speech.requests.get", get)
    return get


@pytest.fixture
def marty():
    robot = Marty.__new__(Marty)
    robot.client = ClientMV2.__new__(ClientMV2)
    robot.client.speak = Mock(return_value=True)
    robot.client.close = Mock()
    robot.client.wait_if_required = Mock()
    robot.client.last_speech_duration_ms = 1234
    return robot


def test_settings_persist_and_explicit_options_override_without_resetting(marty):
    marty.set_voice("MALE")
    marty.set_voice_speed(1.5)
    marty.set_speech_language("French")
    marty.speak("bonjour", blocking=True)
    marty.client.speak.assert_called_with("bonjour", "TENOR", language="fr", speed=1.5)
    marty.client.wait_if_required.assert_called_once_with(1234, True)
    marty.speak("hello", "FEMALE", language="en", speed=1)
    marty.client.speak.assert_called_with("hello", "ALTO", language="en", speed=1)
    marty.speak("encore")
    marty.client.speak.assert_called_with("encore", "TENOR", language="fr", speed=1.5)


@pytest.mark.parametrize("speed", [0, 2.1, float("inf"), float("nan"), "fast"])
def test_invalid_speed_does_not_change_state(marty, speed):
    with pytest.raises(ValueError):
        marty.set_voice_speed(speed)
    assert marty._get_speech_settings()["speed"] == 1


def test_invalid_voice_and_accent_are_reported(marty):
    with pytest.raises(ValueError, match="voice"):
        marty.set_voice("not a voice")
    with pytest.raises(ValueError, match="speech language"):
        marty.set_speech_language("xx")


def test_synthesis_uses_robotical_service_locale_gender_timeout_and_limit(service):
    tts = Text2Speech()
    result = tts.speak("x" * 200, "MALE", "en")
    service.assert_called_once_with(tts.SERVER_HOST + "/synth", params={
        "locale": "en-US", "gender": "male", "text": "x" * 128
    }, timeout=10)
    assert isinstance(result, bytes)
    assert 350 <= tts.duration_ms <= 450
    service.return_value.raise_for_status.assert_called_once()


def test_speed_really_changes_audio_duration(service):
    tts = Text2Speech()
    normal = tts.speak("hello", "FEMALE", speed=1)
    faster = tts.speak("hello", "FEMALE", speed=2)
    normal_duration = len(AudioSegment.from_file(BytesIO(normal), format="mp3"))
    faster_duration = len(AudioSegment.from_file(BytesIO(faster), format="mp3"))
    assert faster_duration == pytest.approx(normal_duration / 2, abs=10)
    assert tts.duration_ms == pytest.approx(faster_duration, abs=10)


def test_single_gender_and_kitten_match_blocks(service):
    tts = Text2Speech()
    tts.speak("hello", "MALE", "ar")
    assert service.call_args.kwargs["params"]["gender"] == "female"
    assert tts.duration_ms > 400
    tts.speak("one   two\nthree", "KITTEN", "fr")
    assert service.call_args.kwargs["params"] == {
        "locale": "en-US", "gender": "female", "text": "meow meow meow"
    }


def test_translation_reports_text_and_supports_other_language_codes(marty, service):
    assert marty.translate("hello & goodbye", "el") == "bonjour"
    service.assert_called_once_with(Text2Speech().SERVER_HOST + "/translate", params={
        "language": "el", "text": "hello & goodbye"
    }, timeout=10)
    assert marty.translate("123", "fr") == "123"
    assert service.call_count == 1
    assert not marty.client.speak.called


def test_translation_failure_is_not_silently_treated_as_success(marty, service):
    service.return_value.json.return_value = {"error": "unavailable"}
    with pytest.raises(ValueError, match="invalid result"):
        marty.translate("hello", "fr")
    service.side_effect = requests.Timeout("offline")
    with pytest.raises(requests.Timeout):
        marty.translate("hello", "fr")


def test_viewer_language_uses_computer_locale(marty, monkeypatch):
    monkeypatch.setattr("martypy.Text2Speech.locale.getlocale", lambda: ("fr_FR", "UTF-8"))
    assert marty.get_language() == "French"


def test_computer_speech_does_not_send_robot_audio(marty, service, monkeypatch):
    play = Mock()
    monkeypatch.setattr("pydub.playback.play", play)
    marty.set_speech_language("fr")
    assert marty.speak_on_computer("bonjour") is True
    play.assert_called_once()
    assert service.call_args.kwargs["params"]["locale"] == "fr-FR"
    assert not marty.client.speak.called


@pytest.mark.parametrize("fail", [False, True])
def test_robot_speech_uses_unique_temp_file_and_cleans_up(service, fail):
    client = ClientMV2.__new__(ClientMV2)
    client._playMP3ProgressAdapter = Mock()
    paths = []

    def stream(path, endpoint, progress):
        paths.append(path)
        assert Path(path).read_bytes() == service.return_value.content
        assert endpoint == "streamaudio"
        if fail:
            raise RuntimeError("stream failed")
        return True

    client.ricIF = Mock(streamSoundFile=stream)
    if fail:
        with pytest.raises(RuntimeError, match="stream failed"):
            client.speak("hello")
    else:
        assert client.speak("hello")
        assert client.speak("hello")
        assert paths[0] != paths[1]
    assert all(not Path(path).exists() for path in paths)
