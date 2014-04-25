Camera calibration toolbox for Python
=====================================

.. image:: https://pypip.in/license/calibtools/badge.png
    :target: https://pypi.python.org/pypi/calibtools/
    :alt: License

.. image:: https://pypip.in/v/calibtools/badge.png
    :target: https://pypi.python.org/pypi/calibtools/
    :alt: Latest Version

.. image:: https://pypip.in/d/calibtools/badge.png
    :target: https://pypi.python.org/pypi//calibtools/
    :alt: Downloads

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
