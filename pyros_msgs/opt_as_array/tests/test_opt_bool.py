from __future__ import absolute_import, division, print_function

import os
import sys
import site

site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps'))

import rosimport
rosimport.activate()


from . import msg as test_gen_msgs

# patching (need to know the field name)
import pyros_msgs.opt_as_array
pyros_msgs.opt_as_array.duck_punch(test_gen_msgs.test_opt_bool_as_array, ['data'])

import pytest

import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.lists(hypothesis.strategies.booleans(), max_size=1))
def test_init_rosdata(data):
    """Testing that a proper data is stored as is"""
    msg = test_gen_msgs.test_opt_bool_as_array(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.booleans())
def test_init_data(data):
    """Testing that an implicitely convertible data is stored as expected"""
    msg = test_gen_msgs.test_opt_bool_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(hypothesis.strategies.booleans())
def test_init_raw(data):
    """Testing storing of data without specifying the field"""
    msg = test_gen_msgs.test_opt_bool_as_array(data)
    assert msg.data == [data]


def test_init_default():
    """Testing default value"""
    msg = test_gen_msgs.test_opt_bool_as_array()
    assert msg.data == []


# TODO : all possible (from ros_mappings) except booleans
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.integers(),
    hypothesis.strategies.floats(),
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with pytest.raises(AttributeError) as cm:
        test_gen_msgs.test_opt_bool_as_array(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of" in str(cm.value)


# Just in case we run this directly
if __name__ == '__main__':
    pytest.main([
        '-s',
        'test_opt_bool.py'
    ])
