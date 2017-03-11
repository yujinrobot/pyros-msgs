from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
import sys

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

import math
from hypothesis import given, example, assume, settings, Verbosity, HealthCheck
import hypothesis.strategies as st

# Defining a strategy for our typechecker.
# This can also be understood as a spec of our TypeSchemas to map to other types
# IE : these are the rules to build a typechecker

boolarray_type_checker = TypeChecker(Array(Sanitizer(bool)), Array(Accepter(bool)))

int_min_bound = -42
int_max_bound = six_long(sys.maxsize + sys.maxsize/2)  # we force a long here (py2)
intarray_type_checker = TypeChecker(Array(Sanitizer(six_long)), Array(MinMax(Any(Accepter(int), Accepter(six_long)), int_min_bound, int_max_bound)))

# We also test MinMax accepter operator
float_min_bound = -42.0
float_max_bound = float(sys.maxsize + sys.maxsize/2)  # some big float
floatarray_type_checker = TypeChecker(Array(Sanitizer(float)), Array(MinMax(Accepter(float), float_min_bound, float_max_bound)))

stringarray_type_checker = TypeChecker(Array(Sanitizer(str)), Array(Any(Accepter(six.binary_type), CodePoint(Accepter(six.text_type), 0, 127))))


def proper_elem_strategy_selector(type_checker):
    el_strat = None
    if type_checker is boolarray_type_checker:
        el_strat = st.booleans()
    elif type_checker is intarray_type_checker:
        el_strat = st.integers(min_value=int_min_bound, max_value=int_max_bound)
    elif type_checker is floatarray_type_checker:
        el_strat = st.floats(min_value=float_min_bound, max_value=float_max_bound)
    elif type_checker is stringarray_type_checker:
        el_strat = st.one_of(st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))
    else:
        raise RuntimeError("Unknown type checker, cannot deduce proper strategy.")
    return el_strat


def proper_strategy_selector(type_checker):
    return st.lists(proper_elem_strategy_selector(type_checker))


def bad_strategy_selector(type_checker):
    el_strat = None
    if type_checker is boolarray_type_checker:
        el_strat = st.one_of(st.integers(), st.floats(), st.binary(), st.text())
    elif type_checker is intarray_type_checker:
        el_strat = st.one_of(st.integers(min_value=int_max_bound+1), st.integers(max_value=int_min_bound-1), st.floats(), st.binary(), st.text())
    elif type_checker is floatarray_type_checker:
        el_strat = st.one_of(st.integers(), st.binary(), st.text())  # st.floats(min_value=numpy.nextafter(max_bound, 1)), st.floats(max_value=numpy.nextafter(min_bound, -1))
    elif type_checker is stringarray_type_checker:
        el_strat = st.one_of(st.booleans(), st.integers(), st.floats(), st.text(alphabet=st.characters(min_codepoint=128), min_size=1))
    else:
        raise RuntimeError("Unknown type checker, cannot deduce bad strategy.")

    return st.one_of(
        el_strat,  # bad value
        st.lists(el_strat, min_size=1),  # list of bad values and we force at least one
        proper_elem_strategy_selector(type_checker)  # good values but not in list
    )


# TODO : custom type

@given(proper_strategy_selector(boolarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_boolarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert boolarray_type_checker(value) == value


@given(bad_strategy_selector(boolarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_boolarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        boolarray_type_checker(value)
    assert "is not accepted by Array of Accepter from <type 'bool'>" in excinfo.value.message


@given(proper_strategy_selector(intarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_intarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert intarray_type_checker(value) == value


@given(bad_strategy_selector(intarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_intarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        intarray_type_checker(value)
    assert "is not accepted by Array of MinMax [-42..13835058055282163712] of Any of set([Accepter from <type 'int'>, Accepter from <type 'long'>])" in excinfo.value.message


@given(proper_strategy_selector(floatarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_floatarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert floatarray_type_checker(value) == value


@given(bad_strategy_selector(floatarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_floatarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        floatarray_type_checker(value)
    assert "is not accepted by Array of MinMax [-42.0..1.38350580553e+19] of Accepter from <type 'float'>" in excinfo.value.message


@given(proper_strategy_selector(stringarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_stringarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert stringarray_type_checker(value) == value


@given(bad_strategy_selector(stringarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_stringarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        stringarray_type_checker(value)
    assert "is not accepted by Array of Any of set([Accepter from <type 'str'>, CodePoint [0..127] of Accepter from <type 'unicode'>])" in excinfo.value.message
