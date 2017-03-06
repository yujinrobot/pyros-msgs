from __future__ import absolute_import, division, print_function

from pprint import pprint

import six

try:
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import genpy


from pyros_msgs.common import six_long, typeschema_check, maybe_tuple


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
    # 'bool[]': ([bool], (bool, [bool])),
    # 'int8[]': ([int], (int, [int])),
    # 'int16[]': ([int], (int, [int])),
    # 'int32[]': ([int], (int, [int])),
    # 'int64[]': ([six_long], (int, six_long, [(int, six_long)])),
    # 'uint8[]': ([int], (int, [int])),
    # 'uint16[]': ([int], (int, [int])),
    # 'uint32[]': ([int], (int, [int])),
    # 'uint64[]': ([six_long], (int, six_long, [(int, six_long)])),
    # 'float32[]': ([float], (float, [float])),
    # 'float64[]': ([float], (float, [float])),
    # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    # 'string[]': ([six.binary_type], (six.binary_type, six.text_type, [(six.binary_type, six.text_type)])),
    # for time and duration we want to extract the slots
    # we want genpy to get the list of slots (rospy.Time doesnt have it)
    # 'time[]': ([{'_sanitized': genpy.Time, 'secs': int, 'nsecs': int}], (genpy.Time, [genpy.Time])),
    # 'duration[]': ([{'_sanitized': genpy.Duration, 'secs': int, 'nsecs': int}], (genpy.Duration, [genpy.Duration])),
}
# TODO : add predicates to be able to differentiate int sizes...


def typeschema_from_rostype(slot_type):
    """
    Retrieves an actual type tuple based on the ros type string
    :param slot_type: the ros type string
    :return: the corresponding typeschema
    Reference :
    >>> typeschema_from_rostype('bool')
    (<type 'bool'>, <type 'bool'>)
    >>> typeschema_from_rostype('bool[]')
    ([<type 'bool'>], (<type 'bool'>, [<type 'bool'>]))

    >>> typeschema_from_rostype('int64[]')
    ([<type 'long'>], (<type 'int'>, <type 'long'>, [(<type 'int'>, <type 'long'>)]))

    >>> typeschema_from_rostype('string[]')
    ([<type 'str'>], (<type 'str'>, <type 'unicode'>, [(<type 'str'>, <type 'unicode'>)]))

    >>> typeschema_from_rostype('time')
    ({'secs': <type 'int'>, '_sanitized': <class 'genpy.rostime.Time'>, 'nsecs': <type 'int'>}, <class 'genpy.rostime.Time'>)
    >>> typeschema_from_rostype('duration[]')
    ([{'secs': <type 'int'>, '_sanitized': <class 'genpy.rostime.Duration'>, 'nsecs': <type 'int'>}], (<class 'genpy.rostime.Duration'>, [<class 'genpy.rostime.Duration'>]))
    """

    if slot_type in rosfield_schematype_mapping:  # basic field type, end of recursion
        # simple type (check genpy.base.is_simple())
        return rosfield_schematype_mapping.get(slot_type)
    elif slot_type.endswith('[]'):  # we cannot avoid having this here since we can add '[]' to a custom message type
        # for array types we also want to allow raw elements (we will wrap them when sanitizing)
        gen_ts = typeschema_from_rostype(slot_type[:-2])[0]  # sanitized typeschema
        acc_ts = typeschema_from_rostype(slot_type[:-2])[1]  # accepted typeschema
        return tuple([[gen_ts],  # the generated typeschema
                      tuple([t for ts in (maybe_tuple(acc_ts), maybe_tuple([acc_ts])) for t in ts])  # the (flatten) accepted typeschema
               ])
    else:  # custom message type
        rostype = genpy.message.get_message_class(slot_type)

        # assert isinstance(rostype, genpy.Message) # TODO : not working ??

        # we extract the slots now, to make it explicit in the typeschema
        typeschema_gen = {
            s: typeschema_from_rostype(st)[0]
            for s, st in zip(rostype.__slots__, rostype._slot_types)
        }

        typeschema_gen.update({'_sanitized': rostype})

        typeschema_acc = (rostype, )

        return (typeschema_gen, typeschema_acc)


# TODO : common message types :
# - std_msgs/Header
# -
