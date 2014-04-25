import logging
import sys

import cv2
import numpy as np

log = logging.getLogger(__name__)

class _RawVideoCapture(object):
    def __init__(self, width, height, stream=sys.stdin.buffer):
        self.width = width
        self.height = height
        self.stream = stream

    def read(self):
        nbytes = 3 * self.width * self.height
        try:
            frame = self.stream.read(nbytes)
        except IOError:
            return False, None

        if len(frame) != nbytes:
            return False, None

        # Massage data into right shape. Note FFMPEG and OpenCV disagree about byte
        # ordering
        frame = np.frombuffer(frame, dtype=np.uint8)
        return True, frame.reshape(self.height, self.width, -1)[:,:,::-1]

def open_video(specifier):
    """Return an OpenCV VideoCapture-like object which can be used to read
    frames from *specifier*. Note that only the read() method is guaranteed to
    be defined.

    """
    if specifier.startswith('device:'):
        specifier_dev = int(specifier[7:])
        log.debug('Opening video device {0}...'.format(specifier_dev))
        vc = cv2.VideoCapture(specifier_dev)
    elif specifier.startswith('raw:'):
        try:
            w, h = tuple(int(x) for x in specifier[4:].split('x'))
        except ValueError:
            log.error('Could not parse raw specifier size from "{0}"'.format(specifier))
            return 1
        log.debug('Using raw video with shape {0}x{1}'.format(w,h))
        vc = _RawVideoCapture(w, h)
    else:
        log.debug('Using OpenCV video capture on {0}'.format(specifier))
        vc = cv2.VideoCapture(specifier)

    return vc
