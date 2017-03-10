from __future__ import absolute_import, division, print_function

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
    Sanitizer, Accepter, Array, Any,
    TypeChecker,
    TypeCheckerException,
)


from hypothesis import given, example, settings, Verbosity, HealthCheck
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

sanitized_fields_type_sanitizers = [
    (Sanitizer(bool), st.booleans()),  # ROS bool field
    (Sanitizer(int), st.integers()),  # ROS int8, int16, int32, uint8, uint16, uint32
    (Sanitizer(six_long), st.integers()),  # ROS int64, uint64
    (Sanitizer(float), st.floats()),  # ROS float32, float 64
    (Sanitizer(six.binary_type), st.binary()),  # ROS string
    (Sanitizer(
        lambda c: Custom(d1=c.d1, d2=c.d2) if c else Custom()),
        st.builds(Custom, d1=st.integers(min_value=0), d2=st.integers(min_value=0))
    ),  # composed type
]

sanitized_fields_arraytype_sanitizers = [
    (Array(s[0]),  st.lists(elements=s[1], min_size=1, max_size=1))
    for s in sanitized_fields_type_sanitizers
]

accepted_fields_type_accepters = [
    (Accepter(bool), st.booleans()),  # ROS bool field
    (Accepter(int), st.integers()),  # ROS int8, int16, int32, uint8, uint16, uint32
    (Accepter(six_long), st.integers()),  # ROS int64, uint64
    (Accepter(float), st.floats()),  # ROS float32, float 64
    (Any(Accepter(six.binary_type), Accepter(six.text_type)), st.one_of(st.binary(), st.text())),  # ROS string
    (Accepter({
        'd1': TypeChecker(Sanitizer(int), Accepter(int)),
        'd2': TypeChecker(Sanitizer(int), Accepter(int))
    }), st.builds(Custom, d1=st.integers(min_value=0), d2=st.integers(min_value=0))),  # composed type
]

accepted_fields_arraytype_accepters = [
    (Array(s[0]),  st.lists(elements=s[1], min_size=1, max_size=1))
    for s in accepted_fields_type_accepters
]

# TODO : strategies for composed types

# generate a basic strategy for generated types
sanitized_fields_type_strategy = st.sampled_from([f for f in sanitized_fields_type_sanitizers + sanitized_fields_arraytype_sanitizers])

accepted_fields_type_strategy = st.sampled_from([f for f in accepted_fields_type_accepters + accepted_fields_arraytype_accepters])


# We need a composite strategy to link type and test values
@st.composite
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def sanitized_typechecker_and_value(draw, sanitized_type_st=sanitized_fields_type_strategy):
    sanitized_type_and_strat = draw(sanitized_type_st)
    return sanitized_type_and_strat[0], draw(sanitized_type_and_strat[1])


@given(sanitized_typechecker_and_value())
# @example((ArraySanitizer(Sanitizer(bool)), [False]))
# @example((ArraySanitizer(Sanitizer(long)), [230]))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_sanitize_equal(sanitized_and_val):
    """
    Verify that sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert sanitized_and_val[0](sanitized_and_val[1]) == sanitized_and_val[1]


@st.composite
def accepted_typechecker_and_value(draw, accepted_type_st=accepted_fields_type_strategy):
    accepted_type_and_strat = draw(accepted_type_st)
    return accepted_type_and_strat[0], draw(accepted_type_and_strat[1])


@given(accepted_typechecker_and_value())
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_typechecker_accept(accepted_typechecker_and_value):
    """
    Verify that accept returns true for any instance of accepted types.
    """
    assert accepted_typechecker_and_value[0](accepted_typechecker_and_value[1])

