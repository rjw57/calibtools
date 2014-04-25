calibtools: a camera calibration toolbox
========================================

This package is a repository for some useful scripts for performing camera
calibration in Python. It requires the following modules:

* OpenCV's Python bindings
* moviepy
* numpy

The calibtools utlity
---------------------

The calibtools package provides one command-line utility which is named,
unimaginatively, ``calibtools``. The command-line interface documentation is
reproduced below:

.. autoliteral:: calibtools.tool

Recipes
~~~~~~~

To pipe video directly from ffmpeg, e.g. to have some fine control over a
webcam, one can use:

.. code-block:: console

    $ ffmpeg -f video4linux2 -input_format mjpeg -s 1280x720 -r 30 -i /dev/video1 \
        -vcodec rawvideo -f rawvideo -pix_fmt rgb24 - \
        | calibtools calib raw:1280x720 -v -o foo.json

To convert undistorted video on the fly, one can use:

.. code-block:: console

    $ calibtools undistort calibration.json video.mp4 - | ffmpeg -y -f rawvideo \
        -pix_fmt rgb24 -s 1920x1080 -i - -r 30 output.mp4

