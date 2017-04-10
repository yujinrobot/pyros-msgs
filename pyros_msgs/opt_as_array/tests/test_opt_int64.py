from __future__ import absolute_import, division, print_function

import os

try:
    import rospy  # just checking if ROS environment has been sourced
except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import rospy  # just checking if ROS environment has been sourced

# TODO : find a better place for this ?
from pyros_msgs.typecheck.ros_genmsg_py import import_msgsrv

# a dynamically generated message type just for testing...
test_opt_int64_as_array = import_msgsrv(
    os.path.join(os.path.dirname(__file__), 'msg', 'test_opt_int64_as_array.msg'),
)

import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(test_opt_int64_as_array, ['data'])

import pytest
import hypothesis
import hypothesis.strategies

from pyros_msgs.typecheck import six_long


@hypothesis.given(hypothesis.strategies.lists(hypothesis.strategies.integers(min_value=six_long(-9223372036854775808), max_value=six_long(9223372036854775807)), max_size=1))
def test_init_rosdata(data):
    msg = test_opt_int64_as_array(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.integers(min_value=six_long(-9223372036854775808), max_value=six_long(9223372036854775807)))
def test_init_data(data):
    msg = test_opt_int64_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(hypothesis.strategies.integers(min_value=six_long(-9223372036854775808), max_value=six_long(9223372036854775807)))
def test_init_raw(data):
    msg = test_opt_int64_as_array(data)
    assert msg.data == [data]


def test_init_default():
    msg = test_opt_int64_as_array()
    assert msg.data == []


# TODO : all possible (from ros_mappings) except proper integers
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.integers(max_value=six_long(-9223372036854775808)-1),
    hypothesis.strategies.integers(min_value=six_long(9223372036854775807)+1),
    hypothesis.strategies.floats(),
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with pytest.raises(AttributeError) as cm:
        test_opt_int64_as_array(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.value.message

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
