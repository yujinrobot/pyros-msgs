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
    get_accepted_from_type,
    get_generated_from_type,
)


def is_type_match(accepted_type_tuple, value):
    """
    Determining if a value matches any of the type in the accepted_type_tuple
    :param accepted_type_tuple: a tuple of accepted types. Can contain basic types, list or dict.
    :param value: the value to test the type
    :return: True if the value is acceptable, False otherwise

    >>> is_type_match(bool, True)
    True
    >>> is_type_match(bool, [True])
    False
    >>> is_type_match(bool, [True, False])
    False
    >>> is_type_match([bool], True)
    False
    >>> is_type_match([bool], [False])
    True
    >>> is_type_match([bool], [False, True])
    True
    >>> is_type_match(int, 42)
    True
    >>> is_type_match([int], [42])
    True
    >>> is_type_match([int], [42, 23])
    True
    >>> is_type_match([six_long], six_long(42))
    False
    >>> is_type_match([int], [six_long(42)])
    False
    >>> is_type_match([(int, six_long)], [42, six_long(42)])
    True
    """
    match_any = False
    for at in maybe_tuple(accepted_type_tuple):  # iterating on the tuple of accepted types
        if isinstance(at, list):  # a list denotes we also want a list, but we should check inside...
            match_all = isinstance(value, list)  # better be strict here
            if match_all:
                for ve in value:
                    # we should have only one accepted element type tuple
                    assert len(at) == 1, "BUG : {at} has more than one element".format(**locals())
                    match_all = match_all and is_type_match(at[0], ve)
            match_any = match_any or match_all
        # not dict in ROs messagse
        # elif isinstance(at, dict):  # a dict denotes we also want a dict, but we should check inside...
        #     match_all = isinstance(value, dict)  # better be strict here
        #     if match_all:
        #         for vk, ve in value.items():
        #             for aelemtype in [aet for avk, aet in at.items() if avk == vk]:  # we ned to mathc key by key
        #                 match_all = match_all and is_type_match(aelemtype, ve)
        #     match_any = match_any or match_all
        else:  # basic type
            match_any = match_any or isinstance(value, at)
    return match_any


def sanitize_type(generated_type, value):
    """
    Determining if a value matches any of the type in the accepted_type_tuple
    :param accepted_type_tuple: a tuple of accepted types. Can contain basic types, list or dict.
    :param value: the value to test the type
    :return: True if the value is acceptable, False otherwise

    >>> sanitize_type(bool, True)
    True
    >>> sanitize_type(int, 42)
    42
    >>> sanitize_type([int], 42)
    [42]
    >>> sanitize_type(int, [42])
    Traceback (most recent call last):
    ...
    TypeError: int() argument must be a string or a number, not 'list'
    >>> sanitize_type([int], [42])
    [42]
    >>> sanitize_type(six_long, 42)
    42L
    >>> sanitize_type(int, 42L)
    42
    """

    if isinstance(generated_type, list):  # a list denotes we also generate a list, but we should check inside...
        assert len(generated_type) == 1  # we should have only one
        value = [sanitize_type(generated_type[0], v) for v in maybe_list(value)]
    # elif isinstance(generated_type, dict):  # a dict denotes we also want a dict, but we should check inside...
    #     value = [sanitize_type(generated_type[0], v) for v in maybe_dict(value)]  # we should have only one generated type
    else:  # basic type
        value = generated_type(value)  # casting the value

    return value




    #
    #
    #
    # if slot_type in [v[0] for v in ros_python_basic_field_type_mapping.items()]:
    #
    #
    # # Attempt conversion using basic type constructor
    #     slot_value = ros_python_basic_field_type_mapping.get(slot_type)[1](slot_value)
    #
    # elif slot_type in optional_type_constructor_mappings:
    #     # Attempt conversion using optional type constructor
    #     slot_value = optional_type_constructor_mappings.get(slot_type)(slot_value)
    #
    # elif slot_type.endswith("[]"):
    #     if isinstance(slot_value, collections.Iterable) and not isinstance(slot_value, six.string_types):
    #         # we validate each element (a field can be optional or can also be a normal ros field)
    #         slot_value = [validate_type(s, slot_type[:-2]) for s in slot_value]
    #     else:  # an array type which is not an array. lets attempt element validation
    #         slot_value = validate_type(slot_value, slot_type[:-2])
    #
    # # other cases should all be valid cases (we rely on the other message for their own type validation)
    # else:
    #     # custom field type
    #     try:
    #         msg_class = genpy.message.get_message_class(slot_type)
    #     except:
    #         raise TypeError("message class for '{slot_type}' not found".format(**locals()))
    #     if not isinstance(slot_value, msg_class):
    #         raise TypeError("value '{slot_value}' is not of type {msg_class}".format(**locals()))


def validate_type(slot_value, slot_type, optional_type_constructor_mappings=None):
    """
    Validate the type of the value for ROS, and modify the slot dict on the fly
    to enfore the expected type for ROS.

    Meaningful Examples :
    >>> validate_type(42, 'int8')
    42
    >>> validate_type(42, 'int64')
    42L
    >>> validate_type(r'fortytwo', 'string')
    'fortytwo'
    >>> validate_type(u'fortytwo', 'string')
    'fortytwo'

    With optional fields :


    TODO : Time, Duration, etc.
    """

    # Default is to not accept any optional type.
    optional_type_constructor_mappings = optional_type_constructor_mappings or []

    # In every case, we want to enforce proper ros types (arrays included), since rospy doesn't...
    acceptable = get_accepted_from_type(slot_type)
    if is_type_match(acceptable, slot_value):
        slot_value = sanitize_type(get_generated_from_type(slot_type), slot_value)
    else:
        # break properly
        raise TypeError("value '{slot_value}' is not of an acceptable type {acceptable}".format(**locals()))
    #

    return slot_value
