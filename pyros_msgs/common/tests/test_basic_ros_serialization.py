from __future__ import absolute_import, division, print_function

import numpy
import pytest
from StringIO import StringIO

try:
    import std_msgs.msg as std_msgs
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import std_msgs.msg as std_msgs
    import genpy


from hypothesis import given, example, settings, Verbosity, HealthCheck
import hypothesis.strategies as st


@given(st.builds(std_msgs.Float32, data=st.floats()))
@settings(verbosity=Verbosity.verbose, timeout=10, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_serialize_deserialize_inverse(value):
    """"""

    # sending
    buff = StringIO()
    value.serialize(buff)
    serialized = buff.getvalue()
    buff.close()

    # receiving
    received = std_msgs.Float32()
    received.deserialize(serialized)

    if isinstance(value, (std_msgs.Float32, std_msgs.Float64)):  # for floats, this is only true relative to some epsilon...
        numpy.testing.assert_allclose(received.data, value.data, rtol=1)
    else:
        assert received == value


@given(st.builds(std_msgs.Time, data=st.builds(genpy.Time, secs=st.integers(min_value=0, max_value=4294967295))))
@settings(verbosity=Verbosity.verbose, timeout=10, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_serialize_deserialize_inverse(value):
    """"""

    # sending
    buff = StringIO()
    value.serialize(buff)
    serialized = buff.getvalue()
    buff.close()

    # receiving
    received = std_msgs.Time()
    received.deserialize(serialized)

    assert received == value