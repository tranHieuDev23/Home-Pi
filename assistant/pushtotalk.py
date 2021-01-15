# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample that implements a gRPC client for the Google Assistant API."""

import concurrent.futures
import json
import logging
import os
import os.path
from .speech_request_handler import get_speech_request_handler
import pathlib2 as pathlib
import sys
import uuid

import click
import grpc
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)
from tenacity import retry, stop_after_attempt, retry_if_exception
from . import assistant_helpers, audio_helpers


ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5


class Assistant(object):
    """Assistant class that supports conversations and device actions.

    Args:
      device_model_id: identifier of the device model.
      device_id: identifier of the registered device instance.
      conversation_stream(ConversationStream): audio stream
        for recording query and playing back assistant answer.
      channel: authorized gRPC channel for connection to the
        Google Assistant API.
      deadline_sec: gRPC deadline in seconds for Google Assistant API call.
      device_handler: callback for device actions.
    """

    def __init__(self, language_code, device_model_id, device_id, conversation_stream, deadline_sec, device_handler, media_player):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_stream = conversation_stream
        self.media_player = media_player

        # Opaque blob provided in AssistResponse that,
        # when provided in a follow-up AssistRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Assist()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True

        # Create Google Assistant API gRPC client.
        self.assistant_client = None
        self.deadline = deadline_sec

        self.device_handler = device_handler

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False
        self.conversation_stream.close()

    def set_assistant_channel(self, channel):
        try:
            self.assistant_client = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
                channel
            )
        except:
            self.assistant_client = None

    def is_grpc_error_unavailable(e):
        is_grpc_error = isinstance(e, grpc.RpcError)
        if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
            logging.error('grpc unavailable error: %s', e)
            return True
        return False

    @retry(reraise=True, stop=stop_after_attempt(3),
           retry=retry_if_exception(is_grpc_error_unavailable))
    def assist(self):
        """Send a voice request to the Assistant and playback the response.

        Returns: True if conversation should continue.
        """
        if (self.assistant_client is None):
            return False

        continue_conversation = False
        device_actions_futures = []

        self.media_player.mute(True)
        self.conversation_stream.start_recording()
        logging.info('Recording audio request.')

        def iter_log_assist_requests():
            for c in self.gen_assist_requests():
                assistant_helpers.log_assist_request_without_audio(c)
                yield c
            logging.debug('Reached end of AssistRequest iteration.')

        # This generator yields AssistResponse proto messages
        # received from the gRPC Google Assistant API.
        for resp in self.assistant_client.Assist(iter_log_assist_requests(),
                                                 self.deadline):
            assistant_helpers.log_assist_response_without_audio(resp)
            if resp.event_type == END_OF_UTTERANCE:
                logging.info('End of audio request detected.')
                logging.info('Stopping recording.')
                self.conversation_stream.stop_recording()
                self.media_player.mute(False)
            if resp.speech_results:
                logging.info('Transcript of user request: "%s".',
                             ' '.join(r.transcript
                                      for r in resp.speech_results))
            if len(resp.audio_out.audio_data) > 0:
                if not self.conversation_stream.playing:
                    self.conversation_stream.stop_recording()
                    self.conversation_stream.start_playback()
                    logging.info('Playing assistant response.')
                self.conversation_stream.write(resp.audio_out.audio_data)
            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                logging.debug('Updating conversation state.')
                self.conversation_state = conversation_state
            if resp.dialog_state_out.volume_percentage != 0:
                volume_percentage = resp.dialog_state_out.volume_percentage
                logging.info('Setting volume to %s%%', volume_percentage)
                self.conversation_stream.volume_percentage = volume_percentage
            if resp.dialog_state_out.microphone_mode == DIALOG_FOLLOW_ON:
                continue_conversation = True
                logging.info('Expecting follow-on query from user.')
            elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
                continue_conversation = False
            if resp.device_action.device_request_json:
                device_request = json.loads(
                    resp.device_action.device_request_json
                )
                fs = self.device_handler(device_request)
                if fs:
                    device_actions_futures.extend(fs)

        if len(device_actions_futures):
            logging.info('Waiting for device executions to complete.')
            concurrent.futures.wait(device_actions_futures)

        logging.info('Finished playing assistant response.')
        self.conversation_stream.stop_playback()
        return continue_conversation

    def gen_assist_requests(self):
        """Yields: AssistRequest messages to send to the API."""

        config = embedded_assistant_pb2.AssistConfig(
            audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
            ),
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
                volume_percentage=self.conversation_stream.volume_percentage,
            ),
            dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                language_code=self.language_code,
                conversation_state=self.conversation_state,
                is_new_conversation=self.is_new_conversation,
            ),
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self.device_id,
                device_model_id=self.device_model_id,
            )
        )
        # Continue current conversation with later requests.
        self.is_new_conversation = False
        # The first AssistRequest must contain the AssistConfig
        # and no audio data.
        yield embedded_assistant_pb2.AssistRequest(config=config)
        for data in self.conversation_stream:
            # Subsequent requests need audio data, but not config.
            yield embedded_assistant_pb2.AssistRequest(audio_in=data)


class PushToTalkInstance:
    def __init__(self, api_endpoint, credentials_file, project_id, device_model_id, device_id, device_config, lang, verbose, audio_sample_rate, audio_sample_width, audio_iter_size, audio_block_size, audio_flush_size, grpc_deadline):
        """Samples for the Google Assistant API.

        Examples:
        Run the sample with microphone input and speaker output:

            $ python -m googlesamples.assistant

        Run the sample with file input and speaker output:

            $ python -m googlesamples.assistant -i <input file>

        Run the sample with file input and output:

            $ python -m googlesamples.assistant -i <input file> -o <output file>
        """
        # Setup logging.
        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

        # Configure audio source and sink.
        audio_device = None
        audio_source = audio_device = (
            audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size
            )
        )
        audio_sink = audio_device = (
            audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size
            )
        )
        # Create conversation stream with the given audio source and sink.
        conversation_stream = audio_helpers.ConversationStream(
            source=audio_source,
            sink=audio_sink,
            iter_size=audio_iter_size,
            sample_width=audio_sample_width,
        )

        if not device_id or not device_model_id:
            try:
                with open(device_config) as f:
                    device = json.load(f)
                    device_id = device['id']
                    device_model_id = device['model_id']
                    logging.info("Using device model %s and device id %s",
                                 device_model_id,
                                 device_id)
            except Exception as e:
                logging.warning('Device config not found: %s' % e)
                logging.info('Registering device')
                if not device_model_id:
                    logging.error('Option --device-model-id required '
                                  'when registering a device instance.')
                    sys.exit(-1)
                if not project_id:
                    logging.error('Option --project-id required '
                                  'when registering a device instance.')
                    sys.exit(-1)
                device_base_url = (
                    'https://%s/v1alpha2/projects/%s/devices' % (api_endpoint,
                                                                 project_id)
                )
                device_id = str(uuid.uuid1())
                payload = {
                    'id': device_id,
                    'model_id': device_model_id,
                    'client_type': 'SDK_SERVICE'
                }
                session = google.auth.transport.requests.AuthorizedSession(
                    credentials_file
                )
                r = session.post(device_base_url, data=json.dumps(payload))
                if r.status_code != 200:
                    logging.error('Failed to register device: %s', r.text)
                    sys.exit(-1)
                logging.info('Device registered: %s', device_id)
                pathlib.Path(os.path.dirname(device_config)
                             ).mkdir(exist_ok=True)
                with open(device_config, 'w') as f:
                    json.dump(payload, f)

        device_handler, media_player = get_speech_request_handler(device_id)

        self.assistant = Assistant(lang, device_model_id, device_id,
                                   conversation_stream, grpc_deadline, device_handler, media_player)

        # OAuth 2.0 credentials file
        self.credentials_file = credentials_file
        # Authorized gRPC channel
        self.grpc_channel = None
        self.api_endpoint = api_endpoint
        self.__connect_to_grpc_channel()

    def __is_grpc_channel_ready(self):
        if (self.grpc_channel is None):
            return False
        try:
            grpc.channel_ready_future(self.grpc_channel).result(timeout=5)
            return True
        except:
            return False

    def __connect_to_grpc_channel(self):
        try:
            with open(self.credentials_file, 'r') as f:
                credentials = google.oauth2.credentials.Credentials(token=None,
                                                                    **json.load(f))
                http_request = google.auth.transport.requests.Request()
                credentials.refresh(http_request)
        except Exception as e:
            logging.error('Error loading credentials: %s', e)
            logging.error(
                'Run google-oauthlib-tool to initialize new OAuth 2.0 credentials.')
            return False

        try:
            self.grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
                credentials, http_request, self.api_endpoint)
            self.assistant.set_assistant_channel(self.grpc_channel)
            logging.info('Connecting to %s', self.api_endpoint)
        except Exception as e:
            logging.error(
                'Error connecting to API endpoint credentials: %s', e)
            return False
        return True

    def loop(self):
        if (not self.__is_grpc_channel_ready()):
            if (not self.__connect_to_grpc_channel()):
                return False

        try:
            continue_conversation = True
            while continue_conversation:
                continue_conversation = self.assistant.assist()
            return True
        except Exception as e:
            is_grpc_error = isinstance(e, grpc.RpcError)
            if (is_grpc_error):
                self.grpc_channel = None
            return False


@click.command()
@click.option('--api-endpoint', default=ASSISTANT_API_ENDPOINT,
              metavar='<api endpoint>', show_default=True,
              help='Address of Google Assistant API service.')
@click.option('--credentials',
              metavar='<credentials>', show_default=True,
              default=os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json'),
              help='Path to read OAuth2 credentials.')
@click.option('--project-id',
              metavar='<project id>',
              help=('Google Developer Project ID used for registration '
                    'if --device-id is not specified'))
@click.option('--device-model-id',
              metavar='<device model id>',
              help=(('Unique device model identifier, '
                     'if not specifed, it is read from --device-config')))
@click.option('--device-id',
              metavar='<device id>',
              help=(('Unique registered device instance identifier, '
                     'if not specified, it is read from --device-config, '
                     'if no device_config found: a new device is registered '
                     'using a unique id and a new device config is saved')))
@click.option('--device-config', show_default=True,
              metavar='<device config>',
              default=os.path.join(
                  click.get_app_dir('googlesamples-assistant'),
                  'device_config.json'),
              help='Path to save and restore the device configuration')
@click.option('--lang', show_default=True,
              metavar='<language code>',
              default='en-US',
              help='Language code of the Assistant')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Verbose logging.')
@click.option('--audio-sample-rate',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE,
              metavar='<audio sample rate>', show_default=True,
              help='Audio sample rate in hertz.')
@click.option('--audio-sample-width',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH,
              metavar='<audio sample width>', show_default=True,
              help='Audio sample width in bytes.')
@click.option('--audio-iter-size',
              default=audio_helpers.DEFAULT_AUDIO_ITER_SIZE,
              metavar='<audio iter size>', show_default=True,
              help='Size of each read during audio stream iteration in bytes.')
@click.option('--audio-block-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE,
              metavar='<audio block size>', show_default=True,
              help=('Block size in bytes for each audio device '
                    'read and write operation.'))
@click.option('--audio-flush-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE,
              metavar='<audio flush size>', show_default=True,
              help=('Size of silence data in bytes written '
                    'during flush operation'))
@click.option('--grpc-deadline', default=DEFAULT_GRPC_DEADLINE,
              metavar='<grpc deadline>', show_default=True,
              help='gRPC deadline in seconds')
def main(api_endpoint, credentials, project_id, device_model_id, device_id, device_config, lang, verbose, audio_sample_rate, audio_sample_width, audio_iter_size, audio_block_size, audio_flush_size, grpc_deadline):
    instance = PushToTalkInstance(api_endpoint, credentials, project_id, device_model_id, device_id, device_config, lang,
                                  verbose, audio_sample_rate, audio_sample_width, audio_iter_size, audio_block_size, audio_flush_size, grpc_deadline)
    while True:
        input("Press Enter to start issue command")
        instance.loop()


def get_default_push_to_talk():
    api_endpoint = ASSISTANT_API_ENDPOINT
    credentials = os.path.join(click.get_app_dir(
        'google-oauthlib-tool'), 'credentials.json')
    project_id = os.getenv('PROJECT_ID')
    device_model_id = os.getenv('DEVICE_MODEL_ID')
    device_config = os.path.join(click.get_app_dir(
        'googlesamples-assistant'), 'device_config.json')
    lang = 'en-US'
    verbose = False
    audio_sample_rate = audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE
    audio_sample_width = audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH
    audio_iter_size = audio_helpers.DEFAULT_AUDIO_ITER_SIZE
    audio_block_size = audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE
    audio_flush_size = audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE
    grpc_deadline = DEFAULT_GRPC_DEADLINE
    return PushToTalkInstance(
        api_endpoint, credentials, project_id, device_model_id, None, device_config, lang,
        verbose, audio_sample_rate, audio_sample_width, audio_iter_size, audio_block_size,
        audio_flush_size, grpc_deadline
    )


if __name__ == '__main__':
    main()
