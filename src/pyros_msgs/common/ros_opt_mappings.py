from __future__ import absolute_import, division, print_function

import collections
from pprint import pprint
import six
# to get long for py2 and int for py3
six_long = six.integer_types[-1]

from collections import Iterable, Mapping, OrderedDict

try:
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import genpy

from pyros_msgs.common import (
    six_long,
    maybe_tuple,
    maybe_list,
)

# Mapping between accepted ros types, and generated typeschema
# The generated typeschema should match optional rostype typeschema
ros_opt_as_array_field_type_mapping = {
    'bool[]': (('bool', 'bool[]'), [bool]),  # a bool[] can represent an optional bool or an optional bool[]
    'int8[]': (('int8', 'int8[]'), [int]),
    'int16[]': (('int16', 'int16[]'), [int]),
    'int32[]': (('int32', 'int32[]'), [int]),
    'int64[]': (('int64', 'int64[]'), [six_long]),
    'uint8[]': (('uint8', 'uint8[]'), [int]),
    'uint16[]': (('uint16', 'uint16[]'), [int]),
    'uint32[]': (('uint32', 'uint32[]'), [int]),
    'uint64[]': (('uint64', 'uint64[]'), [six_long]),
    'float32[]': (('float32', 'float32[]'), [float]),
    'float64[]': (('float64', 'float64[]'), [float]),
    'string[]': (('string', 'string[]'), [str]),
    'time[]': (('time', 'time[]'), [genpy.Time]),
    'duration[]': (('duration', 'duration[]'), [genpy.Duration]),
}


def get_accepted_typeschema_from_opt_array_type(opt_type):
    """
    Get a tuple representing the possible accepted types for this optional type
    :param opt_type: the optional type
    :return: the tuple of accepted types

    >>> get_accepted_typeschema_from_opt_array_type('int8[]')
    (<type 'int'>, [<type 'int'>])

    >>> get_accepted_typeschema_from_opt_array_type('int64[]')
    (<type 'int'>, <type 'long'>, [(<type 'int'>, <type 'long'>)])
    """
    # we get the matching ros_type we are making optional
    ros_types = ros_opt_as_array_field_type_mapping[opt_type][0]  # will except if opt_type is not as expected
    # we retrieve the accepted type from the optional rostype
    accepted_types = [get_accepted_typeschema_from_type(rt) for rt in ros_types]
    # we flatten the list of accepted types
    return tuple(t for et in accepted_types for t in et)


def get_generated_typeschema_from_opt_array_type(opt_type):
    # we get the matching ros_type we are making optional
    gen_typeschema = ros_opt_as_array_field_type_mapping[opt_type][1]  # will except if opt_type is not as expected
    # We have only one optional generated type
    return gen_typeschema  # will except if opt_type is not as expected


# Here we can use the default base type value
def get_default_val_from_opt_array_type(opt_type):
    # We have one optional type and it is already under the ros format
    return get_default_val_from_type(opt_type)


# NESTED :
# We need to redefine mappings here and not reuse the basic methods directly

ros_opt_as_nested_field_type_mapping = {
    'pyros_msgs/opt_bool': ('bool',  {'data': bool}),  # a pyros_msgs/opt_bool can only represent an optional bool
    'pyros_msgs/opt_int8': ('int8', ),
    'pyros_msgs/opt_int16': ('int16', ),
    'pyros_msgs/opt_int32': ('int32', ),
    'pyros_msgs/opt_int64': ('int64', ),
    'pyros_msgs/opt_uint8': ('uint8', ),
    'pyros_msgs/opt_uint16': ('uint16', ),
    'pyros_msgs/opt_uint32': ('uint32', ),
    'pyros_msgs/opt_uint64': ('uint64', ),
    'pyros_msgs/opt_float32': ('float32', ),
    'pyros_msgs/opt_float64': ('float64', ),
    'pyros_msgs/opt_string': ('string', ),
    'pyros_msgs/opt_time': ('time', ),
    'pyros_msgs/opt_duration': ('duration', ),
    'pyros_msgs/opt_bool[]': ('bool', 'bool[]', ),
    'pyros_msgs/opt_int8[]': ('int8[]', ),
    'pyros_msgs/opt_int16[]': ('int16[]', ),
    'pyros_msgs/opt_int32[]': ('int32[]', ),
    'pyros_msgs/opt_int64[]': ('int64[]', ),
    'pyros_msgs/opt_uint8[]': ('uint8[]', ),
    'pyros_msgs/opt_uint16[]': ('uint16[]', ),
    'pyros_msgs/opt_uint32[]': ('uint32[]', ),
    'pyros_msgs/opt_uint64[]': ('uint64[]', ),
    'pyros_msgs/opt_float32[]': ('float32[]', ),
    'pyros_msgs/opt_float64[]': ('float64[]', ),
    'pyros_msgs/opt_string[]': ('string[]', ),
    'pyros_msgs/opt_time[]': ('time[]', ),
    'pyros_msgs/opt_duration[]': ('duration[]', ),
}


def get_accepted_typeschema_from_opt_nested_type(opt_type):
    # we get the matching ros_type we are making optional
    ros_types = ros_opt_as_nested_field_type_mapping[opt_type][0]  # will except if opt_type is not as expected
    # we retrieve the accepted type from the optional rostype
    accepted_types = [get_accepted_typeschema_from_type(rt) for rt in ros_types]
    # we flatten the list of accepted types
    return tuple(t for et in accepted_types for t in et)


def get_generated_typeschema_from_opt_nested_type(opt_type):
    # we get the matching ros_type we are making optional
    gen_typeschema = ros_opt_as_nested_field_type_mapping[opt_type][1]  # will except if opt_type is not as expected
    # We have only one optional generated type
    return gen_typeschema  # will except if opt_type is not as expected


ros_opt_as_nested_default_mapping = {
    'pyros_msgs/opt_bool': False,
    'pyros_msgs/opt_int8': 0,
    'pyros_msgs/opt_int16': 0,
    'pyros_msgs/opt_int32': 0,
    'pyros_msgs/opt_int64': six_long(0),
    'pyros_msgs/opt_uint8': 0,
    'pyros_msgs/opt_uint16': 0,
    'pyros_msgs/opt_uint32': 0,
    'pyros_msgs/opt_uint64': six_long(0),
    'pyros_msgs/opt_float32': 0.0,
    'pyros_msgs/opt_float64': 0.0,
    'pyros_msgs/opt_string': '',
    'pyros_msgs/opt_time': 0,
    'pyros_msgs/opt_duration': 0,
    'pyros_msgs/opt_bool[]': [False],
    'pyros_msgs/opt_int8[]': [0],
    'pyros_msgs/opt_int16[]': [0],
    'pyros_msgs/opt_int32[]': [0],
    'pyros_msgs/opt_int64[]': [six_long(0)],
    'pyros_msgs/opt_uint8[]': [0],
    'pyros_msgs/opt_uint16[]': [0],
    'pyros_msgs/opt_uint32[]': [0],
    'pyros_msgs/opt_uint64[]': [six_long(0)],
    'pyros_msgs/opt_float32[]': [0.0],
    'pyros_msgs/opt_float64[]': [0.0],
    'pyros_msgs/opt_string[]': [''],
    'pyros_msgs/opt_time[]': [0],
    'pyros_msgs/opt_duration[]': [0],
}


def get_default_val_from_opt_nested_type(opt_type):
    return ros_opt_as_nested_default_mapping[opt_type]








