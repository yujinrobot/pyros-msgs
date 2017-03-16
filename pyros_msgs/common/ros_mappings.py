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
import contracts

from pyros_msgs.common import (
    six_long,
    Accepter, Sanitizer, Array, Any, MinMax, CodePoint,
    TypeChecker,
)


# we can store contract directly in the contracts module (no need for some special structure here)
# TODO : check if the numpy contracts work without numpy... otherwise should we to redefine ? or depend on numpy ?
contracts.new_contract('ros_bool', 'bool')
contracts.new_contract('ros_int8', str('int8'))
contracts.new_contract('ros_int16', str('int16'))
contracts.new_contract('ros_int32', str('int32'))
contracts.new_contract('ros_int64', str('int64'))
contracts.new_contract('ros_uint8', str('uint8'))
contracts.new_contract('ros_uint16', str('uint16'))
contracts.new_contract('ros_uint32', str('uint32'))
contracts.new_contract('ros_uint64', str('uint64'))
contracts.new_contract('ros_float32', str('float32'))
contracts.new_contract('ros_float64', str('float64'))
contracts.new_contract('ros_string', str('str|unicode'))  # TODO : improve that (codepoint)

# Ref : http://wiki.ros.org/msg
rosfield_typechecker = {
    # (generated(1), accepted(n)) tuples
    'bool': TypeChecker('ros_bool', Sanitizer(bool)),
    # CAREFUL : in python booleans are integers
    # => booleans will be accepted as integers... not sure if we can do anything about this.
    'int8': TypeChecker('ros_int8', Sanitizer(int)),
    'int16': TypeChecker('ros_int16', Sanitizer(int)),
    'int32': TypeChecker('ros_int32', Sanitizer(int)),
    'int64': TypeChecker('ros_int64', Sanitizer(six_long)),
    'uint8': TypeChecker('ros_uint8', Sanitizer(int)),
    'uint16': TypeChecker('ros_uint16', Sanitizer(int)),
    'uint32': TypeChecker('ros_uint32', Sanitizer(int)),
    'uint64': TypeChecker('ros_uint64', Sanitizer(six_long)),
    'float32': TypeChecker('ros_float32', Sanitizer(float)),
    'float64': TypeChecker('ros_float64', Sanitizer(float)),
    # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
    'string': TypeChecker('ros_string', Sanitizer(six.binary_type)),
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
            "list(" + typechecker.contract + ")",
            Array(typechecker.sanitizer)
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

        def contract_callable(v):
                all(hasattr(v, s) and slots.get(s).accepter(getattr(v, s)) for s, st in slots.items())

        contract = contracts.new_contract("ros_" + slot_type, contract_callable)

        def sanitizer(value):  # we do not need default value here, no optional nested
            return rosmsg_type(**{
                k: tc(getattr(value, k)) if value else tc()  # we pass a subvalue to the sanitizer of the member type
                for k, tc in slots.items()
            })
        # TODO : to be able to use this from __init__ in messages types, we need to return only the dictionnary.

        return TypeChecker(contract, Sanitizer(sanitizer))

rosfield_typechecker.update({
    # for time and duration we want to extract the slots
    # we want genpy to get the list of slots (rospy.Time doesnt have it)
    'time': typechecker_from_rosfield_type(genpy.Time),
    'duration': typechecker_from_rosfield_type(genpy.Duration),
})



# TODO : common message types :
# - std_msgs/Header
# -
