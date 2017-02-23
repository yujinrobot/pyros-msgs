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


def maybe_list(l):
    """Return list of one element if ``l`` is a scalar."""
    return l if l is None or isinstance(l, list) else [l]


def maybe_tuple(t):
    """Return tuple one element if ``t`` is a scalar."""
    return t if t is None or isinstance(t, tuple) else (t,)


# Just to make sure we dont forget anything
all_ros_field_types = [
'bool', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
'float32', 'float64', 'string', 'time', 'duration',
'bool[]', 'int8[]', 'int16[]', 'int32[]', 'int64[]', 'uint8[]', 'uint16[]', 'uint32[]', 'uint64[]',
'float32[]', 'float64[]', 'string[]', 'time[]', 'duration[]',
]


# Ref : http://wiki.ros.org/msg
ros_python_basic_field_type_mapping = {
    # (accepted(n), generated(1)) tuples
    'bool': (bool, bool),
    'int8': (int, int), 'int16': (int, int), 'int32': (int, int), 'int64': ((int, six_long), six_long),
    'uint8': (int, int), 'uint16': (int, int), 'uint32': (int, int), 'uint64': ((int, six_long), six_long),
    'float32': (float, float), 'float64': (float, float),
    'string': ((six.binary_type, six.text_type), six.binary_type),  # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    'time': (genpy.rostime.Time, genpy.rostime.Time),  # we want genpy to get the list of slots (rospy.Time doesnt have it)
    'duration': (genpy.rostime.Duration, genpy.rostime.Duration),  # we want genpy to get the list of slots (rospy.Duration doesnt have it)
}


def get_accepted_from_type(slot_type):
    """
    Retrieves an actual type tuple based on the ros type string
    :param slot_type: the ros type string
    :return: the tuple of accepted types for that type

    Reference :
    >>> pprint({ t: get_accepted_from_type(t) for t in all_ros_field_types })
    {'bool': <type 'bool'>,
     'bool[]': [<type 'bool'>],
     'duration': <class 'genpy.rostime.Duration'>,
     'duration[]': [<class 'genpy.rostime.Duration'>],
     'float32': <type 'float'>,
     'float32[]': [<type 'float'>],
     'float64': <type 'float'>,
     'float64[]': [<type 'float'>],
     'int16': <type 'int'>,
     'int16[]': [<type 'int'>],
     'int32': <type 'int'>,
     'int32[]': [<type 'int'>],
     'int64': (<type 'int'>, <type 'long'>),
     'int64[]': [(<type 'int'>, <type 'long'>)],
     'int8': <type 'int'>,
     'int8[]': [<type 'int'>],
     'string': (<type 'str'>, <type 'unicode'>),
     'string[]': [(<type 'str'>, <type 'unicode'>)],
     'time': <class 'genpy.rostime.Time'>,
     'time[]': [<class 'genpy.rostime.Time'>],
     'uint16': <type 'int'>,
     'uint16[]': [<type 'int'>],
     'uint32': <type 'int'>,
     'uint32[]': [<type 'int'>],
     'uint64': (<type 'int'>, <type 'long'>),
     'uint64[]': [(<type 'int'>, <type 'long'>)],
     'uint8': <type 'int'>,
     'uint8[]': [<type 'int'>]}
    """
    if slot_type in ros_python_default_mapping:
        # simple type (check genpy.base.is_simple())
        return maybe_tuple(ros_python_basic_field_type_mapping.get(slot_type)[0])
    elif slot_type.endswith('[]'):
        # array type (recurse)
        return maybe_tuple([get_accepted_from_type(slot_type[:-2])])
    else:
        # attempt custom type (call __init__())
        return maybe_tuple(genpy.message.get_message_class(slot_type))


def get_generated_from_type(slot_type):
    """
    Retrieves an actual type tuple based on the ros type string
    :param slot_type: the ros type string
    :return: the tuple of accepted types for that type

    Reference :
    >>> pprint({ t: get_generated_from_type(t) for t in all_ros_field_types })
    {'bool': <type 'bool'>,
     'bool[]': [<type 'bool'>],
     'duration': <class 'genpy.rostime.Duration'>,
     'duration[]': [<class 'genpy.rostime.Duration'>],
     'float32': <type 'float'>,
     'float32[]': [<type 'float'>],
     'float64': <type 'float'>,
     'float64[]': [<type 'float'>],
     'int16': <type 'int'>,
     'int16[]': [<type 'int'>],
     'int32': <type 'int'>,
     'int32[]': [<type 'int'>],
     'int64': <type 'long'>,
     'int64[]': [<type 'long'>],
     'int8': <type 'int'>,
     'int8[]': [<type 'int'>],
     'string': <type 'str'>,
     'string[]': [<type 'str'>],
     'time': <class 'genpy.rostime.Time'>,
     'time[]': [<class 'genpy.rostime.Time'>],
     'uint16': <type 'int'>,
     'uint16[]': [<type 'int'>],
     'uint32': <type 'int'>,
     'uint32[]': [<type 'int'>],
     'uint64': <type 'long'>,
     'uint64[]': [<type 'long'>],
     'uint8': <type 'int'>,
     'uint8[]': [<type 'int'>]}

    """
    if slot_type in ros_python_default_mapping:
        # simple type (check genpy.base.is_simple())
        return ros_python_basic_field_type_mapping.get(slot_type)[1]
    elif slot_type.endswith('[]'):
        # array type (recurse)
        return [get_generated_from_type(slot_type[:-2])]
    else:
        # attempt custom type (call __init__())
        return genpy.message.get_message_class(slot_type)


ros_python_default_mapping = {
    'bool': False,
    'int8': 0, 'int16': 0, 'int32': 0, 'int64': six_long(0),
    'uint8': 0, 'uint16': 0, 'uint32': 0, 'uint64': six_long(0),
    'float32': 0.0, 'float64': 0.0,
    'string': '',
    'time': 0,
    'duration': 0,
}


def get_default_val_from_type(slot_type):
    """
    Retrieves a default value based on the ros type string
    :param slot_type: trhe ros type string
    :return: default value for that type

    Reference :
    >>> pprint({ t: get_default_val_from_type(t) for t in all_ros_field_types })
    {'bool': False,
     'bool[]': [False],
     'duration': 0,
     'duration[]': [0],
     'float32': 0.0,
     'float32[]': [0.0],
     'float64': 0.0,
     'float64[]': [0.0],
     'int16': 0,
     'int16[]': [0],
     'int32': 0,
     'int32[]': [0],
     'int64': 0L,
     'int64[]': [0L],
     'int8': 0,
     'int8[]': [0],
     'string': '',
     'string[]': [''],
     'time': 0,
     'time[]': [0],
     'uint16': 0,
     'uint16[]': [0],
     'uint32': 0,
     'uint32[]': [0],
     'uint64': 0L,
     'uint64[]': [0L],
     'uint8': 0,
     'uint8[]': [0]}

    """
    if slot_type in ros_python_default_mapping:
        # simple type (check genpy.base.is_simple())
        return ros_python_default_mapping.get(slot_type)
    elif slot_type.endswith('[]'):
        # array type (recurse)
        return [get_default_val_from_type(slot_type[:-2])]
    else:
        # attempt custom type (call __init__())
        return genpy.message.get_message_class(slot_type)()


# BOTH as array and as nested together (to avoid repetition)
ros_opt_type_str_mapping = {
    'bool': ('bool[]', 'pyros_msgs/opt_bool'),
    'int8': ('int8[]', 'pyros_msgs/opt_int8'), 'int16': ('int16[]', 'pyros_msgs/opt_int16'), 'int32': ('int32[]', 'pyros_msgs/opt_int32'), 'int64': ('int64[]', 'pyros_msgs/opt_int64'),
    'uint8': ('uint8[]', 'pyros_msgs/opt_uint8'), 'uint16': ('uint16[]', 'pyros_msgs/opt_uint16'), 'uint32': ('uint32[]', 'pyros_msgs/opt_uint32'), 'uint64': ('uint64[]', 'pyros_msgs/opt_uint64'),
    'float32': ('float32[]', 'pyros_msgs/opt_float32'), 'float64': ('float64[]', 'pyros_msgs/opt_float64'),
    'string': ('string[]', 'pyros_msgs/opt_string'),
    'time': ('time[]', 'pyros_msgs/opt_time'),
    'duration': ('duration[]', 'pyros_msgs/opt_duration'),
}


# defining all closures here to have a source for lambda and avoid hiding important stuff in runtime...
_type_lambda_closures = {
    'bool':         lambda v: get_generated_from_type('bool')       (v),
    'int8':         lambda v: get_generated_from_type('int8')       (v),
    'int16':        lambda v: get_generated_from_type('int16')      (v),
    'int32':        lambda v: get_generated_from_type('int32')      (v),
    'int64':        lambda v: get_generated_from_type('int64')      (v),
    'uint8':        lambda v: get_generated_from_type('uint8')      (v),
    'uint16':       lambda v: get_generated_from_type('uint16')     (v),
    'uint32':       lambda v: get_generated_from_type('uint32')     (v),
    'uint64':       lambda v: get_generated_from_type('uint64')     (v),
    'float32':      lambda v: get_generated_from_type('float32')    (v),
    'float64':      lambda v: get_generated_from_type('float64')    (v),
    'string':       lambda v: get_generated_from_type('string')     (v),
    'time':         lambda v: get_generated_from_type('time')       (v),
    'duration':     lambda v: get_generated_from_type('duration')   (v),
    'bool[]':       lambda v: get_generated_from_type('bool[]')     (v),
    'int8[]':       lambda v: get_generated_from_type('int8[]')     (v),
    'int16[]':      lambda v: get_generated_from_type('int16[]')    (v),
    'int32[]':      lambda v: get_generated_from_type('int32[]')    (v),
    'int64[]':      lambda v: get_generated_from_type('int64[]')    (v),
    'uint8[]':      lambda v: get_generated_from_type('uint8[]')    (v),
    'uint16[]':     lambda v: get_generated_from_type('uint16[]')   (v),
    'uint32[]':     lambda v: get_generated_from_type('uint32[]')   (v),
    'uint64[]':     lambda v: get_generated_from_type('uint64[]')   (v),
    'float32[]':    lambda v: get_generated_from_type('float32[]')  (v),
    'float64[]':    lambda v: get_generated_from_type('float64[]')  (v),
    'string[]':     lambda v: get_generated_from_type('string[]')   (v),
    'time[]':       lambda v: get_generated_from_type('time[]')     (v),
    'duration[]':   lambda v: get_generated_from_type('duration[]') (v),
}

# FOR ARRAYS
ros_opt_as_array_type_str_mapping = {opt[0]: r for r, opt in ros_opt_type_str_mapping.items()}

# closure needed to avoid variable clash in comprehension
def _as_array_type_lambda_closure(ros_type_str):
    """
    Internal closure to scope variables
    :param ros_type_str: the slot type string
    :return: lambda function as type constructor

    This (private) closure is used to build ros_opt_as_array_type_constructor_mapping :
    >>> import inspect; pprint({ot: inspect.getsource(l) for ot, l in ros_opt_as_array_type_constructor_mapping.items()})
    {'bool[]': "    'bool':         lambda v: get_generated_from_type('bool')       (v),\\n",
     'duration[]': "    'duration':     lambda v: get_generated_from_type('duration')   (v),\\n",
     'float32[]': "    'float32':      lambda v: get_generated_from_type('float32')    (v),\\n",
     'float64[]': "    'float64':      lambda v: get_generated_from_type('float64')    (v),\\n",
     'int16[]': "    'int16':        lambda v: get_generated_from_type('int16')      (v),\\n",
     'int32[]': "    'int32':        lambda v: get_generated_from_type('int32')      (v),\\n",
     'int64[]': "    'int64':        lambda v: get_generated_from_type('int64')      (v),\\n",
     'int8[]': "    'int8':         lambda v: get_generated_from_type('int8')       (v),\\n",
     'string[]': "    'string':       lambda v: get_generated_from_type('string')     (v),\\n",
     'time[]': "    'time':         lambda v: get_generated_from_type('time')       (v),\\n",
     'uint16[]': "    'uint16':       lambda v: get_generated_from_type('uint16')     (v),\\n",
     'uint32[]': "    'uint32':       lambda v: get_generated_from_type('uint32')     (v),\\n",
     'uint64[]': "    'uint64':       lambda v: get_generated_from_type('uint64')     (v),\\n",
     'uint8[]': "    'uint8':        lambda v: get_generated_from_type('uint8')      (v),\\n"}
    """
    # let that function manage the conversion to/from list
    # but trick it to see the source when inspecting
    return _type_lambda_closures.get(ros_type_str)


def _as_array_default_lambda_closure(ros_type_str):
    """
    Internal closure to scope variables
    :param ros_type_str: the slot type string
    :return: lambda function to generate default value

    This (private) closure is used to build ros_opt_as_array_type_default_mapping :
    >>> pprint(ros_opt_as_array_type_default_mapping)
    {'bool[]': [False],
     'duration[]': [0],
     'float32[]': [0.0],
     'float64[]': [0.0],
     'int16[]': [0],
     'int32[]': [0],
     'int64[]': [0L],
     'int8[]': [0],
     'string[]': [''],
     'time[]': [0],
     'uint16[]': [0],
     'uint32[]': [0],
     'uint64[]': [0L],
     'uint8[]': [0]}
    """
    return lambda v: get_default_val_from_type(ros_type_str)(v)  # let that function manage the conversion to/from list


# constructor for optional field is list(slot_type[:-2]()) in all cases
ros_opt_as_array_type_constructor_mapping = {
    opt: (
        _as_array_type_lambda_closure(r)
    ) for opt, r in ros_opt_as_array_type_str_mapping.items()
}
# default for optional field is [] in all cases
ros_opt_as_array_type_default_mapping = {opt: [get_default_val_from_type(r)] for opt, r in ros_opt_as_array_type_str_mapping.items()}


#FOR NESTED
ros_opt_as_nested_type_str_mapping = {opt[1]: r for r, opt in ros_opt_type_str_mapping.items()}


# closure needed to avoid variable clash in comprehension
def _as_nested_type_lambda_closure(ros_type_str):
    """
    Internal closure to scope variables
    :param ros_type_str: the slot type string
    :return: lambda function as type constructor

    This (private) closure is used to build ros_opt_as_nested_type_constructor_mapping :

    >>> pprint(ros_opt_as_nested_type_constructor_mapping)
    {'pyros_msgs/opt_bool': <type 'bool'>,
     'pyros_msgs/opt_duration': <class 'genpy.rostime.Duration'>,
     'pyros_msgs/opt_float32': <type 'float'>,
     'pyros_msgs/opt_float64': <type 'float'>,
     'pyros_msgs/opt_int16': <type 'int'>,
     'pyros_msgs/opt_int32': <type 'int'>,
     'pyros_msgs/opt_int64': <type 'long'>,
     'pyros_msgs/opt_int8': <type 'int'>,
     'pyros_msgs/opt_string': <type 'str'>,
     'pyros_msgs/opt_time': <class 'genpy.rostime.Time'>,
     'pyros_msgs/opt_uint16': <type 'int'>,
     'pyros_msgs/opt_uint32': <type 'int'>,
     'pyros_msgs/opt_uint64': <type 'long'>,
     'pyros_msgs/opt_uint8': <type 'int'>}
    """
    return lambda v: get_generated_from_type(ros_type_str)(v)  # let that function manage the conversion to/from list

def _as_nested_default_lambda_closure(ros_type_str):
    """
    Internal closure to scope variables
    :param ros_type_str: the slot type string
    :return: lambda function to generate default value

    This (private) closure is used to build ros_opt_as_nested_type_default_mapping :

    >>> pprint(ros_opt_as_nested_type_default_mapping)
    {'pyros_msgs/opt_bool': False,
     'pyros_msgs/opt_duration': 0,
     'pyros_msgs/opt_float32': 0.0,
     'pyros_msgs/opt_float64': 0.0,
     'pyros_msgs/opt_int16': 0,
     'pyros_msgs/opt_int32': 0,
     'pyros_msgs/opt_int64': 0L,
     'pyros_msgs/opt_int8': 0,
     'pyros_msgs/opt_string': '',
     'pyros_msgs/opt_time': 0,
     'pyros_msgs/opt_uint16': 0,
     'pyros_msgs/opt_uint32': 0,
     'pyros_msgs/opt_uint64': 0L,
     'pyros_msgs/opt_uint8': 0}
    """
    return lambda v: get_default_val_from_type(ros_type_str)(v)  # let that function manage the conversion to/from list


# constructor for optional field is the ros constructor in all cases
ros_opt_as_nested_type_constructor_mapping = {opt: get_generated_from_type(r) for opt, r in ros_opt_as_nested_type_str_mapping.items()}
# default for optional field is the ros default in all cases
ros_opt_as_nested_type_default_mapping = {opt: get_default_val_from_type(r) for opt, r in ros_opt_as_nested_type_str_mapping.items()}



# TODO : common message types :
# - std_msgs/Header
# -
