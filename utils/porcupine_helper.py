import struct
from threading import Thread
import pvporcupine
import pyaudio
from pydub import AudioSegment
from pydub.playback import play


class PorcupineInstance(Thread):
    def __init__(self, library_path, model_path, keyword_paths, sensitivities, input_device_index=None, push_to_talk=None, no_internet_audio_file=None):
        """
        Constructor.
        :param library_path: Absolute path to Porcupine's dynamic library.
        :param model_path: Absolute path to the file containing model parameters.
        :param keyword_paths: Absolute paths to keyword model files.
        :param sensitivities: Sensitivities for detecting keywords. Each value should be a number within [0, 1]. A
        higher sensitivity results in fewer misses at the cost of increasing the false alarm rate. If not set 0.5 will
        be used.
        :param input_device_index: Optional argument. If provided, audio is recorded from this input device. Otherwise,
        the default audio input device is used.
        """
        super(PorcupineInstance, self).__init__()
        self._library_path = library_path
        self._model_path = model_path
        self._keyword_paths = keyword_paths
        self._sensitivities = sensitivities
        self._input_device_index = input_device_index
        self._push_to_talk = push_to_talk
        self._no_internet_audio_file = no_internet_audio_file

    def run(self):
        """
         Creates an input audio stream, instantiates an instance of Porcupine object, and monitors the audio stream for
         occurrences of the wake word(s).
         """
        porcupine = None
        pa = None
        audio_stream = None
        try:
            porcupine = pvporcupine.create(
                library_path=self._library_path,
                model_path=self._model_path,
                keyword_paths=self._keyword_paths,
                sensitivities=self._sensitivities)

            pa = pyaudio.PyAudio()

            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
                input_device_index=self._input_device_index)

            print('Listening...')

            while True:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                result = porcupine.process(pcm)
                if result >= 0:
                    self.on_hotword_detected()

        except KeyboardInterrupt:
            print('Stopping ...')
        finally:
            if porcupine is not None:
                porcupine.delete()
            if audio_stream is not None:
                audio_stream.close()
            if pa is not None:
                pa.terminate()

    @classmethod
    def show_audio_devices(cls):
        fields = ('index', 'name', 'defaultSampleRate', 'maxInputChannels')
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            print(', '.join("'%s': '%s'" % (k, str(info[k])) for k in fields))
        pa.terminate()

    def __notify_no_internet(self):
        if (self._no_internet_audio_file is None):
            return
        try:
            with open(self._no_internet_audio_file, 'rb') as no_internet_audio:
                response_audio = AudioSegment.from_file(
                    no_internet_audio, format='mp3')
                play(response_audio)
        except Exception as e:
            print('Problem while playing no internet notification audio:', str(e))

    def on_hotword_detected(self):
        print("Hot word detected!")
        if (self._push_to_talk is not None):
            if (not self._push_to_talk.loop()):
                self.__notify_no_internet()
