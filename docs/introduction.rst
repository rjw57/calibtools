Introduction
============

This package is a repository for some useful scripts for performing camera
calibration in Python. It requires the following modules:

* OpenCV's Python bindings
* moviepy
* numpy

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

