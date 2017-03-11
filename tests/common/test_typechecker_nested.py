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
    Sanitizer, Accepter, Array, Any, TypeMinMax,
    TypeChecker,
    TypeCheckerException,
)

import math
from hypothesis import given, example, assume, settings, Verbosity, HealthCheck
import hypothesis.strategies as st

# Defining a strategy for our typeschemas.
# This can also be understood as a spec of our TypeSchemas to map to ROS message types
# IE : these are the rules to build a typeschema


# class to represent a composed type. TODO : dynamic generation with strategies
class Custom(object):

    def __init__(self, d1=0, d2=''):
        self.d1 = d1; self.d2 = d2

    def __repr__(self):
        return "d1:{d1} d2:{d2}".format(d1=self.d1, d2=self.d2)

    def __eq__(self, other):
        return self.d1 == other.d1 and self.d2 == other.d2


type_checker = TypeChecker(
    Sanitizer(
        lambda c: Custom(d1=c.d1, d2=c.d2) if c else Custom()
    ), Accepter({
        'd1': TypeChecker(Sanitizer(int), Accepter(int)),
        'd2': TypeChecker(Sanitizer(int), Accepter(int))
    })
)

strat = st.builds(Custom, d1=st.integers(min_value=0), d2=st.integers(min_value=0))

@given(strat)
@settings(verbosity=Verbosity.verbose, timeout=0.01, suppress_health_check=[HealthCheck.too_slow])
def test_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert type_checker(value) == value


@given(st.one_of(st.integers(), st.floats(), st.binary()))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_breaks_on_bad_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        type_checker(value)
    assert "is not accepted by Accepter from <type 'bool'>" in excinfo.value.message
