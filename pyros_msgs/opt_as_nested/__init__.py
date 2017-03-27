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

from .opt_as_nested import duck_punch

__all__ = [
    'duck_punch',
]