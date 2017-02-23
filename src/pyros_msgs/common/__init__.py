from __future__ import absolute_import, division, print_function
"""
this pacakge determine mappings between ros native types and yros optional types.
It is extensively documented and tested.

you are encourages to run doctest on it :
py.test --pyargs pyros_msgs.common --doctest-modules
"""

from .mappings import (
    six_long,
    maybe_list,
    maybe_tuple,

    # use functions instead
    # ros_python_basic_field_type_mapping,
    # ros_python_default_mapping,
    get_accepted_from_type,
    get_generated_from_type,
    get_default_val_from_type,

    ros_opt_as_array_type_str_mapping,
    ros_opt_as_array_type_constructor_mapping,
    ros_opt_as_array_type_default_mapping,

    ros_opt_as_nested_type_str_mapping,
    ros_opt_as_nested_type_constructor_mapping,
    ros_opt_as_nested_type_default_mapping,

)

from .validation import validate_type

__all__ = [
    'ros_python_basic_field_type_mapping',
    'ros_python_default_mapping',

    'ros_opt_as_array_type_str_mapping',
    'ros_opt_as_array_type_constructor_mapping',
    'ros_opt_as_array_type_default_mapping',

    'ros_opt_as_nested_type_str_mapping',
    'ros_opt_as_nested_type_constructor_mapping',
    'ros_opt_as_nested_type_default_mapping',

    'validate_type',
]
