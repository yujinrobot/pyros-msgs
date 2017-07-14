from __future__ import absolute_import, division, print_function

import os
import sys


import genpy
import site

site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps'))

import rosimport
rosimport.activate()

from . import msg as test_gen_msgs


import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(test_gen_msgs.test_opt_duration_as_array, ['data'])

import pytest
import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.lists(
    hypothesis.strategies.builds(
        genpy.Duration,
        secs=hypothesis.strategies.one_of(
            hypothesis.strategies.integers(min_value=-2147483648 +3, max_value=2147483647 -2),
            hypothesis.strategies.sampled_from([-2147483648 +3, 2147483647 -2])
        ),
        nsecs=hypothesis.strategies.one_of(
            hypothesis.strategies.integers(min_value=-2147483648, max_value=2147483647),
            hypothesis.strategies.sampled_from([-2147483648, 2147483647])
        )
    ), max_size=1
))
def test_init_rosdata(data):
    msg = test_gen_msgs.test_opt_duration_as_array(data=data)
    assert msg.data == data



@hypothesis.given(
    hypothesis.strategies.builds(
        genpy.Duration,
        secs=hypothesis.strategies.one_of(
            hypothesis.strategies.integers(min_value=-2147483648 + 3, max_value=2147483647 - 2),
            hypothesis.strategies.sampled_from([-2147483648 +3, 2147483647 -2])
        ),
        nsecs=hypothesis.strategies.one_of(
            hypothesis.strategies.integers(min_value=-2147483648, max_value=2147483647),
            hypothesis.strategies.sampled_from([-2147483648, 2147483647])
        )
    )
)
def test_init_data(data):
    msg = test_gen_msgs.test_opt_duration_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(
    hypothesis.strategies.builds(
        genpy.Duration,
        secs=hypothesis.strategies.one_of(
            hypothesis.strategies.integers(min_value=-2147483648 + 3, max_value=2147483647 - 2),
            hypothesis.strategies.sampled_from([-2147483648 +3, 2147483647 -2])
        ),
        nsecs=hypothesis.strategies.one_of(
            hypothesis.strategies.integers(min_value=-2147483648, max_value=2147483647),
            hypothesis.strategies.sampled_from([-2147483648, 2147483647])
        )
    )
)
def test_init_raw(data):
    msg = test_gen_msgs.test_opt_duration_as_array(data)
    assert msg.data == [data]


def test_init_default():
    msg = test_gen_msgs.test_opt_duration_as_array()
    assert msg.data == []

# TODO : test_wrong_init_except(data) check typecheck.tests.test_ros_mappings

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
