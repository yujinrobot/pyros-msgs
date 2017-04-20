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
    gen_test_msgs, gen_test_srvs = msg_generate.generate_test_msgs()
except Exception as e:
    pytest.raises(e)

import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(gen_test_msgs.test_opt_string_as_nested, ['data'])

import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_rosdata(data):
    msg = gen_test_msgs.test_opt_string_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_data(data):
    msg = gen_test_msgs.test_opt_string_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_raw(data):
    msg = gen_test_msgs.test_opt_string_as_nested(data)
    assert msg.data == data


def test_init_default():
    msg = gen_test_msgs.test_opt_string_as_nested()
    assert msg.data == None


# TODO : all possible (from ros_mappings) except text/binary
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.booleans(),
    hypothesis.strategies.integers(),
    hypothesis.strategies.floats(),
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(min_codepoint=128), min_size=1)
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    try:
        gen_test_msgs.test_opt_string_as_nested(data)
    except AttributeError:
        pass
    except UnicodeEncodeError:
        pass
    else:
        raise ("Typechecking error for strings")



# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])

