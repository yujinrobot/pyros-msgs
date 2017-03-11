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
    Sanitizer, Accepter, Array, Any, MinMax,
    TypeChecker,
    TypeCheckerException,
)

import sys
import math
import numpy  # only for nextafter
import pytest
from hypothesis import given, example, assume, settings, Verbosity, HealthCheck
import hypothesis.strategies as st

# Defining a strategy for our typeschemas.
# This can also be understood as a spec of our TypeSchemas to map to ROS message types
# IE : these are the rules to build a typeschema

# We sanitize every int to six_long (python3 style)
# We are testing Any accepter operator here
type_checker = TypeChecker(Sanitizer(float), Accepter(float))


@given(st.one_of(st.floats()))  # where we learn that in python
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assume(not math.isnan(value) and not math.isinf(value))  # because equality doesnt hold for inf and nan
    assert type_checker(value) == value


@given(st.one_of(st.booleans(), st.integers(), st.binary()))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_breaks_on_bad_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        type_checker(value)
    assert "is not accepted by Accepter from <type 'float'>" in excinfo.value.message


# We also test MinMax accepter operator
min_bound = -42.0
max_bound = float(sys.maxsize + sys.maxsize/2)  # some big float
type_checker_min_max = TypeChecker(Sanitizer(float), MinMax(Accepter(float), min_bound, max_bound))


@given(st.one_of(st.floats(min_value=min_bound, max_value=max_bound)))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_with_minmax_accepter_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert type_checker_min_max(value) == value


@given(st.one_of(st.integers(), st.binary()))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_with_minmax_accepter_breaks_on_bad_nonfloat_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        type_checker_min_max(value)
    assert "is not accepted by MinMax [-42.0..1.38350580553e+19] of Accepter from <type 'float'>" in excinfo.value.message


# Separate test because of float arithemtics...
# TODO FIXME
@given(st.one_of(st.floats(min_value=numpy.nextafter(max_bound, 1)), st.floats(max_value=numpy.nextafter(min_bound, -1))))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_with_minmax_accepter_breaks_on_bad_float_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        type_checker_min_max(value)
    assert "is not accepted by MinMax [-42.0..1.38350580553e+19] of Accepter from <type 'float'>" in excinfo.value.message