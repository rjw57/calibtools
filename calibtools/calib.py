import itertools
import json
import logging
import sys

import cv2
import numpy as np

from calibtools.util import open_video

log = logging.getLogger(__name__)

def corner_shape_parameters(corners, frame_shape, cb_shape):
    """
    Return a tuple of shape parameters for a given set of corners. This is
    based on the parameters from ROS's perception library[1]. The parameters
    returned are mean x- and y- co-ordinate normalised onto the interval
    [0,1], the relative size of the set of corners within the frame on the
    interval [0,1] and a 'skewness' metric on the inteval [0,1].

    *corners* is a Nx2 numpy array of detected corner locations.

    *frame_shape* is a pair giving the width and height of the frame.

    *cb_shape* is a pair giving the number of horizontal and vertical corners

    [1] https://github.com/ros-perception/image_pipeline/

    """
    corners = corners.reshape(-1, 2)
    assert corners.shape[0] == cb_shape[0] * cb_shape[1]

    h, w = frame_shape

    # Extract the "outside" corners which define the shape of the board in
    # a clockwise order. I.e. [A,B,C,D] where:
    #
    # A----B
    # |    |
    # D----C
    A, B, C, D = tuple(x.reshape(-1) for x in corners[[0, cb_shape[0]-1, -1, -cb_shape[0]], :])

    ba, bc = A - B, C - B   # Edges
    bd, ac = D - B, C - A   # Diagonals

    # Compute the angle between AB and BC
    angle = np.arccos(np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc)))

    # Compute skew metric
    skew = min(1, 2 * np.abs(0.5*np.pi - angle))

    # Compute area (assuming quadrilateral) and hence size metric
    area = 0.5 * np.abs(bd[0]*ac[1] - bd[1]*ac[0])
    size = np.sqrt(area / (h*w))

    # For X and Y, we "shrink" the image all around by approx. half the board
    # size. Otherwise large boards are penalized because you can't get much
    # X/Y variation.
    border = np.sqrt(area)
    X = np.clip((np.mean(corners[:,0]) - 0.5*border) / (w - border), 0, 1)
    Y = np.clip((np.mean(corners[:,1]) - 0.5*border) / (h - border), 0, 1)

    return (X, Y, size, skew)

def tool(video, cb_shape, autostop=True, skip=None, output=None, start=None,
        duration=None, threshold=None):
    # Load input video
    vc = open_video(video)

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

    # A list of parameters for each board we used
    used_board_params = []
    minmax_parameters = None
    goals = np.asarray((0.7, 0.7, 0.4, 0.5))
    param_labels = ('X', 'Y', 'size', 'skew')

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

        log.debug('Board found in frame {0}'.format(frame_idx))

        board_params = np.asarray(corner_shape_parameters(corners, frame_shape, cb_shape))
        log.debug('Board has parameters: {0}'.format(board_params))

        log.debug('Automatic selection threshold is {0}'.format(threshold))

        # If we have previous parameters and we auto threshold, see if we go
        # any further
        if len(used_board_params) > 0 and threshold is not None:
            # Compute L1 distance in parameters for each prior board
            min_l1_delta = np.asarray(
                    list(np.sum(np.abs(p - board_params)) for p in used_board_params)
            ).min()

            log.debug('Minimum L1 delta is {0}'.format(min_l1_delta))

            # Is minimum distance not good?
            if min_l1_delta < threshold:
                continue

        # Add this board's parameters to our records
        used_board_params.append(board_params)

        # Update minimum and maximum params
        if minmax_parameters is None:
            minmax_parameters = np.vstack((board_params, board_params))
        else:
            minmax_parameters[0,:] = np.minimum(minmax_parameters[0,:], board_params)
            minmax_parameters[1,:] = np.maximum(minmax_parameters[1,:], board_params)

        # Compute progress towards full coverage
        ranges = minmax_parameters[1,:] - minmax_parameters[0,:]
        ranges[2:] = minmax_parameters[1,2:] # Don't reward small sizes or small skews
        progress = np.clip(ranges / goals, 0, 1)
        progress_str = ' '.join(
                '{1}:{0}%'.format(int(100*x), k) for x, k in zip(progress, param_labels)
        )

        log.info('Using board in frame {0}. Progress: {1}'.format(frame_idx, progress_str))
        log.debug('Parameter ranges: {0}'.format(minmax_parameters.T.tolist()))

        # Refine corners
        cv2.cornerSubPix(frame, corners, (5,5), (-1,-1),
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 0.03))

        # Record corners
        image_pts.append(corners)
        used_frames.append(frame_idx)

        # Do we auto-stop?
        if autostop and np.all(progress > 0.99):
            break

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
