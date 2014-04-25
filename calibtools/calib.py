import itertools
import json
import logging
import sys

import cv2
import numpy as np

log = logging.getLogger(__name__)

def tool(video, cb_shape, skip=None, output=None, start=None, duration=None):
    # Load input video
    log.debug('Processing {0}...'.format(video))
    vc = cv2.VideoCapture(video)

    # Parse chessboard shape
    if len(cb_shape) != 2:
        log.error('Chessboard shape should have 2 components, a width and height.')
        return 1
    log.debug('Using chessboard with shape: {0}x{1}'.format(*cb_shape))

    # Defaults
    skip = skip or 1
    start = start or 0
    log.debug('Processing every {0} frame(s) from {1}'.format(skip, start))

    image_pts = []
    frame_shape = None
    used_frames = []
    for frame_idx in itertools.count(0):
        flag, frame = vc.read()
        if not flag:
            break

        # Skip frame if we're not processing this one
        if frame_idx < start or frame_idx % skip != 0:
            continue

        # Stop processing after specified duration
        if duration is not None and frame_idx >= start + duration:
            break

        log.debug('Processing frame {0}'.format(frame_idx))

        # Convert to grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        if frame_shape is None:
            frame_shape = frame.shape

        # Look for chessboard
        rv, corners = cv2.findChessboardCorners(frame,
                cb_shape, flags=cv2.CALIB_CB_FAST_CHECK)
        if not rv:
            continue

        log.info('Board found in frame {0}'.format(frame_idx))

        # Refine corners
        cv2.cornerSubPix(frame, corners, (5,5), (-1,-1),
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 0.03))

        # Record corners
        image_pts.append(corners)
        used_frames.append(frame_idx)

    if len(image_pts) == 0:
        log.error('No chessboards found in video')
        return 1

    # Generate chessboard object points
    cb_coords = np.zeros((cb_shape[0] * cb_shape[1], 3), dtype=np.float32)
    cb_coords[:,:2] = np.asarray(list(itertools.product(range(cb_shape[1]), range(cb_shape[0]))))
    cb_pts = [ cb_coords ] * len(image_pts)

    # Calibrate
    log.info('Calibrating with {0} frame(s)...'.format(len(image_pts)))
    cam_matrix = np.eye(3)
    reproj_err, cam_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            cb_pts, image_pts, frame_shape[::-1], cam_matrix, None,
            flags=cv2.CALIB_RATIONAL_MODEL,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    log.info('Re-projection error is {0} pixels'.format(reproj_err))

    calib_result = {
        'input': {
            'video': video,
            'checkerboard_shape': cb_shape,
            'used_frames': used_frames,
        },
        'output': {
            'frameSize': frame_shape[::-1],
            'reprojError': reproj_err,
            'camMatrix': cam_matrix.tolist(),
            'distCoeffs': dist_coeffs.reshape(-1).tolist(),
        },
    }

    if output is not None:
        log.debug('Writing result to {0}.'.format(output))
    json.dump(calib_result, open(output, 'w') if output is not None else sys.stdout, indent=2)

    return 0
