from __future__ import absolute_import, division, print_function

import os
import sys

import genpy
import pytest

# generating all and accessing the required message class.
from pyros_msgs.opt_as_nested.tests import msg_generate

try:
    # This should succeed if the message class was already generated
    import pyros_msgs.msg as pyros_msgs
    import std_msgs.msg as std_msgs
except ImportError:  # we should enter here if the message was not generated yet.
    std_msgs, _ = msg_generate.generate_std_msgs()
    pyros_msgs, _ = msg_generate.generate_pyros_msgs()

try:
    test_gen_msgs, gen_test_srvs = msg_generate.generate_test_msgs()
except Exception as e:
    pytest.raises(e)


import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(test_gen_msgs.test_opt_time_as_nested, ['data'])

import hypothesis
import hypothesis.strategies


@hypothesis.given(
    hypothesis.strategies.builds(
        genpy.Time,
        secs=hypothesis.strategies.integers(min_value=0, max_value=4294967295 -3),
        nsecs=hypothesis.strategies.integers(min_value=0, max_value=4294967295)
    ))
def test_init_rosdata(data):
    msg = test_gen_msgs.test_opt_time_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(
    hypothesis.strategies.builds(
        genpy.Time,
        secs=hypothesis.strategies.integers(min_value=0, max_value=4294967295 -3),
        nsecs=hypothesis.strategies.integers(min_value=0, max_value=4294967295)
    )
)
def test_init_data(data):
    msg = test_gen_msgs.test_opt_time_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(
    hypothesis.strategies.builds(
        genpy.Time,
        secs=hypothesis.strategies.integers(min_value=0, max_value=4294967295 -3),
        nsecs=hypothesis.strategies.integers(min_value=0, max_value=4294967295)
    )
)
def test_init_raw(data):
    msg = test_gen_msgs.test_opt_time_as_nested(data)
    assert msg.data == data


def test_init_default():
    msg = test_gen_msgs.test_opt_time_as_nested()
    assert msg.data == None


# TODO : test_wrong_init_except(data) check typecheck.tests.test_ros_mappings

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
