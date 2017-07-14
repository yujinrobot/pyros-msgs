from __future__ import absolute_import, division, print_function

# TODO : check all types
import genpy
import pytest

from . import msg as test_gen_msgs


import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(test_gen_msgs.test_opt_duration_as_nested, ['data'])

import hypothesis
import hypothesis.strategies


@hypothesis.given(
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
    ))
def test_init_rosdata(data):
    msg = test_gen_msgs.test_opt_duration_as_nested(data=data)
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
    msg = test_gen_msgs.test_opt_duration_as_nested(data=data)
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
def test_init_raw(data):
    msg = test_gen_msgs.test_opt_duration_as_nested(data)
    assert msg.data == data


def test_init_default():
    msg = test_gen_msgs.test_opt_duration_as_nested()
    assert msg.data == None

# TODO : test_wrong_init_except(data) check typecheck.tests.test_ros_mappings

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
