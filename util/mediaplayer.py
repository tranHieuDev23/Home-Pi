import vlc
import os
import json

STATUS_FILE_PATH = '.player.json'


class VlcPlayer():
    def __init__(self):
        self._vlc_instance = vlc.Instance('--verbose 0')
        self._vlc_player = self._vlc_instance.media_player_new()
        self.track_urls = None
        self.current_track_id = None
        self.num_tracks = None
        self.volume_level = 90
        self._load_status()
        self.set_volume(self.volume_level)
        self._is_playing = False

    def play_track_list(self, track_urls):
        self.track_urls = track_urls
        self.current_track_id = 0
        self.num_tracks = len(track_urls)
        self._dump_status()
        self._play_media_url(self.track_urls[self.current_track_id])

    def play_track(self, track_url):
        self.play_track_list([track_url])

    def set_volume(self, level):
        self.volume_level = max(level, 0)
        self._vlc_player.audio_set_volume(level)

    def get_volume(self):
        return self.volume_level

    def mute(self, status=True):
        return self._vlc_player.audio_set_mute(status)

    def stop(self):
        self._vlc_player.stop()
        self._is_playing = False

    def pause(self):
        self._vlc_player.pause()

    def play(self):
        if (self._vlc_player.get_state() == vlc.State.Playing):
            return
        if (self._vlc_player.get_state() == vlc.State.Paused):
            self._vlc_player.play()
        else:
            if (self.track_urls is not None):
                self._play_media_url(self.track_urls[self.current_track_id])

    def is_playing(self):
        return self._is_playing

    def next(self):
        if (self.current_track_id == self.num_tracks - 1):
            self.current_track_id = 0
        else:
            self.current_track_id += 1
        self._dump_status()
        self._play_media_url(self.track_urls[self.current_track_id])

    def previous(self):
        if (self.current_track_id == 0):
            self.current_track_id = self.num_tracks - 1
        else:
            self.current_track_id -= 1
        self._dump_status()
        self._play_media_url(self.track_urls[self.current_track_id])

    def _load_status(self):
        if (not os.path.isfile(STATUS_FILE_PATH)):
            return
        with open(STATUS_FILE_PATH, 'r') as input_file:
            player_status = json.load(input_file)
            self.track_urls = player_status['track_urls']
            self.current_track_id = player_status['current_track_id']
            self.num_tracks = player_status['num_tracks']
            self.volume_level = player_status['volume_level']

    def _dump_status(self):
        player_status = {
            'track_urls': self.track_urls,
            'current_track_id': self.current_track_id,
            'num_tracks': self.num_tracks,
            'volume_level': self.volume_level
        }
        with open(STATUS_FILE_PATH, 'w') as output_file:
            json.dump(player_status, output_file)

    def _end_callback(self, _):
        self.next()

    def _play_media_url(self, media_url):
        self._vlc_player = self._vlc_instance.media_player_new()
        media = self._vlc_instance.media_new(media_url)
        self._vlc_player.set_media(media)
        self._vlc_player.play()
        self._is_playing = True
        event_manager = self._vlc_player.event_manager()
        event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached, self._end_callback)
