from __future__ import absolute_import, division, print_function

from pprint import pprint

import six

from pyros_msgs.common import six_long, typeschema_check, maybe_tuple

try:
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import genpy


# Just to make sure we dont forget anything
# TODO : get rid of this
all_ros_field_types = [
'bool', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
'float32', 'float64', 'string', 'time', 'duration',
'bool[]', 'int8[]', 'int16[]', 'int32[]', 'int64[]', 'uint8[]', 'uint16[]', 'uint32[]', 'uint64[]',
'float32[]', 'float64[]', 'string[]', 'time[]', 'duration[]',
]


# Ref : http://wiki.ros.org/msg
rosfield_schematype_mapping = {
    # (generated(1), accepted(n)) tuples
    'bool': (bool, bool),
    'int8': (int, int),
    'int16': (int, int),
    'int32': (int, int),
    'int64': (six_long, (int, six_long)),
    'uint8': (int, int),
    'uint16': (int, int),
    'uint32': (int, int),
    'uint64': (six_long, (int, six_long)),
    'float32': (float, float),
    'float64': (float, float),
    # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    'string': (six.binary_type, (six.binary_type, six.text_type)),
    # for time and duration we want to extract the slots
    # we want genpy to get the list of slots (rospy.Time doesnt have it)
    'time': ({'_sanitized': genpy.Time, 'secs': int, 'nsecs': int}, genpy.Time),
    'duration': ({'_sanitized': genpy.Duration, 'secs': int, 'nsecs': int}, genpy.Duration),

    # For Arrays we also want to allow one raw element.
    'bool[]': ([bool], (bool, [bool])),
    'int8[]': ([int], (int, [int])),
    'int16[]': ([int], (int, [int])),
    'int32[]': ([int], (int, [int])),
    'int64[]': ([six_long], (int, six_long, [(int, six_long)])),
    'uint8[]': ([int], (int, [int])),
    'uint16[]': ([int], (int, [int])),
    'uint32[]': ([int], (int, [int])),
    'uint64[]': ([six_long], (int, six_long, [(int, six_long)])),
    'float32[]': ([float], (float, [float])),
    'float64[]': ([float], (float, [float])),
    # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    'string[]': ([six.binary_type], (six.binary_type, six.text_type, [(six.binary_type, six.text_type)])),
    # for time and duration we want to extract the slots
    # we want genpy to get the list of slots (rospy.Time doesnt have it)
    'time[]': ([{'_sanitized': genpy.Time, 'secs': int, 'nsecs': int}], (genpy.Time, [genpy.Time])),
    'duration[]': ([{'_sanitized': genpy.Duration, 'secs': int, 'nsecs': int}], (genpy.Duration, [genpy.Duration])),
}
# TODO : add predicates to be able to differentiate int sizes...


def typeschema_from_rostype(slot_type):
    """
    Retrieves an actual type tuple based on the ros type string
    :param slot_type: the ros type string
    :return: the corresponding typeschema
    Reference :
    >>> typeschema_from_rostype('bool')
    (<type 'bool'>,)
    >>> typeschema_from_rostype('bool[]')
    ([<type 'bool'>],)

    >>> typeschema_from_rostype('time')
    (genpy.rostime.Time, genpy.rostime.Time)

    """

    if slot_type in rosfield_schematype_mapping:  # basic field type, end of recursion
        # simple type (check genpy.base.is_simple())
        return rosfield_schematype_mapping.get(slot_type)
    else:  # custom message type
        rostype = genpy.message.get_message_class(slot_type)
        # For safety
        assert isinstance(rostype, genpy.Message)

        typeschema = {
            slot: typeschema_from_rostype(slot_type)
            for slot, slot_type in zip(rostype.__slots__, rostype._slot_types)
        }

        return typeschema


# TODO : common message types :
# - std_msgs/Header
# -
