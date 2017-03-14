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

from .typechecker import (
    maybe_list,
    maybe_tuple,
    maybe_set,
    Accepter, Sanitizer, Array, Any, MinMax, CodePoint,
    TypeCheckerException,
    TypeChecker,
)

from .ros_mappings import (
    typechecker_from_rosfield_type,
)


__all__ = [
]
