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
import pytest

from pyros_msgs.common.typechecker import (
    six_long,
    maybe_list,
    maybe_tuple,
    Sanitizer, Accepter, Array, Any, MinMax,
    TypeChecker,
    TypeCheckerException,
)

import math
import sys
from hypothesis import given, example, assume, settings, Verbosity, HealthCheck
import hypothesis.strategies as st

# Defining a strategy for our typeschemas.
# This can also be understood as a spec of our TypeSchemas to map to ROS message types
# IE : these are the rules to build a typeschema

# We sanitize every int to six_long (python3 style)
# We are testing Any accepter operator here
type_checker = TypeChecker(Sanitizer(six_long), Any(Accepter(int), Accepter(six_long)))


@given(st.one_of(st.booleans(), st.integers()))  # where we learn that in python booleans are ints...
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_with_any_accepter_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert type_checker(value) == value


@given(st.one_of(st.floats(), st.binary()))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_with_any_accepter_breaks_on_bad_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        type_checker(value)
    assert "is not accepted by Any of set([Accepter from <type 'int'>, Accepter from <type 'long'>])" in excinfo.value.message


# We also test MinMax accepter operator
min_bound = -42
max_bound = six_long(sys.maxsize + sys.maxsize/2)  # we force a long here (py2)
type_checker_min_max = TypeChecker(Sanitizer(six_long), MinMax(Any(Accepter(int), Accepter(six_long)), min_bound, max_bound))


@given(st.one_of(st.integers(min_value=min_bound, max_value=max_bound)))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_with_minmax_accepter_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert type_checker_min_max(value) == value


@given(st.one_of(st.integers(min_value=max_bound+1), st.integers(max_value=min_bound-1), st.floats(), st.binary()))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_with_minmax_accepter_breaks_on_bad_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        type_checker_min_max(value)
    assert "is not accepted by MinMax [-42..13835058055282163712] of Any of set([Accepter from <type 'int'>, Accepter from <type 'long'>])" in excinfo.value.message
