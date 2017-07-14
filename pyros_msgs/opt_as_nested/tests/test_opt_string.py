from __future__ import absolute_import, division, print_function

# TODO : check all types

import os
import sys
import pytest
import site

site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps'))

import rosimport
rosimport.activate()

from . import msg as test_gen_msgs


import pyros_msgs.opt_as_nested
# patching (need to know the field name)
pyros_msgs.opt_as_nested.duck_punch(test_gen_msgs.test_opt_string_as_nested, ['data'])

import hypothesis
import hypothesis.strategies


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_rosdata(data):
    msg = test_gen_msgs.test_opt_string_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_data(data):
    msg = test_gen_msgs.test_opt_string_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(hypothesis.strategies.one_of(
    # note : this will be unicode values
    hypothesis.strategies.text(alphabet=hypothesis.strategies.characters(max_codepoint=127)),
    # Note : binary strategy can create problem for hypothesis output. skipping for now.
    # hypothesis.strategies.binary()
))
def test_init_raw(data):
    msg = test_gen_msgs.test_opt_string_as_nested(data)
    assert msg.data == data


def test_init_default():
    msg = test_gen_msgs.test_opt_string_as_nested()
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
        test_gen_msgs.test_opt_string_as_nested(data)
    except AttributeError:
        pass
    except UnicodeEncodeError:
        pass
    else:
        raise ("Typechecking error for strings")



# Just in case we run this directly
if __name__ == '__main__':
    pytest.main(['-s', __file__])

