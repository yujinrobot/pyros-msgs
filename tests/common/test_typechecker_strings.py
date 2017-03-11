from __future__ import absolute_import, division, print_function, unicode_literals

try:
    import pyros_msgs
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import pyros_msgs
    import genpy

import six

from pyros_msgs.common.typechecker import (
    six_long,
    maybe_list,
    maybe_tuple,
    Sanitizer, Accepter, Array, Any, MinMax, CodePoint,
    TypeChecker,
    TypeCheckerException,
)

import pytest
import math
from hypothesis import given, example, assume, settings, Verbosity, HealthCheck
import hypothesis.strategies as st

# Defining a strategy for our typeschemas.
# This can also be understood as a spec of our TypeSchemas to map to ROS message types
# IE : these are the rules to build a typeschema

# We sanitize every int to six_long (python3 style)
# We are testing Any accepter operator here
type_checker = TypeChecker(Sanitizer(str), Any(Accepter(six.binary_type), CodePoint(Accepter(six.text_type), 0, 127)))


@given(st.one_of(st.binary(), st.text(alphabet=st.characters(
    # we match ascii here
    min_codepoint=0,
    max_codepoint=127,
))))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert type_checker(value) == value


@given(st.one_of(st.booleans(), st.integers(), st.floats()))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        type_checker(value)
    assert "is not accepted by Any of set([CodePoint [0..127] of Accepter from <type 'unicode'>, Accepter from <type 'str'>])" in excinfo.value.message


# Separate test for unicode fanciness
@given(st.text(alphabet=st.characters(min_codepoint=128), min_size=1))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_breaks_on_bad_text_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
         type_checker(value)
    assert "is not accepted by Any of set([CodePoint [0..127] of Accepter from <type 'unicode'>, Accepter from <type 'str'>])" in excinfo.value.message
