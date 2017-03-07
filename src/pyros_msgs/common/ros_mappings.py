from __future__ import absolute_import, division, print_function

import six

try:
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import genpy


from pyros_msgs.common import six_long, TypeSchema, maybe_tuple


# Ref : http://wiki.ros.org/msg
rosfield_schematype_mapping = {
    # (generated(1), accepted(n)) tuples
    'bool': TypeSchema(bool, bool),
    'int8': TypeSchema(int, int),
    'int16': TypeSchema(int, int),
    'int32': TypeSchema(int, int),
    'int64': TypeSchema(six_long, (int, six_long)),
    'uint8': TypeSchema(int, int),
    'uint16': TypeSchema(int, int),
    'uint32': TypeSchema(int, int),
    'uint64': TypeSchema(six_long, (int, six_long)),
    'float32': TypeSchema(float, float),
    'float64': TypeSchema(float, float),
    # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    'string': TypeSchema(six.binary_type, (six.binary_type, six.text_type)),
    # for time and duration we want to extract the slots
    # we want genpy to get the list of slots (rospy.Time doesnt have it)
    'time': TypeSchema(lambda v=genpy.Time(): genpy.Time(secs=v.secs, nsecs=v.nsecs), {'secs': int, 'nsecs': int}),
    'duration': TypeSchema(lambda v=genpy.Duration(): genpy.Duration(secs=v.secs, nsecs=v.nsecs), {'secs': int, 'nsecs': int}),

}
# TODO : add predicates to be able to differentiate int sizes...


def typeschema_from_rosmsg_type(rosmsg_type):
    """
    Generate the typeschema from a ROS message type.

    :param rosmsg_type: the class for the ros message
    :return:

    Reference:
    >>> typeschema_from_rosmsg_type(genpy.Duration)  #doctest: +ELLIPSIS
    (<function <lambda> at 0x...>, ({'secs': <type 'int'>, 'nsecs': <type 'int'>},))

    >>> typeschema_from_rosmsg_type(genpy.Time)  #doctest: +ELLIPSIS
    (<function <lambda> at 0x...>, ({'secs': <type 'int'>, 'nsecs': <type 'int'>},))
    """

    # assert isinstance(rostype, genpy.Message) # TODO : not working ??

    # TODO : is this enough ? or too simple ?

    # Message are equivalent, value per value, but direct copy is not implemented on init...
    typeschema_gen = lambda v=rosmsg_type(): rosmsg_type(**{k: getattr(v, k) for k in rosmsg_type.__slots__})

    typeschema_acc = ({
        s: typeschema_from_rosfield_type(srt).accepted_types
        for s, srt in zip(rosmsg_type.__slots__, rosmsg_type._slot_types)
    }, )

    return TypeSchema(typeschema_gen, typeschema_acc)


def typeschema_from_rosfield_type(slot_type):
    """
    Retrieves an actual type tuple based on the ros type string
    :param slot_type: the ros type string
    :return: the corresponding typeschema
    Reference :
    >>> typeschema_from_rosfield_type('bool')
    (<type 'bool'>, <type 'bool'>)
    >>> typeschema_from_rosfield_type('bool[]')
    ([<type 'bool'>], (<type 'bool'>, [<type 'bool'>]))

    >>> typeschema_from_rosfield_type('int64[]')
    ([<type 'long'>], (<type 'int'>, <type 'long'>, [(<type 'int'>, <type 'long'>)]))

    >>> typeschema_from_rosfield_type('string[]')
    ([<type 'str'>], (<type 'str'>, <type 'unicode'>, [(<type 'str'>, <type 'unicode'>)]))

    >>> typeschema_from_rosfield_type('time')  #doctest: +ELLIPSIS
    (<function <lambda> at 0x...>, {'secs': <type 'int'>, 'nsecs': <type 'int'>})
    >>> typeschema_from_rosfield_type('duration[]')  #doctest: +ELLIPSIS
    ([<function <lambda> at 0x...>], ({'secs': <type 'int'>, 'nsecs': <type 'int'>}, [{'secs': <type 'int'>, 'nsecs': <type 'int'>}]))
    """

    if slot_type in rosfield_schematype_mapping:  # basic field type, end of recursion
        # simple type (check genpy.base.is_simple())
        return rosfield_schematype_mapping.get(slot_type)
    elif slot_type.endswith('[]'):  # we cannot avoid having this here since we can add '[]' to a custom message type
        # for array types we also want to allow raw elements (we will wrap them when sanitizing)
        gen_ts = typeschema_from_rosfield_type(slot_type[:-2]).sanitized_type  # sanitized typeschema
        acc_ts = typeschema_from_rosfield_type(slot_type[:-2]).accepted_types  # accepted typeschema
        return TypeSchema(
            [gen_ts],  # the generated typeschema
            tuple([t for ts in (maybe_tuple(acc_ts), maybe_tuple([acc_ts])) for t in ts])  # the (flatten) accepted typeschema
        )
    else:  # custom message type
        rosmsg_type = genpy.message.get_message_class(slot_type)
        return typeschema_from_rosmsg_type(rosmsg_type)



# TODO : common message types :
# - std_msgs/Header
# -
