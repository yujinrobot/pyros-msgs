from __future__ import absolute_import, division, print_function

import pytest

from . import msg as test_gen_msgs
import std_msgs.msg as std_msgs

import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(test_gen_msgs.test_opt_std_empty_as_nested, ['data'])

import hypothesis
import hypothesis.strategies

@hypothesis.given(hypothesis.strategies.builds(std_msgs.Empty))
def test_init_rosdata(data):
    msg = test_gen_msgs.test_opt_std_empty_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.builds(std_msgs.Empty))
def test_init_data(data):
    msg = test_gen_msgs.test_opt_std_empty_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.builds(std_msgs.Empty))
def test_init_raw(data):
    msg = test_gen_msgs.test_opt_std_empty_as_nested(data)
    assert msg.data == data


def test_init_default():
    msg = test_gen_msgs.test_opt_std_empty_as_nested()
    assert msg.data == None


# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
