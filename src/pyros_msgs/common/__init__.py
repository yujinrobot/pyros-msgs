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
    maybe_set,
    time_type_factory, time_type_recycler,
    duration_type_factory, duration_type_recycler,
    TypeSchema,
)

from .ros_mappings import (
    typeschema_from_rosfield_type,
    typeschema_from_rosmsg_type
)


__all__ = [
]
