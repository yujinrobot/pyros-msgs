from __future__ import absolute_import, division, print_function

# TODO : check all types

import os
import sys
import pytest

# generating all and accessing the required message class.
from pyros_msgs.opt_as_nested.tests import msg_generate

try:
    # This should succeed if the message class was already generated
    import pyros_msgs.msg as pyros_msgs
except ImportError:  # we should enter here if the message was not generated yet.
    pyros_msgs = msg_generate.generate_pyros_msgs()

try:
    test_gen_msgs, gen_test_srvs = msg_generate.generate_test_msgs()
except Exception as e:
    pytest.raises(e)

import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(test_gen_msgs.test_opt_uint64_as_nested, ['data'])

import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.integers(min_value=0, max_value=18446744073709551615))
def test_init_rosdata(data):
    """Testing that a proper data is stored as is"""
    msg = test_gen_msgs.test_opt_uint64_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.integers(min_value=0, max_value=18446744073709551615))
def test_init_data(data):
    """Testing that an implicitely convertible data is stored as expected"""
    msg = test_gen_msgs.test_opt_uint64_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.integers(min_value=0, max_value=18446744073709551615))
def test_init_raw(data):
    """Testing storing of data without specifying the field"""
    msg = test_gen_msgs.test_opt_uint64_as_nested(data)
    assert msg.data == data


def test_init_default():
    """Testing default value"""
    msg = test_gen_msgs.test_opt_uint64_as_nested()
    assert msg.data is None


# TODO : all possible (from ros_mappings) except proper integers
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.integers(max_value=0-1),
    hypothesis.strategies.integers(min_value=18446744073709551615+1),
    hypothesis.strategies.floats(),
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with pytest.raises(AttributeError) as cm:
        test_gen_msgs.test_opt_uint64_as_nested(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.value.message

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main([
        '-s',
        __file__
    ])
