from __future__ import absolute_import, division, print_function
"""
this pacakge determine mappings between ros native types and yros optional types.
It is extensively documented and tested.

you are encourages to run doctest on it :
py.test --pyargs pyros_msgs.common --doctest-modules
"""

# compat

import six
# to get long for py2 and int for py3
six_long = six.integer_types[-1]

from .typeschemas import (
    TypeSchemaException,
    maybe_list,
    maybe_tuple,
    TypeSchema,
)

from .ros_mappings import (
    typeschema_from_rosfield_type,
    typeschema_from_rosmsg_type
)

from .ros_opt_mappings import (
    get_accepted_typeschema_from_opt_array_type,
    get_generated_typeschema_from_opt_array_type,
    get_default_val_from_opt_array_type,

    get_accepted_typeschema_from_opt_nested_type,
    get_generated_typeschema_from_opt_nested_type,
    get_default_val_from_opt_nested_type,
)

from .validation import validate_type

__all__ = [
]
