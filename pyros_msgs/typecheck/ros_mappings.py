from __future__ import absolute_import, division, print_function, unicode_literals


"""
This module defines ros mappings and  strategies for testing (covering ros use case only).
It can be read as a specification of the current package.
"""


import six

from pyros_msgs.typecheck import (
    six_long,
    Accepter, Sanitizer, Array, Any, MinMax, CodePoint,
    TypeChecker,
)


# Ref : http://wiki.ros.org/msg
rosfield_typechecker = {
    # (generated(1), accepted(n)) tuples
    'bool': TypeChecker(Sanitizer(bool), Accepter(bool)),
    # CAREFUL : in python booleans are integers
    # => booleans will be accepted as integers... not sure if we can do anything about this.
    'int8': TypeChecker(Sanitizer(int), MinMax(Accepter(int), -128, 127)),
    'int16': TypeChecker(Sanitizer(int), MinMax(Accepter(int), -32768, 32767)),
    'int32': TypeChecker(Sanitizer(int), MinMax(Accepter(int), -2147483648, 2147483647)),
    'int64': TypeChecker(Sanitizer(six_long), MinMax(Any(Accepter(int), Accepter(six_long)), six_long(-9223372036854775808), six_long(9223372036854775807))),
    'uint8': TypeChecker(Sanitizer(int), MinMax(Accepter(int), 0, 255)),
    'uint16': TypeChecker(Sanitizer(int), MinMax(Accepter(int), 0, 65535)),
    'uint32': TypeChecker(Sanitizer(int), MinMax(Accepter(int), 0, 4294967295)),
    'uint64': TypeChecker(Sanitizer(six_long), MinMax(Any(Accepter(int), Accepter(six_long)), 0, six_long(18446744073709551615))),
    'float32': TypeChecker(Sanitizer(float), MinMax(Accepter(float), -3.4028235e+38, 3.4028235e+38)),
    'float64': TypeChecker(Sanitizer(float), MinMax(Accepter(float), -1.7976931348623157e+308, 1.7976931348623157e+308)),  # we get these values from numpy, maybe we should use numpy (finfo, iinfo) directly here?
    # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    'string': TypeChecker(Sanitizer(six.binary_type), Any(Accepter(six.binary_type), CodePoint(Accepter(six.text_type), min_cp=0, max_cp=127))),
}


def typechecker_from_rosfield_type(slot_type):
    """
    Retrieves an actual type tuple based on the ros type string
    :param slot_type: the ros type string
    :return: the corresponding typeschema
    Reference :
    >>> typechecker_from_rosfield_type('bool')
    (<type 'bool'>, <type 'bool'>)
    >>> typechecker_from_rosfield_type('bool[]')
    ([<type 'bool'>], (<type 'bool'>, [<type 'bool'>]))

    >>> typechecker_from_rosfield_type('int64[]')
    ([<type 'long'>], (<type 'int'>, <type 'long'>, [(<type 'int'>, <type 'long'>)]))

    >>> typechecker_from_rosfield_type('string[]')
    ([<type 'str'>], (<type 'str'>, <type 'unicode'>, [(<type 'str'>, <type 'unicode'>)]))

    >>> typechecker_from_rosfield_type('time')  #doctest: +ELLIPSIS
    (<function <lambda> at 0x...>, {'secs': <type 'int'>, 'nsecs': <type 'int'>})
    >>> typechecker_from_rosfield_type('duration[]')  #doctest: +ELLIPSIS
    ([<function <lambda> at 0x...>], ({'secs': <type 'int'>, 'nsecs': <type 'int'>}, [{'secs': <type 'int'>, 'nsecs': <type 'int'>}]))
    """

    if slot_type in rosfield_typechecker:  # basic field type, end of recursion
        # simple type (check genpy.base.is_simple())
        return rosfield_typechecker.get(slot_type)
    elif isinstance(slot_type, six.string_types) and slot_type.endswith('[]'):  # we cannot avoid having this here since we can add '[]' to a custom message type
        # we need to recurse...
        typechecker = typechecker_from_rosfield_type(slot_type[:-2])
        return TypeChecker(
            Array(typechecker.sanitizer),
            Array(typechecker.accepter)
        )
    else:  # custom message type  # TODO confirm instance of genpy.Message ?
        # We accept the message python type, or the ros string description
        if isinstance(slot_type, six.string_types):
            rosmsg_type = genpy.message.get_message_class(slot_type)
        else:
            rosmsg_type = slot_type

        # we need to recurse on slots
        slots = {
            f: typechecker_from_rosfield_type(ft)
            for f, ft in zip(rosmsg_type.__slots__, rosmsg_type._slot_types)
            # TODO : filter special fields ?
        }

        def sanitizer(value=None):  # we do not need default value here, no optional nested
            return rosmsg_type(**{
                k: tc(getattr(value, k)) if value else tc()  # we pass a subvalue to the sanitizer of the member type
                for k, tc in slots.items()
            })
        # TODO : to be able to use this from __init__ in messages types, we need to return only the dictionnary.

        return TypeChecker(Sanitizer(sanitizer), Accepter(slots))

rosfield_typechecker.update({
    # for time and duration we want to extract the slots
    # we want genpy to get the list of slots (rospy.Time doesnt have it)
    # NOTE : slots_types in genpy indicate int32 which is wrong for Time, but correct for Duration
    # Until this is fixed we will treat Time and Duration as "special" like genpy does...
    'time': TypeChecker(
        Sanitizer(lambda v=None:
                  genpy.Time(secs=rosfield_typechecker.get('uint32')(v.secs),
                             nsecs=rosfield_typechecker.get('uint32')(v.nsecs)) if v is not None else genpy.Time()
                  ),
        Accepter({'secs': rosfield_typechecker.get('uint32'),
                  'nsecs': rosfield_typechecker.get('uint32')
                  })
    ),
    'duration': TypeChecker(
        Sanitizer(lambda v=None:
                  genpy.Duration(secs=rosfield_typechecker.get('int32')(v.secs),
                             nsecs=rosfield_typechecker.get('int32')(v.nsecs)) if v is not None else genpy.Duration()
                  ),
        Accepter({'secs': rosfield_typechecker.get('int32'),
                  'nsecs': rosfield_typechecker.get('int32')
                  })
    ),
})



# TODO : common message types :
# - std_msgs/Header
# -
