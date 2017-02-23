from __future__ import absolute_import
from __future__ import print_function


"""
pyros_msgs.opt_as_nested is a module that declares optional fields as a specific message type.

This is useful if you want to express an optional field in a message without any ambiguity.

When importing this module, a set of ros messages will be imported, and duck punched to make default value a "non initialized value"
"""

# Getting all msgs first (since our __file__ is set to ros generated __init__)

try:
    from pyros_msgs.msg import *

except ImportError as ie:
    # if pyros_msgs.msg not found, it s likely we are not interpreting this from devel/.
    # importing our generated messages dynamically, using namespace packages (same as genpy generated __init__.py).
    # Ref : http://stackoverflow.com/a/27586272/4006172
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
    # TODO : put this in pyros-setup, catkin_pip, pyros_utils, depending on what seems the better fit...
    # Note that this requires sys.path to already be setup.
    # It is a second step for ROS packages, after PYTHONPATH configuration...
    from pyros_msgs.msg import *

# Fixing out __file__ for proper python behavior
import pyros_utils

# Getting actual filepath (not ros generated init)
# detecting and fixing ROS generated __init__.py behavior when importing this package

ros_exec = pyros_utils.get_ros_executed_file()
if ros_exec:
    __file__ = ros_exec

# Now we can import packages relatively

from .nested import (
    opt_empty,
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