from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
import io


class TextToSpeechHelper:
    def __init__(self, service_account_filename):
        self.__client = texttospeech.TextToSpeechClient.from_service_account_json(
            service_account_filename)
        self.__voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        self.__audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

    def speak(self, text):
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self.__client.synthesize_speech(
            input=synthesis_input, voice=self.__voice, audio_config=self.__audio_config)
        response_audio = AudioSegment.from_file(
            io.BytesIO(response.audio_content), format='mp3')
        play(response_audio)
