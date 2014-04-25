import itertools
import json
import logging
import sys

import cv2
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
import numpy as np

from calibtools.util import open_video

def tool(calibration, video, output, start=None, duration=None):
    start = start or 0

    # Load calibration
    logging.debug('Loading calibration from {0}...'.format(calibration))
    calibration = json.load(open(calibration))
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
    vc = open_video(video)
    try:
        fps = vc.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 25
    except AttributeError:
        fps = 25

    # Prepare output
    vo = FFMPEG_VideoWriter(output, frame_size, fps, 'png',
            logfile=sys.stderr)

    for frame_idx in itertools.count(0):
        flag, frame = vc.read()
        if not flag:
            break

        # Skip frame if we're not processing this one
        if frame_idx < start:
            continue
        if duration is not None and frame_idx >= start + duration:
            break

        logging.debug('Processing frame {0}...'.format(frame_idx))

        # Undistort
        output = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)

        # Note that OpenCV and FFMPEG differ on ordering of components
        vo.write_frame(output[:,:,::-1])

    vo.close()

    return 0
