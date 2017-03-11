from __future__ import absolute_import, division, print_function, unicode_literals


"""
This module defines ros mappings and  strategies for testing (covering ros use case only).
It can be read as a specification of the current package.
"""

try:
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import genpy


import six

from pyros_msgs.common import (
    six_long,
    Accepter, Sanitizer, Array, Any,
    TypeChecker,
    maybe_tuple,
    maybe_set,
)


# Ref : http://wiki.ros.org/msg
rosfield_typechecker = {
    # (generated(1), accepted(n)) tuples
    'bool': TypeChecker(Sanitizer(bool), Accepter(bool)),
    'int8': TypeChecker(Sanitizer(int), Accepter(int)),
    'int16': TypeChecker(Sanitizer(int), Accepter(int)),
    'int32': TypeChecker(Sanitizer(int), Accepter(int)),
    'int64': TypeChecker(Sanitizer(six_long), Accepter({int, six_long})),
    'uint8': TypeChecker(Sanitizer(int), Accepter(int)),
    'uint16': TypeChecker(Sanitizer(int), Accepter(int)),
    'uint32': TypeChecker(Sanitizer(int), Accepter(int)),
    'uint64': TypeChecker(Sanitizer(six_long), Accepter({int, six_long})),
    'float32': TypeChecker(Sanitizer(float), Accepter(float)),
    'float64': TypeChecker(Sanitizer(float), Accepter(float)),
    # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    'string': TypeChecker(Sanitizer(six.binary_type), Any(Accepter(six.binary_type), Accepter(six.text_type))),
    # for time and duration we want to extract the slots
    # we want genpy to get the list of slots (rospy.Time doesnt have it)
    'time': TypeChecker(Sanitizer(genpy.Time), Accepter(genpy.Time)),
    'duration': TypeChecker(Sanitizer(genpy.Duration), Accepter(genpy.Duration)),
}
# TODO : add predicates to be able to differentiate int sizes...


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
    elif slot_type.endswith('[]'):  # we cannot avoid having this here since we can add '[]' to a custom message type
        # we need to recurse...
        typechecker = typechecker_from_rosfield_type(rosfield_typechecker[:-2])
        return TypeChecker(
            Array(typechecker.sanitizer),
            Array(typechecker.accepter)
        )
    else:  # custom message type
        rosmsg_type = genpy.message.get_message_class(slot_type)
        # we also need to recurse on slot_types
        slots = {
            s: typechecker_from_rosfield_type(st)
            for s, st in zip(rosmsg_type.__slots__, rosmsg_type._slot_types)
        }

        # this init function set all attributes (slots) from arguments (resolved types)
        def internal_type_init(self, **ks):
            for k, s in ks.items():
                setattr(self, k, s)

        # we dynamically create our class/type with slots to leverage existing type checking mechanisms
        sanitized_msgtype = type(rosmsg_type.__name__ + "_type", (), {
            '__slots__': rosmsg_type.__slots__,
            '__init__': internal_type_init
        })
        sanitized_msgtype_instance = sanitized_msgtype(**slots)

        return TypeChecker(Sanitizer(rosmsg_type), Accepter(slots))


class RosMsgTypeAccepter(Accepter):
    def __init__(self, t):
        if hasattr(t, '__slots__'):  # composed type with slots (ros msg type structure)
            # we need to recurse on slot_types
            slots = {
                s: typechecker_from_rosfield_type(st)
                for s, st in zip(t.__slots__, t._slot_types)
                }
        # in other cases nothing is needed, we use basic accepter logic
        super(RosMsgTypeAccepter, self).__init__(t)


class RosMsgTypeSanitizer(Sanitizer):
    def __init__(self, t):
        if hasattr(t, '__slots__'):  # composed type with slots (ros msg type structure)
            # we need to recurse on slot_types
            slots = {
                s: typechecker_from_rosfield_type(st)
                for s, st in zip(t.__slots__, t._slot_types)
                }

            # this init function set all attributes (slots) from arguments (resolved types)
            def internal_type_init(self, **ks):
                for k, s in ks.items():
                    setattr(self, k, s)

            # we dynamically create our class/type with slots to leverage existing type checking mechanisms
            sanitized_msgtype = type(t.__name__ + "_typecheck", (), {
                '__slots__': t.__slots__,
                '__init__': internal_type_init
            })
            sanitized_msgtype_instance = sanitized_msgtype(**slots)

        # in other cases, we can let the basic sanitizer handle it
        super(RosMsgTypeSanitizer, self).__init__(t)

    # Special handling of ROS msg structure (objects with __slots__)
    def __call__(self, v=None):
        if hasattr(self.t, '__slots__'):
            return super(RosMsgTypeSanitizer, self).__call__(
                **{s: getattr(self.t, s).sanitizer(getattr(v, s)) for s in v.__slots__}
            )
        else:  # basic type
            return super(RosMsgTypeSanitizer, self).__call__(v)




        if slot_type in rosfield_typechecker:  # basic field type, end of recursion
            # simple type (check genpy.base.is_simple())
            return rosfield_typechecker.get(slot_type)
        elif slot_type.endswith(
                '[]'):  # we cannot avoid having this here since we can add '[]' to a custom message type
            # we need to recurse...
            typechecker = typechecker_from_rosfield_type(rosfield_typechecker[:-2])
            return TypeChecker(
                Array(typechecker.sanitizer),
                Array(typechecker.accepter)
            )
        else:  # custom message type
            rosmsg_type = genpy.message.get_message_class(slot_type)
            # we also need to recurse on slot_types
            slots = {
                s: typechecker_from_rosfield_type(st)
                for s, st in zip(rosmsg_type.__slots__, rosmsg_type._slot_types)
                }

            # this init function set all attributes (slots) from arguments (resolved types)
            def internal_type_init(self, **ks):
                for k, s in ks.items():
                    setattr(self, k, s)

            # we dynamically create our class/type with slots to leverage existing type checking mechanisms
            sanitized_msgtype = type(rosmsg_type.__name__ + "_type", (), {
                '__slots__': rosmsg_type.__slots__,
                '__init__': internal_type_init
            })
            sanitized_msgtype_instance = sanitized_msgtype(**slots)


        super(RosTypeSanitizer, self).__init__(t)



# TODO : common message types :
# - std_msgs/Header
# -
