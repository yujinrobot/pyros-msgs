from __future__ import absolute_import, division, print_function

# TODO : check all types

import os
import sys

try:
    import rospy  # just checking if ROS environment has been sourced
except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import rospy  # just checking if ROS environment has been sourced


# TODO : find a better place for this ?
from pyros_msgs.importer.rosmsg_generator import generate_msgsrv_nspkg, import_msgsrv

# a dynamically generated message type just for testing...
generated_modules = generate_msgsrv_nspkg(
    [os.path.join(os.path.dirname(__file__), 'msg', 'test_opt_bool_as_nested.msg')],
)
for m in generated_modules:
    import_msgsrv(m)

test_opt_bool_as_nested = getattr(sys.modules['gen_msgs.msg._test_opt_bool_as_nested'], 'test_opt_bool_as_nested')


import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(test_opt_bool_as_nested, ['data'])

import pytest


import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.one_of(hypothesis.strategies.none(), hypothesis.strategies.booleans()))
def test_init_none_data(data):
    """Testing that a opt field can get any bool or none"""
    msg = test_opt_bool_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.one_of(hypothesis.strategies.none(), hypothesis.strategies.booleans()))
def test_init_raw(data):
    """Testing storing of data without specifying the field"""
    msg = test_opt_bool_as_nested(data)
    assert msg.data == data


def test_init_default():
    """Testing default value"""
    msg = test_opt_bool_as_nested()
    assert msg.data is None


# TODO : all possible (from ros_mappings) except booleans
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.integers(),
    hypothesis.strategies.floats(),
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with pytest.raises(AttributeError) as cm:
        test_opt_bool_as_nested(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.value.message


# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
