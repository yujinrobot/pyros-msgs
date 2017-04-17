from __future__ import absolute_import, division, print_function

import os
import sys


import pytest


# generating all and accessing the required message class.
from pyros_msgs.opt_as_array.tests import msg_generate

try:
    # This should succeed if the message class was already generated
    import std_msgs.msg as std_msgs
except ImportError:  # we should enter here if the message was not generated yet.
    std_msgs, _ = msg_generate.generate_std_msgs()

test_gen_msgs, gen_test_srvs = msg_generate.generate_test_msgs()


import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(test_gen_msgs.test_opt_std_empty_as_array, ['data'])

import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.lists(hypothesis.strategies.builds(std_msgs.Empty), max_size=1))
def test_init_rosdata(data):
    msg = test_gen_msgs.test_opt_std_empty_as_array(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.builds(std_msgs.Empty))
def test_init_data(data):
    msg = test_gen_msgs.test_opt_std_empty_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(hypothesis.strategies.builds(std_msgs.Empty))
def test_init_raw(data):
    msg = test_gen_msgs.test_opt_std_empty_as_array(data)
    assert msg.data == [data]


def test_init_default():
    msg = test_gen_msgs.test_opt_std_empty_as_array()
    assert msg.data == []


# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
