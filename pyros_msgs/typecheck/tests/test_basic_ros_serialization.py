from __future__ import absolute_import, division, print_function

import numpy
import pytest
from StringIO import StringIO


import os
import sys

from pyros_msgs.importer.rosmsg_generator import MsgDependencyNotFound, generate_msgsrv_nspkg, import_msgsrv

try:
    # First we try to import from environment
    import std_msgs.msg as std_msgs

except ImportError:
    # If we cannot import messages from environment (happens in isolated python usecase) we can try to generate them
    std_msgs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps', 'std_msgs', 'msg')
    flist = os.listdir(std_msgs_dir)
    generated_modules = generate_msgsrv_nspkg(
        [os.path.join(std_msgs_dir, f) for f in flist],
        package='std_msgs',
        dependencies=['std_msgs'],
        include_path=['std_msgs:{0}'.format(std_msgs_dir)],
       ns_pkg=True
    )
    import_msgsrv('std_msgs.msg')
    std_msgs = sys.modules['std_msgs.msg']

import genpy

from hypothesis import given, example, settings, Verbosity
import hypothesis.strategies as st


@given(st.builds(std_msgs.Float32, data=st.floats(min_value=-3.4028235e+38, max_value=3.4028235e+38)))  # limits for IEEE 754 binary32 floats
@settings(verbosity=Verbosity.verbose, timeout=10)
def test_typechecker_serialize_deserialize_float32_inverse(value):
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
@settings(verbosity=Verbosity.verbose, timeout=10)
def test_typechecker_serialize_deserialize_time_inverse(value):
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

