from __future__ import absolute_import, division, print_function

import numpy
import six


# generating all and accessing the required message class.
from pyros_msgs.typecheck.tests import msg_generate

try:
    # This should succeed if the message class was already generated
    import std_msgs.msg as std_msgs
except ImportError:  # we should enter here if the message was not generated yet.
    std_msgs, std_srvs = msg_generate.generate_std_msgs()

import genpy

from hypothesis import given, example, settings, Verbosity
import hypothesis.strategies as st


@given(st.builds(std_msgs.Float32, data=st.floats(min_value=-3.4028235e+38, max_value=3.4028235e+38)))  # limits for IEEE 754 binary32 floats
@settings(verbosity=Verbosity.verbose, timeout=10)
def test_typechecker_serialize_deserialize_float32_inverse(value):
    """"""

    # sending
    buff = six.StringIO()
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
@settings(verbosity=Verbosity.verbose, timeout=10)
def test_typechecker_serialize_deserialize_time_inverse(value):
    """"""

    # sending
    buff = six.StringIO()
    value.serialize(buff)
    serialized = buff.getvalue()
    buff.close()

    # receiving
    received = std_msgs.Time()
    received.deserialize(serialized)

    assert received == value

