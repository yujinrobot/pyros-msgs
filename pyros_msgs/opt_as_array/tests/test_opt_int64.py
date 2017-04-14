from __future__ import absolute_import, division, print_function

import os
import sys


# generating all and accessing the required message classe.
from pyros_msgs.opt_as_array.tests import msg_generate
gen_test_msgs, gen_test_srvs = msg_generate.generate_test_msgs()

import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(gen_test_msgs.test_opt_int64_as_array, ['data'])

import pytest
import hypothesis
import hypothesis.strategies

from pyros_msgs.typecheck import six_long


@hypothesis.given(hypothesis.strategies.lists(hypothesis.strategies.integers(min_value=six_long(-9223372036854775808), max_value=six_long(9223372036854775807)), max_size=1))
def test_init_rosdata(data):
    msg = gen_test_msgs.test_opt_int64_as_array(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.integers(min_value=six_long(-9223372036854775808), max_value=six_long(9223372036854775807)))
def test_init_data(data):
    msg = gen_test_msgs.test_opt_int64_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(hypothesis.strategies.integers(min_value=six_long(-9223372036854775808), max_value=six_long(9223372036854775807)))
def test_init_raw(data):
    msg = gen_test_msgs.test_opt_int64_as_array(data)
    assert msg.data == [data]


def test_init_default():
    msg = gen_test_msgs.test_opt_int64_as_array()
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
        gen_test_msgs.test_opt_int64_as_array(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.value.message

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
