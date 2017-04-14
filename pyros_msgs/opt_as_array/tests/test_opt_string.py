from __future__ import absolute_import, division, print_function

import os
import sys



# generating all and accessing the required message class.
from pyros_msgs.opt_as_array.tests import msg_generate
gen_test_msgs, gen_test_srvs = msg_generate.generate_test_msgs()

import pyros_msgs.opt_as_array
# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(gen_test_msgs.test_opt_string_as_array, ['data'])

import pytest
import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.lists(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
), max_size=1))
def test_init_rosdata(data):
    msg = gen_test_msgs.test_opt_string_as_array(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_data(data):
    msg = gen_test_msgs.test_opt_string_as_array(data=data)
    assert msg.data == [data]


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_raw(data):
    msg = gen_test_msgs.test_opt_string_as_array(data)
    assert msg.data == [data]


def test_init_default():
    msg = gen_test_msgs.test_opt_string_as_array()
    assert msg.data == []


# TODO : all possible (from ros_mappings) except text/binary
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.booleans(),
    hypothesis.strategies.integers(),
    hypothesis.strategies.floats(),
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(min_codepoint=128), min_size=1)
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with pytest.raises(AttributeError) as cm:
        gen_test_msgs.test_opt_string_as_array(data)
    assert isinstance(cm.value, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.value.message


# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])
