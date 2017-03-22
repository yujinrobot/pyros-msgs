from __future__ import absolute_import
from __future__ import print_function


"""
pyros_msgs.opt_as_nested is a module that declares optional fields as a specific message type.

This is useful if you want to express an optional field in a message without any ambiguity.

When importing this module, a set of ros messages will be imported, and duck punched to make default value a "non initialized value"
"""

try:
    import pyros_utils

except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import pyros_utils

# Fixing out __file__ for proper python behavior

# Getting actual filepath (not ros generated init)
# detecting and fixing ROS generated __init__.py behavior when importing this package

ros_exec = pyros_utils.get_ros_executed_file()
if ros_exec:
    __file__ = ros_exec

# Now we can import packages relatively

from .nested import (
    #opt_empty,
    opt_bool,
    opt_int8,
    opt_int16,
    opt_int32,
    opt_int64,
    opt_uint8,
    opt_uint16,
    opt_uint32,
    opt_uint64,
    opt_float32,
    opt_string,
    opt_time,
    opt_duration,
    opt_header,
)


from .opt_as_nested import duck_punch

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

    'duck_punch',
]