from __future__ import absolute_import, division, print_function


import os
import sys
import numpy
from six import BytesIO

import site

site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps'))

import rosimport
rosimport.activate()

# This should succeed if the message class was already generated
import std_msgs.msg as std_msgs

import genpy

from hypothesis import given, example, settings, Verbosity
import hypothesis.strategies as st


@given(st.builds(std_msgs.Float32, data=st.floats(min_value=-3.4028235e+38, max_value=3.4028235e+38)))  # limits for IEEE 754 binary32 floats
@settings(verbosity=Verbosity.verbose, timeout=10)
def test_typechecker_serialize_deserialize_float32_inverse(value):
    """"""

    # sending
    buff = BytesIO()
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
    buff = BytesIO()
    value.serialize(buff)
    serialized = buff.getvalue()
    buff.close()

    # receiving
    received = std_msgs.Time()
    received.deserialize(serialized)

    assert received == value

