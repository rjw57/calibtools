from setuptools import setup, find_packages

from calibtools import __version__ as version

setup(
    name = 'calibtools',
    version = version,
    description = 'Camera calibration tools for Python',
    author = 'Rich Wareham',
    author_email = 'rich.calibtools@richwareham.com',
    url = 'https://github.com/rjw57/calibtools/',
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'calibtools-calib = calibtools.calib:start',
            'calibtools-undistort = calibtools.undistort:start',
        ]
    },
    licence = 'MIT',
    install_requires = [
        'moviepy', 'numpy', 'docopt',
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities',
    ],
)
