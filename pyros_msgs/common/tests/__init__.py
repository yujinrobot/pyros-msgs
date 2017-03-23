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
from hypothesis import given, example, assume, settings, Verbosity
import hypothesis.strategies as st


bool_type_checker = TypeChecker(Sanitizer(bool), Accepter(bool))
boolarray_type_checker = TypeChecker(Array(Sanitizer(bool)), Array(Accepter(bool)))

integer_type_checker = TypeChecker(Sanitizer(six_long), Any(Accepter(int), Accepter(six_long)))
int_min_bound = -42
int_max_bound = six_long(sys.maxsize + sys.maxsize/2)  # we force a long here (py2)
integer_type_checker_min_max = TypeChecker(Sanitizer(six_long), MinMax(Any(Accepter(int), Accepter(six_long)), int_min_bound, int_max_bound))
intarray_type_checker = TypeChecker(Array(Sanitizer(six_long)), Array(MinMax(Any(Accepter(int), Accepter(six_long)), int_min_bound, int_max_bound)))


float_type_checker = TypeChecker(Sanitizer(float), Accepter(float))
float_min_bound = -42.0
float_max_bound = float(sys.maxsize + sys.maxsize/2)  # some big float
float_type_checker_min_max = TypeChecker(Sanitizer(float), MinMax(Accepter(float), float_min_bound, float_max_bound))
floatarray_type_checker = TypeChecker(Array(Sanitizer(float)), Array(MinMax(Accepter(float), float_min_bound, float_max_bound)))


string_type_checker = TypeChecker(Sanitizer(str), Any(Accepter(six.binary_type), CodePoint(Accepter(six.text_type), 0, 127)))
stringarray_type_checker = TypeChecker(Array(Sanitizer(str)), Array(Any(Accepter(six.binary_type), CodePoint(Accepter(six.text_type), 0, 127))))


# Defining good and bad strategies for our typecheckers.

def proper_basic_strategy_selector(type_checker):
    if type_checker is bool_type_checker:
        el_strat = st.booleans()
    elif type_checker is integer_type_checker:
        el_strat = st.integers()
    elif type_checker is integer_type_checker_min_max:
        el_strat = st.integers(min_value=int_min_bound, max_value=int_max_bound)
    elif type_checker is float_type_checker:
        el_strat = st.floats()  # TODO : deal with nan and inf
    elif type_checker is float_type_checker_min_max:
        el_strat = st.floats(min_value=float_min_bound, max_value=float_max_bound)
    elif type_checker is string_type_checker:
        el_strat = st.one_of(st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))
    else:
        raise RuntimeError("Unknown type checker, cannot deduce proper strategy.")
    return el_strat


def proper_list_strategy_selector(type_checker):
    if type_checker is boolarray_type_checker:
        el_strat = st.booleans()
    elif type_checker is intarray_type_checker:
        el_strat = st.integers(min_value=int_min_bound, max_value=int_max_bound)
    elif type_checker is floatarray_type_checker:  # TODO : check how nan and inf behave...
        el_strat = st.floats(min_value=float_min_bound, max_value=float_max_bound)
    elif type_checker is stringarray_type_checker:
        el_strat = st.one_of(st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))
    else:
        raise RuntimeError("Unknown type checker, cannot deduce proper strategy.")
    return st.lists(el_strat)


def bad_basic_strategy_selector(type_checker):  # Note we limit text to ascii to avoid problem with format and printing. use the bad strategy for string to test for this.
    if type_checker is bool_type_checker:
        el_strat = st.one_of(st.integers(), st.floats(), st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))
    elif type_checker is integer_type_checker:
        el_strat = st.one_of(st.floats(), st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))
    elif type_checker is integer_type_checker_min_max:
        el_strat = st.one_of(st.integers(min_value=int_max_bound+1), st.integers(max_value=int_min_bound-1), st.floats(), st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))
    elif type_checker is float_type_checker:
        el_strat = st.one_of(st.integers(), st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))
    elif type_checker is float_type_checker_min_max:
        el_strat = st.one_of(st.integers(), st.binary(), st.text(alphabet=st.characters(max_codepoint=127)))  # st.floats(min_value=numpy.nextafter(max_bound, 1)), st.floats(max_value=numpy.nextafter(min_bound, -1))
    elif type_checker is string_type_checker:
        el_strat = st.one_of(st.booleans(), st.integers(), st.floats(), st.text(alphabet=st.characters(min_codepoint=128), min_size=1))
    else:
        raise RuntimeError("Unknown type checker, cannot deduce bad strategy.")

    return el_strat


def bad_list_strategy_selector(type_checker):
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

    return st.lists(el_strat, min_size=1)  # list of bad values and we force at least one


def proper_strategy_selector(type_checker):
    if type_checker in [
        boolarray_type_checker,
        intarray_type_checker,
        floatarray_type_checker,
        stringarray_type_checker
    ]:
        return proper_list_strategy_selector(type_checker)
    else:
        return proper_basic_strategy_selector(type_checker)


def bad_strategy_selector(type_checker):
    if type_checker in [
        boolarray_type_checker,
        intarray_type_checker,
        floatarray_type_checker,
        stringarray_type_checker
    ]:
        return bad_list_strategy_selector(type_checker)
    else:
        return bad_basic_strategy_selector(type_checker)