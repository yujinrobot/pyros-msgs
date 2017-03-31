from __future__ import absolute_import, division, print_function, unicode_literals

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

# Defining a strategy for our typeschemas.
# This can also be understood as a spec of our TypeSchemas to map to ROS message types
# IE : these are the rules to build a typeschema


# # class to represent a composed type. TODO : dynamic generation with strategies
# class Custom(object):
#
#     def __init__(self, d1=0, d2=''):
#         self.d1 = d1; self.d2 = d2
#
#     def __repr__(self):
#         return "d1:{d1} d2:{d2}".format(d1=self.d1, d2=self.d2)
#
#     def __eq__(self, other):
#         return self.d1 == other.d1 and self.d2 == other.d2
#
#
# type_checker = TypeChecker(
#     Sanitizer(
#         lambda c: Custom(d1=c.d1, d2=c.d2) if c else Custom()
#     ), Accepter({
#         'd1': TypeChecker(Sanitizer(int), Accepter(int)),
#         'd2': TypeChecker(Sanitizer(int), Accepter(int))
#     })
# )
#
# strat = st.builds(Custom, d1=st.integers(min_value=0), d2=st.integers(min_value=0))


#
# importing existing test type checkers from test_typechecker_arrays
#

from . import (
    boolarray_type_checker, bool_type_checker,
    intarray_type_checker, integer_type_checker, integer_type_checker_min_max,
    floatarray_type_checker, float_type_checker, float_type_checker_min_max,
    stringarray_type_checker, string_type_checker,

    proper_strategy_selector,
    bad_strategy_selector,
)


# We need to build the custom type and the typechecker from same strategies
custom_fields_tc = st.dictionaries(
    keys=st.text(alphabet=st.characters(max_codepoint=127), min_size=1),  # keys are ascii characters
    values=st.sampled_from([
        boolarray_type_checker, bool_type_checker,
        intarray_type_checker, integer_type_checker, integer_type_checker_min_max,
        floatarray_type_checker, float_type_checker, float_type_checker_min_max,
        stringarray_type_checker, string_type_checker,
    ])
)


def build_instance_strat(fields_dict, strat_selector):
    def custom_init(self, **kwargs):
        self.__slots__ = [k for k in kwargs]
        for k, v in kwargs.items():
            setattr(self, k, v)

    def custom_repr(self):
        repr_str = "CTT: "
        for s in self.__slots__:
            try:
                repr_str += "{s}:{v}".format(s=s, v=getattr(self, s))
            except UnicodeDecodeError:
                repr_str += "{s}:?".format(s=s, v=getattr(self, s))
        return repr_str

    def custom_eq(self, other):
        eq = True
        for k in self.__slots__:
            # Because floats nan and inf are special...
            if isinstance(getattr(self, k), float) and isinstance(getattr(other, k), float):
                eq = eq and (
                  getattr(self, k) == getattr(self, k) or  # use "isclose() type of method instead ?"
                  (math.isnan(getattr(self, k)) and math.isnan(getattr(self, k))) or
                  (math.isinf(getattr(self, k)) and math.isinf(getattr(self, k)))
                )
            else:
                eq = eq and getattr(self, k) == getattr(other, k)
        return eq

    kwargs_init = {k: strat_selector(v) for k, v in fields_dict.items()}

    members_dict = fields_dict.copy()
    members_dict.update({
        '__init__': custom_init,
        '__repr__': custom_repr,
        '__eq__': custom_eq,
    })

    # generating an object from it
    CustomTestType = type(str("CustomTestType"), (), members_dict)

    return CustomTestType, kwargs_init  # instance and initializer args


@st.composite
def build_instance(draw, fields_dict, strat_selector):
    fields = draw(fields_dict)

    cls, init_args = build_instance_strat(fields, strat_selector)

    # Instantiating the class with the arguments
    inst = cls(**{k: draw(s) for k, s in init_args.items()})

    # generating a typechecker for our value
    inst_type_checker = TypeChecker(
        Sanitizer(
            lambda c: cls(**{k: getattr(c, k) for k in fields}) if c else cls()
        ), Accepter({k: v for k, v in fields.items()})
    )

    return inst, inst_type_checker


@given(build_instance(custom_fields_tc, proper_strategy_selector))
@settings(verbosity=Verbosity.verbose, timeout=5)
def test_maintains_equality(inst_type_checker_tuple):
    """
    Verify that value is accepted and the sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert inst_type_checker_tuple[1](inst_type_checker_tuple[0]) == inst_type_checker_tuple[0]


# @given(st.one_of(st.integers(), st.floats(), st.binary()))
# @settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
# def test_breaks_on_bad_values(value):
#     """
#     Verify that value is not accepted
#     """
#     with pytest.raises(TypeCheckerException) as excinfo:
#         type_checker(value)
#     assert "is not accepted by Accepter from <type 'bool'>" in excinfo.value.message
