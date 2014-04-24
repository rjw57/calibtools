"""
Undistort an input video writing result to output.

Usage:
    calibtools-undistort [options] <calibration> <input> <output>

Options:
    -h, --help                      Show a brief usage summary.
    --version                       Show program version.
    -v, --verbose                   Be verbose in logging output.
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
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
import numpy as np

from calibtools import __version__

def main(cli_opts=None):
    # Add cli_opts to defaults
    opts = {
        '--verbose': False,
        '--start': '0',
        '--duration': 'all',
    }
    opts.update(cli_opts or {})

    # Set up logging
    logging.basicConfig(
        level=logging.INFO if opts['--verbose'] else logging.WARN
    )

    # Load calibration
    logging.info('Loading calibration from {0}...'.format(opts['<calibration>']))
    calibration = json.load(open(opts['<calibration>']))

    cam_matrix = np.asarray(calibration['output']['camMatrix'])
    dist_coeffs = np.asarray(calibration['output']['distCoeffs'])
    frame_size = tuple(calibration['output']['frameSize'])

    # Compute optimal new matrix, etc
    new_cam_matrix, valid_roi = cv2.getOptimalNewCameraMatrix(
            cam_matrix, dist_coeffs, frame_size, 1)

    # Calculate undistort maps
    map1, map2 = cv2.initUndistortRectifyMap(
            cam_matrix, dist_coeffs, None, new_cam_matrix, frame_size,
            cv2.CV_16SC2)

    # Load input video
    logging.info('Processing {0}...'.format(opts['<input>']))
    vc = cv2.VideoCapture(opts['<input>'])
    fps = vc.get(cv2.CAP_PROP_FPS)

    start_frame = int(opts['--start'])
    duration = None if opts['--duration'] == 'all' else int(opts['--duration'])

    # Prepare output
    vo = FFMPEG_VideoWriter(opts['<output>'], frame_size, fps, 'png', '18M')

    for frame_idx in itertools.count(0):
        flag, frame = vc.read()
        if not flag:
            break

        # Skip frame if we're not processing this one
        if frame_idx + 1 < start_frame:
            continue
        if duration is not None and frame_idx + 1 >= start_frame + duration:
            break

        if frame_idx % 100 == 0:
            logging.info('Processing frame {0}...'.format(frame_idx))

        # Undistort
        output = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)

        # Note that OpenCV and FFMPEG differ on ordering of components
        vo.write_frame(output[:,:,::-1])

    vo.close()

    return 0

def start():
    sys.exit(main(docopt.docopt(__doc__, version=__version__)))

if __name__ == '__main__':
    start()
