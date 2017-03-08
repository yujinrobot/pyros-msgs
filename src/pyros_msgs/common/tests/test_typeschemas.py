from __future__ import absolute_import, division, print_function

try:
    import pyros_msgs
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import pyros_msgs


from pyros_msgs.common.typeschemas import (
    TypeSchemaException,
    maybe_list,
    maybe_tuple,
    TypeSchema,
    sanitized_fields_type_factories,
    accepted_fields_type_recyclers,
    basic_sanitized_fields_type_strategy,
    many_accepted_fields_type_strategy,
)


from hypothesis import given
import hypothesis.strategies as st

# We need a composite strategy to link type and test values
@st.composite
def sanitized_typeschema_and_value(draw, sanitized_type_st=basic_sanitized_fields_type_strategy):
    sanitized_type = draw(sanitized_type_st)
    found = False
    val = None

    for t, strat in sanitized_fields_type_factories:
        if t == sanitized_type:
            found = True
            val = draw(strat)
            break

    assert found, "{sanitized_type} not found in {sanitized_fields_type_factories}".format(
        sanitized_type=sanitized_type,
        sanitized_fields_type_factories=sanitized_fields_type_factories,
    )

    return sanitized_type, val


@given(sanitized_typeschema_and_value())
def test_typeschema_sanitize_equal(sanitized_and_val):
    """
    Verify that sanitized value is "equal" to original value
    This means that sanitization conserve value equality, in the python sense.
    """
    assert TypeSchema.sanitize(sanitized_and_val[0], value=sanitized_and_val[1]) == sanitized_and_val[1]


@st.composite
def accepted_typeschema_and_value(draw, accepted_types=many_accepted_fields_type_strategy):

    found = False
    val = None
    for t, strat in sanitized_fields_type_factories:
        if t in accepted_types:  # careful we can have a set of accepted types
            found = True
            val = draw(strat)
            break

    assert found

    return accepted_types, val


@given(accepted_typeschema_and_value())
def test_typeschema_accept(accepted_types, val):
    """
    Verify that accept returns true for any instance of accepted types.
    """
    assert TypeSchema.accept(accepted_types, value=val)

