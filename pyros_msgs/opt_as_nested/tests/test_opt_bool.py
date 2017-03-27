from __future__ import absolute_import, division, print_function

# TODO : property based testing. check hypothesis
# TODO : check all types

import sys

try:
    import genpy
    import pyros_msgs.opt_as_nested  # This will duck punch the standard message type initialization code.
    from pyros_msgs.msg import opt_bool, test_opt_bool_as_nested  # This will duck punch the generated message type.

except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    import pyros_msgs.opt_as_nested  # This will duck punch the standard message type initialization code.
    from pyros_msgs.msg import opt_bool, test_opt_bool_as_nested  # a message type just for testing

import nose

# patching  # TODO : move that into the type, we dont need to know the field name here...
pyros_msgs.opt_as_nested.duck_punch(test_opt_bool_as_nested, ['data'])




import hypothesis
import hypothesis.strategies as st


@hypothesis.given(st.one_of(st.none(), st.booleans()))
def test_init_none_data(data):
    """Testing that a opt field can get any bool or none"""
    msg = test_opt_bool_as_nested(data=data)
    assert msg.data == data


@hypothesis.given(st.one_of(st.none(), st.booleans()))
def test_init_raw(data):
    """Testing storing of data without specifying the field"""
    msg = test_opt_bool_as_nested(data)
    assert msg.data == data


def test_init_default():
    """Testing default value"""
    msg = test_opt_bool_as_nested()
    assert msg.data is None


# TODO : all possible (from ros_mappings) except booleans
@hypothesis.given(hypothesis.strategies.one_of(
    hypothesis.strategies.integers(),
    hypothesis.strategies.floats(),
))
def test_wrong_init_except(data):
    """Testing we except when types do not match"""
    with nose.tools.assert_raises(AttributeError) as cm:
        test_opt_bool_as_nested(data)
    assert isinstance(cm.exception, AttributeError)
    assert "does not match the accepted type schema for 'data' : Any of set" in cm.exception.message


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
