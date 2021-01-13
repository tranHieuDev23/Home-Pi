import argparse
import pvporcupine
from assistant.pushtotalk import get_default_push_to_talk
from utils.porcupine_helper import PorcupineInstance


def __parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--keywords',
        nargs='+',
        help='List of default keywords for detection. Available keywords: %s' % ', '.join(
            sorted(pvporcupine.KEYWORDS)),
        choices=sorted(pvporcupine.KEYWORDS),
        metavar='')
    parser.add_argument(
        '--keyword_paths',
        nargs='+',
        help="Absolute paths to keyword model files. If not set it will be populated from `--keywords` argument")
    parser.add_argument(
        '--library_path', help='Absolute path to dynamic library.', default=pvporcupine.LIBRARY_PATH)
    parser.add_argument(
        '--model_path',
        help='Absolute path to the file containing model parameters.',
        default=pvporcupine.MODEL_PATH)
    parser.add_argument(
        '--sensitivities',
        nargs='+',
        help="Sensitivities for detecting keywords. Each value should be a number within [0, 1]. A higher " +
             "sensitivity results in fewer misses at the cost of increasing the false alarm rate. If not set 0.5 " +
             "will be used.",
        type=float,
        default=None)
    parser.add_argument('--audio_device_index',
                        help='Index of input audio device.', type=int, default=None)
    parser.add_argument('--show_audio_devices', action='store_true')
    args = parser.parse_args()
    if (args.show_audio_devices):
        return args
    if (args.keyword_paths is None):
        if (args.keywords is None):
            raise ValueError(
                "Either `--keywords` or `--keyword_paths` must be set.")
        args.keyword_paths = [pvporcupine.KEYWORD_PATHS[x]
                              for x in args.keywords]
    if (args.sensitivities is None):
        args.sensitivities = [0.5] * len(args.keyword_paths)
    elif (len(args.keyword_paths) != len(args.sensitivities)):
        raise ValueError(
            'Number of keywords does not match the number of sensitivities.')
    return args


def main():
    args = __parse_arguments()
    if args.show_audio_devices:
        PorcupineInstance.show_audio_devices()
        return

    porcupine_instance = PorcupineInstance(
        library_path=args.library_path,
        model_path=args.model_path,
        keyword_paths=args.keyword_paths,
        sensitivities=args.sensitivities,
        input_device_index=args.audio_device_index,
        push_to_talk=get_default_push_to_talk())
    porcupine_instance.run()


if __name__ == '__main__':
    main()
