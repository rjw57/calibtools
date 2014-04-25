"""
Usage:
    calibtools (-h | --help) | --version
    calibtools calib [-v... | --verbose...] [--start=INDEX] [--duration=NUMBER]
        [--skip=NUMBER] [--shape=WxH] [--threshold=NUMBER]
        [--no-stop] <video> [<output>]
    calibtools undistort [-v... | --verbose...] [--start=INDEX]
        [--duration=NUMBER] <calibration> <video> <output>

Common options:
    -h --help               Show a command line usage summary.
    -v --verbose            Be verbose in logging progress. Repeat to increase
                            verbosity.
    --version               Output this tool's version number.

    --start=INDEX           Start processing from frame INDEX (0-based).
    --duration=NUMBER       Read at most NUMBER frames from input.

    <video>                 Read input frames from <video>. See section on
                            specifying video input below.

Calibration options:
    --skip=NUMBER           Only process every NUMBER-th frame. Note that this
                            does not affect the interpretation of --duration. A
                            skip of 10 frames with a duration of 20 will result
                            in 2 frames of output. [default: 1]
    --shape=WxH             Checkerboard has WxH internal corners.
                            [default: 8x6]
    --threshold=NUMBER      Skip boards which are not different by NUMBER from
                            what we have previously seen. A value of 0 will
                            include all boards and a value of 1 will *ignore*
                            all boards save the first one. [default: 0.2]
    --no-stop               Don't automatically stop processing when enough
                            variation in board shape has been observed.
    <output>                Write calibration output in JSON format to <output>.
                            The default behaviour is to write to standard
                            output.

Undistort options:
    <calibration>           A file containing calibration information in JSON
                            format as output by calibtools calib.
    <output>                Write raw RGB24 formatted output frames to <output>.
                            Use - to explicitly specify standard output.

Specifying video input:
    When specifying video input (e.g. via <video>) one can use the filename of
    any file in format which OpenCV can understand. If one uses the form
    device:NUMBER then NUMBER is used as a a live video capture device number
    starting from 0. If one uses the form raw:WxH then raw RGB24 frames of
    width W and height H will be read from standard input. This is particularly
    useful if one wants to use ffmpeg to pipe in video from some capture
    device or video format not known to OpenCV.

"""
import functools
import logging
import json
import sys

import docopt

from calibtools import __version__

log = logging.getLogger(__name__)

SUBCOMMANDS = {}
def subcommand(f):
    """Decorator for subcommand. Adds the subcommand to the global dispatch
    table.

    """
    SUBCOMMANDS[f.__name__] = f
    return f

def parse(v, type_, description=None, default=None):
    try:
        return type_(v) if v is not None else default
    except ValueError:
        msg = 'Could not parse {1}: "{0}"'.format(
            v, description if description is not None else 'integer'
        )
        log.error(msg)
        raise ValueError(msg)

@subcommand
def calib(opts):
    from calibtools.calib import tool

    try:
        cb_shape = tuple(int(x) for x in opts['--shape'].split('x'))
        assert len(cb_shape) == 2
    except (ValueError, AssertionError):
        log.error('Could not parse checkerboard size: "{0}"'.format(opts['--shape']))
        return 1

    try:
        kwargs = {
            'start':        parse(opts['--start'], int, 'starting index'),
            'duration':     parse(opts['--duration'], int, 'duration'),
            'skip':         parse(opts['--skip'], int, 'frame skip'),
            'threshold':    parse(opts['--threshold'], float, 'threshold'),
            'output':       opts['<output>'],
        }
        video = opts['<video>']
        autostop = not parse(opts['--no-stop'], bool, 'no stop flag')
    except ValueError:
        return 1

    return tool(video, cb_shape, autostop=autostop, **kwargs)

@subcommand
def undistort(opts):
    from calibtools.undistort import tool

    try:
        kwargs = {
            'start':    parse(opts['--start'], int, 'starting index'),
            'duration': parse(opts['--duration'], int, 'duration'),
        }
        video = opts['<video>']
        output = opts['<output>']
        calibration = opts['<calibration>']
    except ValueError:
        return 1

    return tool(calibration, video, output, **kwargs)

def main():
    # Parse command line options
    opts = docopt.docopt(__doc__, version=__version__)

    # Handler verbosity. We don't use __name__ because we want to affect the
    # logging level for the root logger
    root_logger = logging.getLogger()
    log_levels = [logging.WARN, logging.INFO, logging.DEBUG]
    root_logger.setLevel(log_levels[min(len(log_levels)-1, opts['--verbose'])])

    # Write root logger to a stream formatter for stderr
    log_handler = logging.StreamHandler(stream=sys.stderr)
    log_handler.setFormatter(logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    ))
    root_logger.addHandler(log_handler)

    # Log options
    log.debug('Parsed command line options:')
    for line in json.dumps(opts, indent=2).split('\n'):
        log.debug(line)

    # Call the appropriate tool. We import at this stage to minimise startup time
    sc_funcs = list(func for sc, func in SUBCOMMANDS.items() if sc in opts and opts[sc])
    assert len(sc_funcs) == 1
    return sc_funcs[0](opts)

if __name__ == '__main__':
    sys.exit(main())

# vim:colorcolumn=81
