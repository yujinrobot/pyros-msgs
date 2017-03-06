from __future__ import absolute_import, division, print_function

import collections
import six

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
    maybe_dict,
    get_accepted_typeschema_from_type,
    get_generated_typeschema_from_type,
    get_accepted_typeschema_from_opt_array_type,
    get_generated_typeschema_from_opt_array_type,
    get_accepted_typeschema_from_opt_nested_type,
    get_generated_typeschema_from_opt_nested_type,
    is_type_match,
    sanitize_type,
    validate_type,
)


def validate_nested_opt_type(slot_value, slot_type):
    """
    Validate the type of the value for the optional field, and modify the slot dict on the fly
    to enforce the expected optional type.
    This function takes care of nested optional fields :
    >>> from pyros_msgs.opt_as_nested import opt_bool
    >>> validate_nested_opt_type(opt_bool(True), 'pyros_msgs/opt_bool')
    initialized_: True
    data: True
    >>> validate_nested_opt_type(True, 'pyros_msgs/opt_bool')
    initialized_: True
    data: True

    >>> validate_nested_opt_type(42, 'pyros_msgs/opt_bool')
    Traceback (most recent call last):
    ...
    TypeError: value '42' is not of an acceptable type (<type 'bool'>, <class 'pyros_msgs.msg._opt_bool.opt_bool'>)
    >>> validate_nested_opt_type(opt_bool(42), 'pyros_msgs/opt_bool')
    Traceback (most recent call last):


    TODO : Time, Duration, etc.
    """

    acceptable = get_accepted_typeschema_from_opt_nested_type(slot_type)
    if is_type_match(acceptable, slot_value):
        slot_value = sanitize_type(get_generated_typeschema_from_opt_nested_type(slot_type), slot_value)
    # simplifying transitive nesting # TODO : check is it a good idea or not ?
    elif is_type_match(get_accepted_typeschema_from_type(slot_type), slot_value):
        slot_value = sanitize_type(get_generated_typeschema_from_type(slot_type), slot_value)
    else:
        # break properly
        raise TypeError("value '{slot_value}' is not of an acceptable type {acceptable}".format(**locals()))
    #

    return slot_value


def validate_array_opt_type(slot_value, slot_type):
    """
    Validate the type of the value for the optional field, and modify the slot dict on the fly
    to enforce the expected optional type.
    This function takes care of array optional fields :
    >>> validate_array_opt_type([True], 'bool[]')
    [True]
    >>> validate_array_opt_type(True, 'bool[]')
    [True]

    >>> validate_array_opt_type(42, 'bool[]')
    Traceback (most recent call last):
    ...
    TypeError: value '42' is not of an acceptable type (<type 'bool'>, [<type 'bool'>])

    >>> validate_array_opt_type([42], 'bool[]')
    Traceback (most recent call last):
    ...
    TypeError: value '[42]' is not of an acceptable type (<type 'bool'>, [<type 'bool'>])

    TODO : Time, Duration, etc.
    """

    acceptable = get_accepted_typeschema_from_opt_array_type(slot_type)
    if is_type_match(acceptable, slot_value):
        slot_value = sanitize_type(get_generated_typeschema_from_opt_array_type(slot_type), slot_value)
    else:
        # break properly
        raise TypeError("value '{slot_value}' is not of an acceptable type {acceptable}".format(**locals()))
    #

    return slot_value