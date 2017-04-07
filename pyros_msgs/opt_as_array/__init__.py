from __future__ import absolute_import, division, print_function

"""
pyros_msgs.opt_as_array is a module that interprets arrays as optional fields in a message.

This is useful if you have an existing ros message type, and want to allow some field to not have any defined value :
An empty array will represent that

When importing this module, the ros message field default value for array will be changed to an empty array.
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

from .opt_as_array import duck_punch


# # Importing here the messages to patch them, so they can be used by someone else already patched
# from pyros_msgs.msg import (
#     test_opt_bool_as_array,
#     test_opt_int8_as_array,
#     test_opt_int16_as_array,
#     test_opt_int32_as_array,
#     test_opt_int64_as_array,
#     test_opt_uint8_as_array,
#     test_opt_uint16_as_array,
#     test_opt_uint32_as_array,
#     test_opt_uint64_as_array,
#     test_opt_float32_as_array,
#     test_opt_float64_as_array,
#     test_opt_string_as_array,
#     test_opt_time_as_array,
#     test_opt_duration_as_array,
# )
#
# # patching (need to know the field name)
# duck_punch(test_opt_bool_as_array, ['data'])
# duck_punch(test_opt_int8_as_array, ['data'])
# duck_punch(test_opt_int16_as_array, ['data'])
# duck_punch(test_opt_int32_as_array, ['data'])
# duck_punch(test_opt_int64_as_array, ['data'])
# duck_punch(test_opt_uint8_as_array, ['data'])
# duck_punch(test_opt_uint16_as_array, ['data'])
# duck_punch(test_opt_uint32_as_array, ['data'])
# duck_punch(test_opt_uint64_as_array, ['data'])
# duck_punch(test_opt_float32_as_array, ['data'])
# duck_punch(test_opt_float64_as_array, ['data'])
# duck_punch(test_opt_string_as_array, ['data'])
# duck_punch(test_opt_time_as_array, ['data'])
# duck_punch(test_opt_duration_as_array, ['data'])