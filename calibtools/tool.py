"""
Usage:
    calibtools (-h | --help) | --version
    calibtools calib [-v... | --verbose...] [--start=INDEX] [--duration=NUMBER]
        [--skip=NUMBER] [-o FILE | --output=FILE] [--shape=WxH] <video>
    calibtools undistort [-v... | --verbose...] [--start=INDEX]
        [--duration=NUMBER] (-o FILE | --output=FILE) <calibration> <video>

Common options:
    -h --help               Show a command line usage summary.
    -v --verbose            Be verbose in logging progress. Repeat to increase
                            verbosity.
    --version               Output this tool's version number.

    -o FILE --output=FILE   Write output to FILENAME. The default behaviour is
                            to write to standard output unless noted otherwise
                            in an individual command's documentation.

    --start=INDEX           Start processing from frame INDEX (0-based).
    --duration=NUMBER       Read at most NUMBER frames from input.

    <video>                 Read input frames from <video>. This must be in a
                            format which OpenCV can understand.

Calibration options:
    --skip=NUMBER           Only process every NUMBER-th frame. Note that this
                            does not affect the interpretation of --duration. A
                            skip of 10 frames with a duration of 20 will result
                            in 2 frames of output. [default: 10]
    --shape=WxH             Checkerboard has WxH internal corners.
                            [default: 8x6]

Undistort options:
    <calibration>           A file containing calibration information in JSON
                            format as output by calibtools calib.

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
            'start':    parse(opts['--start'], int, 'starting index'),
            'duration': parse(opts['--duration'], int, 'duration'),
            'skip':     parse(opts['--skip'], int, 'frame skip'),
            'output':   opts['--output'],
        }
        video = opts['<video>']
    except ValueError:
        return 1

    return tool(video, cb_shape, **kwargs)

@subcommand
def undistort(opts):
    from calibtools.undistort import tool

    try:
        kwargs = {
            'start':    parse(opts['--start'], int, 'starting index'),
            'duration': parse(opts['--duration'], int, 'duration'),
        }
        video = opts['<video>']
        output = opts['--output']
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
