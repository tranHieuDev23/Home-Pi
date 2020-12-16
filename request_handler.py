import device_helpers
from util.mediaplayer import VlcPlayer
from util.youtube_search_engine import youtube_search, youtube_stream_link


def get_request_handler(device_id):
    media_player = VlcPlayer()
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

    @device_handler.command('com.homepi.homeControl.light.commands.On')
    def turnLightOn(room):
        print('Turning on light in %s' % room)

    @device_handler.command('com.homepi.homeControl.light.commands.Off')
    def turnLightOff(room):
        print('Turning off light in %s' % room)

    @device_handler.command('com.homepi.homeControl.media.commands.Play')
    def playMedia(title):
        print('Playing %s' % title)
        if (media_player.is_playing()):
            media_player.stop()
        video_url = youtube_search(title)
        audio_steam, video_stream = youtube_stream_link(video_url)
        media_player.play_track(audio_steam)

    return device_handler, media_player
