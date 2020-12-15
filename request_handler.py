import device_helpers


def get_request_handler(device_id):
    device_handler = device_helpers.DeviceRequestHandler(device_id)

    @device_handler.command('action.devices.commands.mediaStop')
    def stopMedia():
        print('Stop playing...')

    @device_handler.command('action.devices.commands.mediaNext')
    def nextMedia():
        print('To next media...')

    @device_handler.command('action.devices.commands.mediaPrevious')
    def previousMedia():
        print('To previous media...')

    @device_handler.command('action.devices.commands.mediaPause')
    def pauseMedia():
        print('Pause media...')

    @device_handler.command('action.devices.commands.mediaResume')
    def resumeMedia():
        print('Resume media...')

    @device_handler.command('action.devices.commands.mediaSeekRelative')
    def seekRelativeMedia(relativePositionMs):
        print('Seek relative media...', relativePositionMs)

    @device_handler.command('action.devices.commands.mediaSeekToPosition')
    def seekToPosMedia(absPositionMs):
        print('Seek to position media...', absPositionMs)

    @device_handler.command('action.devices.commands.mediaRepeatMode')
    def setRepeatModeMedia(isOn, isSingle):
        print('Set repeat mode media...', isOn, isSingle)

    @device_handler.command('action.devices.commands.mediaShuffle')
    def shuffleMedia():
        print('Shuffle media...')

    @device_handler.command('action.devices.commands.mute')
    def mute(mute):
        print('Muting...', mute)

    @device_handler.command('action.devices.commands.setVolume')
    def setVolume(volumeLevel):
        print('Set volume level:', volumeLevel)

    @device_handler.command('action.devices.commands.volumeRelative')
    def setVolumeRelative(relativeSteps):
        print('Set volume level relative:', relativeSteps)

    @device_handler.command('com.homepi.homeControl.light.commands.On')
    def turnLightOn(room):
        print('Turning on light in %s' % room)

    @device_handler.command('com.homepi.homeControl.light.commands.Off')
    def turnLightOff(room):
        print('Turning off light in %s' % room)

    @device_handler.command('com.homepi.homeControl.media.commands.Play')
    def playMedia(title):
        print('Playing %s' % title)

    return device_handler
