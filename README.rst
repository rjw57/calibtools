Camera calibration toolbox for Python
=====================================

This is a very incomplete set of tools for camera calibration.

Requirements
~~~~~~~~~~~~

* OpenCV's Python Bindings
* moviepy
* numpy

Usage
~~~~~

Print out a checkerboard and record a video of you waving it around. The
``calibtools-calib`` script can then be used to estimate camera parameters. The
``calibtools-undistort`` script will then undistort input videos based on the
parameters.
