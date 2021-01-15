from . import device_helpers
from media.mediaplayer import VlcPlayer
from media.youtube_search_engine import youtube_search, youtube_stream_link
from home_control.home_control_service import issue_command, get_status
from utils.text_to_speech import TextToSpeechHelper


def get_speech_request_handler(device_id):
    media_player = VlcPlayer()
    tts_helper = TextToSpeechHelper('service_account.json')
    device_handler = device_helpers.DeviceRequestHandler(device_id)

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
        target = issue_command(device_name, 'turnOn')
        if (target is not None):
            tts_helper.speak('Okay, turning on %s' % target['displayName'])
        else:
            tts_helper.speak('Sorry, I could not do that')

    @device_handler.command('com.homepi.homeControl.commands.TurnOff')
    def turnOff(device_name):
        print('turnOff(%s)' % (device_name))
        target = issue_command(device_name, 'turnOff')
        if (target is not None):
            tts_helper.speak('Okay, turning off %s' % target['displayName'])
        else:
            tts_helper.speak('Sorry, I could not do that')

    @device_handler.command('com.homepi.homeControl.commands.RequestIsOn')
    def isOn(device_name):
        print('isOn(%s)' % (device_name))
        result = get_status(device_name, ['isOn'])
        if (result is not None):
            target_device, field_values = result
            target_device_name = target_device['displayName']
            isOn = field_values[0]
            if (isOn is None):
                tts_helper.speak(
                    'Sorry, I don\'t know if %s is turned on' % target_device_name)
            elif (isOn):
                tts_helper.speak('%s is turned on' % target_device_name)
            else:
                tts_helper.speak('%s is not turned on' % target_device_name)
        else:
            tts_helper.speak('Sorry, I could not do that')

    @device_handler.command('com.homepi.homeControl.media.commands.Play')
    def playMedia(title):
        print('Playing %s' % title)
        if (media_player.is_playing()):
            media_player.stop()
        video_url = youtube_search(title)
        audio_steam, video_stream = youtube_stream_link(video_url)
        media_player.play_track(audio_steam)

    return device_handler, media_player
