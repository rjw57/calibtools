"""
Usage:
    calibtools-calib [options] <video>

Options:
    -h, --help                      Show a brief usage summary.
    --version                       Show program version.
    -v, --verbose                   Be verbose in logging output.
    -o FILENAME, --output=FILENAME  Write calibration result to FILENAME.
                                    [default: output.json]
    -s NUM, --skip=NUM              Only process every NUM-th frame. [default: 100]
    -c SHAPE, --chessboard=SHAPE    Number of internal corners in chessboard specified
                                    as <width>x<height>. [default: 8x6]
    --start=INDEX                   Start processing from frame at (1-based) INDEX.
                                    [default: 0]
    --duration=COUNT                Process at most COUNT frames. Use 'all' to process
                                    all frames. [default: all]
"""
import itertools
import json
import logging
import sys

import cv2
import docopt
import numpy as np

from calibtools import __version__

def main(cli_opts=None):
    # Add cli_opts to defaults
    opts = {
        '--verbose': False,
        '--skip': '100',
        '--chessboard': '8x6',
        '--start': '0',
        '--duration': 'all',
        '--output': 'output.json',
    }
    opts.update(cli_opts or {})

    # Set up logging
    logging.basicConfig(
        level=logging.INFO if opts['--verbose'] else logging.WARN
    )

    # Load input video
    logging.info('Processing {0}...'.format(opts['<video>']))
    vc = cv2.VideoCapture(opts['<video>'])

    # Parse chessboard shape
    cb_shape = tuple(int(x) for x in opts['--chessboard'].split('x'))
    if len(cb_shape) != 2:
        logging.error('Chessboard shape should have 2 components, a width and height.')
        return 1
    logging.info('Using chessboard with shape: {0}x{1}'.format(*cb_shape))

    skip = int(opts['--skip'])
    logging.info('Processing every {0} frame(s)'.format(skip))

    start_frame = int(opts['--start'])
    duration = None if opts['--duration'] == 'all' else int(opts['--duration'])

    image_pts = []
    frame_shape = None
    for frame_idx in itertools.count(0):
        flag, frame = vc.read()
        if not flag:
            break

        # Skip frame if we're not processing this one
        if frame_idx + 1 < start_frame or frame_idx % skip != 0:
            continue

        if duration is not None and frame_idx + 1 >= start_frame + duration:
            break

        # Convert to grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        if frame_shape is None:
            frame_shape = frame.shape

        # Look for chessboard
        rv, corners = cv2.findChessboardCorners(frame,
                cb_shape, flags=cv2.CALIB_CB_FAST_CHECK)
        if not rv:
            continue

        logging.info('Board found in frame {0}'.format(frame_idx))

        # Refine corners
        cv2.cornerSubPix(frame, corners, (5,5), (-1,-1),
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 0.03))

        # Record corners
        image_pts.append(corners)

    if len(image_pts) == 0:
        logging.error('No chessboards found in video')
        return 1

    # Generate chessboard object points
    cb_coords = np.zeros((cb_shape[0] * cb_shape[1], 3), dtype=np.float32)
    cb_coords[:,:2] = np.asarray(list(itertools.product(range(cb_shape[1]), range(cb_shape[0]))))
    cb_pts = [ cb_coords ] * len(image_pts)

    # Calibrate
    logging.info('Calibrating with {0} frame(s)...'.format(len(image_pts)))
    cam_matrix = np.eye(3)
    reproj_err, cam_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            cb_pts, image_pts, frame_shape[::-1], cam_matrix, None,
            flags=cv2.CALIB_RATIONAL_MODEL,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    logging.info('Re-projection error is {0} pixels'.format(reproj_err))

    calib_result = {
        'input': opts['<video>'],
        'options': opts,
        'output': {
            'frameSize': frame_shape[::-1],
            'reprojError': reproj_err,
            'camMatrix': cam_matrix.tolist(),
            'distCoeffs': dist_coeffs.tolist(),
        },
    }

    logging.info('Writing result to {0}.'.format(opts['--output']))
    json.dump(calib_result, open(opts['--output'], 'w'))

    return 0

def start():
    sys.exit(main(docopt.docopt(__doc__, version=__version__)))

if __name__ == '__main__':
    start()
