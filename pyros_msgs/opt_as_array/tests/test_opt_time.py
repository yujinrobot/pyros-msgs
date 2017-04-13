from __future__ import absolute_import, division, print_function

import os
import sys

import genpy


# generating all and accessing the required message class.
from pyros_msgs.opt_as_array.tests import msg_generate
gen_test_msgs = msg_generate.generate_test_msgs()


import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(gen_test_msgs.test_opt_time_as_array, ['data'])

import pytest
import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.lists(
    hypothesis.strategies.builds(
        genpy.Time,
        secs=hypothesis.strategies.integers(min_value=0, max_value=4294967295 -3),
        nsecs=hypothesis.strategies.integers(min_value=0, max_value=4294967295)
    ), max_size=1
))
def test_init_rosdata(data):
    msg = gen_test_msgs.test_opt_time_as_array(data=data)
    assert msg.data == data


@hypothesis.given(
    hypothesis.strategies.builds(
        genpy.Time,
        secs=hypothesis.strategies.integers(min_value=0, max_value=4294967295 -3),
        nsecs=hypothesis.strategies.integers(min_value=0, max_value=4294967295)
    )
)
def test_init_data(data):
    msg = gen_test_msgs.test_opt_time_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(
    hypothesis.strategies.builds(
        genpy.Time,
        secs=hypothesis.strategies.integers(min_value=0, max_value=4294967295 -3),
        nsecs=hypothesis.strategies.integers(min_value=0, max_value=4294967295)
    )
)
def test_init_raw(data):
    msg = gen_test_msgs.test_opt_time_as_array(data)
    assert msg.data == [data]


def test_init_default():
    msg = gen_test_msgs.test_opt_time_as_array()
    assert msg.data == []


# TODO : test_wrong_init_except(data) check typecheck.tests.test_ros_mappings

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
