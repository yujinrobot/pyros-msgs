from __future__ import absolute_import
from __future__ import print_function

# Getting all msgs first (since our __file__ is set to ros generated __init__)
from .msg import *

# duck punching via module import relay
from ._punch import (
    opt_empty,

    opt_bool,
    opt_int8, opt_int16, opt_int32, opt_int64,
    opt_uint8, opt_uint16, opt_uint32, opt_uint64,
    opt_float32, opt_float64,
    opt_string,

    opt_time,
    opt_duration,
    opt_header,
)

# fixing out __file__ for proper python behavior

# Getting actual filepath (not ros generated init)
# detecting and fixing ROS generated __init__.py behavior when importing this package
# TMP : not working yet...
# import pyros_utils
#
# ros_exec = pyros_utils.get_ros_executed_file()
# if ros_exec:
#     __file__ = ros_exec


__all__ = [
    'opt_empty',

    'opt_bool',
    'opt_int8', 'opt_int16', 'opt_int32', 'opt_int64',
    'opt_uint8', 'opt_uint16', 'opt_uint32', 'opt_uint64',
    'opt_float32', 'opt_float64',
    'opt_string',

    'opt_time',
    'opt_duration',
    'opt_header',
]

