#!/usr/bin/env python

from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

# fetch values from package.xml
setup_args = generate_distutils_setup(
    packages=[
        'pyros_msgs',
        'pyros_msgs.schema',
    ],
    package_dir={
        'pyros_msgs': 'src/pyros_msgs'
    },
)

setup(**setup_args)
