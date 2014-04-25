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

Installation
````````````

The easiest way to install ``calibtools`` is via ``easy_install`` or ``pip``::

    $ pip install calibtools

If you want to check out the latest in-development version, look at
`the project's GitHub page <https://github.com/rjw57/calibtools>`_. Once checked out,
installation is based on setuptools and follows the usual conventions for a
Python project::

    $ python setup.py install

(Although the `develop` command may be more useful if you intend to perform any
significant modification to the library.)

Further documentation
`````````````````````

There is `more documentation <https://calibtools.readthedocs.org/>`_
available online and you can build your own copy via the Sphinx documentation
system::

    $ python setup.py build_sphinx

Compiled documentation may be found in ``build/docs/html/``.
