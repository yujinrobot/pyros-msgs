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
)



def validate_type(slot_value, slot_type):
    """
    Validate the type of the value for ROS, and modify the slot dict on the fly
    to enforce the expected type for ROS.

    Meaningful Examples :
    >>> validate_type(42, 'int8')
    42
    >>> validate_type(42, 'int64')
    42L
    >>> validate_type(r'fortytwo', 'string')
    'fortytwo'
    >>> validate_type(u'fortytwo', 'string')
    'fortytwo'

    TODO : Time, Duration, etc.
    """

    # In every case, we want to enforce proper ros types (arrays included), since rospy doesn't...
    acceptable = get_accepted_typeschema_from_type(slot_type)
    if is_type_match(acceptable, slot_value):
        slot_value = sanitize(get_generated_typeschema_from_type(slot_type), slot_value)
    else:
        # break properly
        raise TypeError("value '{slot_value}' is not of an acceptable type {acceptable}".format(**locals()))
    #

    return slot_value
