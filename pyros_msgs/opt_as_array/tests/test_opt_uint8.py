from __future__ import absolute_import, division, print_function

import os
import sys


# TODO : find a better place for this ?
from pyros_msgs.importer.rosmsg_generator import generate_msgsrv_nspkg, import_msgsrv

# a dynamically generated message type just for testing...
generated_modules = generate_msgsrv_nspkg(
    [os.path.join(os.path.dirname(__file__), 'msg', 'test_opt_uint8_as_array.msg')],
    ns_pkg=True
)
for m in generated_modules:
    import_msgsrv(m)

test_opt_uint8_as_array = getattr(sys.modules['gen_msgs.msg._test_opt_uint8_as_array'], 'test_opt_uint8_as_array')

import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(test_opt_uint8_as_array, ['data'])

import pytest
import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.lists(hypothesis.strategies.integers(min_value=0, max_value=255), max_size=1))
def test_init_rosdata(data):
    """Testing that a proper data is stored as is"""
    msg = test_opt_uint8_as_array(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.integers(min_value=0, max_value=255))
def test_init_data(data):
    """Testing that an implicitely convertible data is stored as expected"""
    msg = test_opt_uint8_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(hypothesis.strategies.integers(min_value=0, max_value=255))
def test_init_raw(data):
    """Testing storing of data without specifying the field"""
    msg = test_opt_uint8_as_array(data)
    assert msg.data == [data]


def test_init_default():
    """Testing default value"""
    msg = test_opt_uint8_as_array()
    assert msg.data == []


# TODO : all possible (from ros_mappings) except proper integers
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.integers(max_value=-1),
    hypothesis.strategies.integers(min_value=255+1),
    hypothesis.strategies.floats(),
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with pytest.raises(AttributeError) as cm:
        test_opt_uint8_as_array(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.value.message

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main([
        '-s',
        __file__
    ])
