from . import device_helpers
from media.mediaplayer import VlcPlayer
from media.youtube_search_engine import youtube_search, youtube_stream_link
from home_control.device_manager import DeviceManager
from utils.text_to_speech import TextToSpeechHelper


def get_speech_request_handler(device_id):
    media_player = VlcPlayer()
    device_manager = DeviceManager()
    tts_helper = TextToSpeechHelper('service_account.json')
    device_handler = device_helpers.DeviceRequestHandler(device_id)

    for item in device_manager.devices:
        item.connect('broker.hivemq.com', 1883)

    @device_handler.command('action.devices.commands.mediaStop')
    def stopMedia():
        print('Stop playing...')
        media_player.stop()

    @device_handler.command('action.devices.commands.mediaNext')
    def nextMedia():
        print('To next media...')
        media_player.next()

    @device_handler.command('action.devices.commands.mediaPrevious')
    def previousMedia():
        print('To previous media...')
        media_player.previous()

    @device_handler.command('action.devices.commands.mediaPause')
    def pauseMedia():
        print('Pause media...')
        media_player.pause()

    @device_handler.command('action.devices.commands.mediaResume')
    def resumeMedia():
        print('Resume media...')
        media_player.play()

    @device_handler.command('action.devices.commands.mute')
    def mute(mute):
        print('Set mute to %s...', str(mute))
        media_player.mute(mute)

    @device_handler.command('action.devices.commands.setVolume')
    def setVolume(volumeLevel):
        print('Set volume level:', volumeLevel)
        media_player.set_volume(volumeLevel)

    @device_handler.command('action.devices.commands.volumeRelative')
    def setVolumeRelative(relativeSteps):
        print('Set volume level relative:', relativeSteps)
        current_level = media_player.get_volume()
        media_player.set_volume(current_level + relativeSteps)

    @device_handler.command('com.homepi.homeControl.commands.TurnOn')
    def turnOn(device_name):
        print('turnOn(%s)' % (device_name))
        search_results = device_manager.search_device({'name': device_name})
        if (len(search_results) == 0):
            tts_helper.speak('I cannot find any device with that name')
            return
        selected_device = search_results[0]
        selected_device.handle_command({'on': True})

    @device_handler.command('com.homepi.homeControl.commands.TurnOff')
    def turnOff(device_name):
        print('turnOff(%s)' % (device_name))
        search_results = device_manager.search_device({'name': device_name})
        if (len(search_results) == 0):
            tts_helper.speak('I cannot find any device with that name')
            return
        selected_device = search_results[0]
        selected_device.handle_command({'off': True})

    @device_handler.command('com.homepi.homeControl.media.commands.Play')
    def playMedia(title):
        print('Playing %s' % title)
        if (media_player.is_playing()):
            media_player.stop()
        video_url = youtube_search(title)
        audio_steam, video_stream = youtube_stream_link(video_url)
        media_player.play_track(audio_steam)

    return device_handler, media_player
