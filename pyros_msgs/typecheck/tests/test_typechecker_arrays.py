from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
import sys

# try:
#     import pyros_msgs
#     import genpy
# except ImportError:
#     import pyros_setup
#     pyros_setup.configurable_import().configure().activate()
#     import pyros_msgs
#     import genpy

import six

from pyros_msgs.typecheck.typechecker import (
    six_long,
    maybe_list,
    maybe_tuple,
    Sanitizer, Accepter, Array, Any, MinMax, CodePoint,
    TypeChecker,
    TypeCheckerException,
)

import math
from hypothesis import given, example, assume, settings, Verbosity
import hypothesis.strategies as st

from . import (
    boolarray_type_checker, bool_type_checker,
    intarray_type_checker, integer_type_checker,
    floatarray_type_checker, float_type_checker,
    stringarray_type_checker, string_type_checker,

    proper_list_strategy_selector,
    proper_basic_strategy_selector,
    bad_basic_strategy_selector,
    bad_list_strategy_selector,
)


@given(proper_list_strategy_selector(boolarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=0.1)
def test_boolarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert boolarray_type_checker(value) == value


@given(st.one_of(
    bad_list_strategy_selector(boolarray_type_checker),  # bad value in list
    proper_basic_strategy_selector(bool_type_checker),  # proper value not in list
    bad_basic_strategy_selector(bool_type_checker),  # just a bad value
))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_boolarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        boolarray_type_checker(value)
    assert "is not accepted by Array of Accepter from <type 'bool'>" in excinfo.value.message


@given(proper_list_strategy_selector(intarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_intarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert intarray_type_checker(value) == value


@given(st.one_of(
    bad_list_strategy_selector(intarray_type_checker),  # bad value in list
    proper_basic_strategy_selector(integer_type_checker),  # proper value not in list
    bad_basic_strategy_selector(integer_type_checker),  # just a bad value
))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_intarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        intarray_type_checker(value)
    assert "is not accepted by Array of MinMax [-42..13835058055282163712] of Any of set" in excinfo.value.message


@given(proper_list_strategy_selector(floatarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_floatarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert floatarray_type_checker(value) == value


@given(st.one_of(
    bad_list_strategy_selector(floatarray_type_checker),  # bad value in list
    proper_basic_strategy_selector(float_type_checker),  # proper value not in list
    bad_basic_strategy_selector(float_type_checker),  # bad value not in list
))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_floatarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        floatarray_type_checker(value)
    assert "is not accepted by Array of MinMax [-42.0..1.38350580553e+19] of Accepter from <type 'float'>" in excinfo.value.message


@given(proper_list_strategy_selector(stringarray_type_checker))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_stringarray_typechecker_maintains_equality(value):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert stringarray_type_checker(value) == value


@given(st.one_of(
    bad_list_strategy_selector(stringarray_type_checker),  # bad value in list
    proper_basic_strategy_selector(string_type_checker),  # proper value not in list
    bad_basic_strategy_selector(string_type_checker),  # bad value not in list
))
@settings(verbosity=Verbosity.verbose, timeout=1)
def test_stringarray_typechecker_breaks_on_bad_number_values(value):
    """
    Verify that value is not accepted
    """
    with pytest.raises(TypeCheckerException) as excinfo:
        stringarray_type_checker(value)
    assert "is not accepted by Array of Any of set" in excinfo.value.message
