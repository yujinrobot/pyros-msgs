from __future__ import absolute_import, division, print_function

# TODO : property based testing. check hypothesis
# TODO : check all types

import sys

try:
    import genpy
    import pyros_msgs
    import pyros_msgs.opt_as_nested  # This will duck punch the generated message type.

except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    import pyros_msgs.opt_as_nested  # This will duck punch the standard message type initialization code.

import nose


def test_init_data_internal():
    msg = pyros_msgs.opt_as_nested.opt_bool(data=True)
    assert msg.initialized_ is True
    assert msg.data is True

    msg = pyros_msgs.opt_as_nested.opt_bool(data=False)
    assert msg.initialized_ is True
    assert msg.data is False


def test_init_raw_internal():
    msg = pyros_msgs.opt_as_nested.opt_bool(True)
    assert msg.initialized_ is True
    assert msg.data is True

    msg = pyros_msgs.opt_as_nested.opt_bool(False)
    assert msg.initialized_ is True
    assert msg.data is False


def test_init_default_internal():
    msg = pyros_msgs.opt_as_nested.opt_bool()
    assert msg.initialized_ is False
    assert msg.data is False  # default value


def test_init_excepts_internal_initialized():
    with nose.tools.assert_raises(AttributeError) as cm:
        pyros_msgs.opt_as_nested.opt_bool(initialized_=True)
    assert isinstance(cm.exception, AttributeError)
    assert cm.exception.message == "The field 'initialized_' is an internal field of pyros_msgs/opt_bool and should not be set by the user."


def test_init_excepts_internal_data():
    with nose.tools.assert_raises(AttributeError) as cm:
        pyros_msgs.opt_as_nested.opt_bool(data=42)
    assert isinstance(cm.exception, AttributeError)
    assert cm.exception.message == "42 does not match the accepted type schema for 'data' : <type 'bool'>"


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
