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

from hypothesis import given, example, assume, settings, Verbosity, HealthCheck
import hypothesis.strategies as st

# Defining a strategy for our typeschemas.
# This can also be understood as a spec of our TypeSchemas to map to ROS message types
# IE : these are the rules to build a typeschema


from . import bool_type_checker, proper_basic_strategy_selector, bad_basic_strategy_selector


@given(proper_basic_strategy_selector(bool_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=0.1, suppress_health_check=[HealthCheck.too_slow])
def test_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert bool_type_checker(value) == value


@given(bad_basic_strategy_selector(bool_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_breaks_on_bad_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        bool_type_checker(value)
    assert "is not accepted by Accepter from <type 'bool'>" in excinfo.value.message
