from __future__ import absolute_import, division, print_function

# TODO : check all types

import os
import sys


# TODO : find a better place for this ?
import pyros_msgs
from pyros_msgs.importer.rosmsg_generator import generate_msgsrv_nspkg, import_msgsrv

# a dynamically generated message type just for testing...
generated_modules = generate_msgsrv_nspkg(
    [os.path.join(os.path.dirname(__file__), 'msg', 'test_opt_int16_as_nested.msg')],
    # we need to specify any dependency to have a chance to get it.
    dependencies=['pyros_msgs'],
    include_path=['pyros_msgs:{0}'.format(os.path.join(os.path.dirname(pyros_msgs.__path__[0]), 'msg'))],
    ns_pkg=True
)
import_msgsrv('gen_msgs.msg._test_opt_int16_as_nested')

test_opt_int16_as_nested = getattr(sys.modules['gen_msgs.msg._test_opt_int16_as_nested'], 'test_opt_int16_as_nested')


import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(test_opt_int16_as_nested, ['data'])

import pytest
import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.integers(min_value=-32768, max_value=32767))
def test_init_rosdata(data):
    """Testing that a proper data is stored as is"""
    msg = test_opt_int16_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.integers(min_value=-32768, max_value=32767))
def test_init_data(data):
    """Testing that an implicitely convertible data is stored as expected"""
    msg = test_opt_int16_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.integers(min_value=-32768, max_value=32767))
def test_init_raw(data):
    """Testing storing of data without specifying the field"""
    msg = test_opt_int16_as_nested(data)
    assert msg.data == data


def test_init_default():
    """Testing default value"""
    msg = test_opt_int16_as_nested()
    assert msg.data is None


# TODO : all possible (from ros_mappings) except proper integers
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.integers(max_value=-32768-1),
    hypothesis.strategies.integers(min_value=32767+1),
    hypothesis.strategies.floats(),
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with pytest.raises(AttributeError) as cm:
        test_opt_int16_as_nested(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.value.message

# Just in case we run this directly
if __name__ == '__main__':
    pytest.main([
        '-s',
        __file__
    ])
